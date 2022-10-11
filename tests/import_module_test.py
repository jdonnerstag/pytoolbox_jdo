#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-function-docstring, missing-module-docstring

from pathlib import Path

import pytest

from pytoolbox_jdo.import_module import modules, import_module_from_file


def test_constructor():
    modules.clear()

    import_module_from_file(Path("./tests/data/config-dev.py"))
    import_module_from_file(Path("./tests/data/config-dev.py"))

    # A module with same name but different directory has been loaded already
    with pytest.raises(Exception):
        import_module_from_file(Path("./tests/data/users/config-dev.py"))
