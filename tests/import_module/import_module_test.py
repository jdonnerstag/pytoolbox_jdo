#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-function-docstring, missing-module-docstring

from pathlib import Path

import pytest

from pytoolbox_jdo.import_module import modules, import_module_from_file
import pytoolbox_jdo.import_module

data_dir = Path(__file__).parent / "data"


def setup_module(_module):
    # This is a global variable and some test might have set it already
    pytoolbox_jdo.import_module.modules.clear()

def test_constructor():
    modules.clear()

    import_module_from_file(data_dir / "config-dev.py")
    import_module_from_file(data_dir / "config-dev.py")

    # A module with same name but different directory has been loaded already
    with pytest.raises(Exception):
        import_module_from_file(data_dir / "users/config-dev.py")
