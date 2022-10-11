#!/usr/bin/env python
# encoding: utf-8

"""Import python modules with a file name"""

import sys
import os
import importlib
from pathlib import Path

# Track the module and file name of module already imported
modules: dict[str, Path] = {}

def import_module_from_file(file: Path):
    """Import a python module from a file location.

    Prevent that modules with the same name but from different files
    are loaded. Python silently continues with the cached version.
    In our use case (e.g. config files), it is an error.
    """

    assert file.is_file(), f"File not found: '{file}'"

    name = os.path.splitext(os.path.basename(file))[0]

    # If a module has already been loaded, Python will silently continue
    # with the module already loaded. To prevent this "issue", we track
    # which files we've loaded and raise an error.
    if modules.get(name, file) != file:
        raise AttributeError(
            f"A module with the same name has already been imported: "
            f"'{name}', file-1={modules.get(name)}, file-2={file}")

    # VS Code automatically adds the cwd, but pytest doesn't.
    # Make sure we always add the cwd.
    dirname = os.path.dirname(file) or "."
    if dirname:
        sys.path.insert(0, dirname)

    try:
        mod = importlib.import_module(name)
        modules[name] = file
        return mod
    except Exception as exc:
        raise Exception(f"Failed to load module from: {file}") from exc
    finally:
        if dirname:
            del sys.path[0]
