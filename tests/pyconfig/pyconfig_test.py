#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-function-docstring, missing-module-docstring

from pathlib import Path

import pytest

from pytoolbox_jdo.pyconfig import Config, ConfigException
import pytoolbox_jdo.import_module


data_dir = Path(__file__).parent / "data"

def setup_module(_module):
    # This is a global variable and some test might have set it already
    pytoolbox_jdo.import_module.modules.clear()

def test_constructor():
    # Create an empty Config. No loading of any config
    cfg = Config(user_config=None, default_config=None)
    assert len(cfg) == 0

    cfg = Config(search_path=data_dir, user_config=None)
    assert cfg
    # __file__ gets automatically added
    assert cfg.get("__file__").name == "config.py"

    with pytest.raises(Exception):
        assert cfg.get("not-exist")

    # This comes from the default config
    assert cfg.get("version") == 1

    # This one is only available in config-linux
    cfg = Config(search_path=data_dir, user_config="linux")
    assert cfg.get("linux_only") == "linux"
    assert cfg.config[1]["__file__"].name == "config-linux.py"
    assert cfg.config[2]["__file__"].name == "config.py"

    with pytest.raises(ConfigException):
        Config(search_path=data_dir, user_config="error")

    with pytest.raises(ConfigException):
        Config(search_path=data_dir, user_config="invalid-filename")

    with pytest.raises(ConfigException):
        Config(search_path=Path("./tests/invalid_dir"), user_config=None)

    # This one is only available in config-linux
    cfg = Config(search_path=data_dir, user_config="dev,linux")
    assert cfg.get("linux_only") == "linux"
    assert cfg.get("development_mode") is True
    assert cfg.config[1]["__file__"].name == "config-linux.py"
    assert cfg.config[2]["__file__"].name == "config-dev.py"
    assert cfg.config[3]["__file__"].name == "config.py"

    # This one is only available in config-linux
    cfg = Config(search_path=data_dir, user_config="dev, linux")
    assert cfg.get("linux_only") == "linux"
    assert cfg.get("development_mode") is True

    # This one is only available in config-linux
    path = [Path("."), data_dir / "users", data_dir]
    cfg = Config(search_path=path, user_config=["me", "linux"])
    assert cfg.config[1]["__file__"].as_posix().endswith("/data/config-linux.py")
    assert cfg.config[2]["__file__"].as_posix().endswith("/users/config-me.py")
    assert cfg.config[3]["__file__"].as_posix().endswith("/data/config.py")

    # Python module config-dev.py has previously been loaded from ./test/data.
    # The search path below will find the file in ./test/data/users and try to
    # import it. Python, by default, continues without an exception. We
    # want to know and throw an exception
    with pytest.raises(Exception):
        path = [Path("."), data_dir / "users", data_dir]
        cfg = Config(search_path=path, user_config="dev")

def test_to_dict():
    cfg = Config(search_path=data_dir, user_config="linux")
    data = cfg.to_dict()
    assert data["linux_only"] == "linux"
    assert data["version"] == 1
    assert data["db"]["batch_size"] == 1000
    assert data["logging"]["root"]["level"] == "DEBUG"

    data = cfg.to_dict("logging")
    assert data["root"]["level"] == "DEBUG"

    # Test we can also substitute placeholders when exporting into a dict.
    with pytest.raises(Exception):
        data = cfg.to_dict("invalid", substitute=True)

    cfg.set("does-not-exist", 10)
    data = cfg.to_dict("invalid", substitute=True)
    assert data["missing"] == "10"

    # Provide the required additional values
    cfg.set("data_files_input_dir", "./tests")
    data = cfg.to_dict("more-files", substitute=True)
    assert data["list_values"] == [
        "./tests/111.dat",
        "./tests/222.dat"
    ]
    assert data["XYZ"]["customer_account"] == {
        "full": "./tests/DWH_CUSTOMER_ACCOUNT_FULL.*",
        "delta": "./tests/DWH_CUSTOMER_ACCOUNT_DELTA.*",
    }


def test_get_value():
    cfg = Config(search_path=data_dir, user_config="linux")
    assert cfg.get("linux_only") == "linux"
    assert cfg.get("version") == 1
    assert cfg.get(["db", "batch_size"]) == 1000
    assert cfg.get("db.batch_size") == 1000
    assert cfg.get("logging.root.level") == "DEBUG"
    assert isinstance(cfg.get("db"), dict)
    assert "connection_string" in cfg.get("db")

    with pytest.raises(Exception):
        cfg.get("does not exist")

    with pytest.raises(Exception):
        cfg.get("logging.also_missing")

    with pytest.raises(Exception):
        cfg.get("missing.root")

    assert cfg.get_value("db.connection_string") == "dbadmin/my-silly-pass@mydatabase.mycompany.com"

def test_placeholder():
    cfg = Config(search_path=data_dir, user_config="dev")
    assert cfg.get("project_root") == "C:\\source_code\\my_project"
    assert cfg.get_value("git.manual_files_git_repo") == "{project_root}\\files"
    assert cfg.get("git.manual_files_git_repo") == "C:\\source_code\\my_project\\files"
    assert cfg.get("test.my_dir") == "C:\\source_code\\my_project"

    assert "-" in cfg.get("timestamp")

    cfg.set("filename", "test")
    assert cfg.get("files.log_file").startswith("C:\\source_code\\my_project\\files/test.")

    assert cfg.get("more-files.list_values") == ['/mydir/111.dat', '/mydir/222.dat']

    assert cfg.get("more-files.XYZ.customer_account") == {
        "delta": "/mydir/DWH_CUSTOMER_ACCOUNT_DELTA.*",
        "full": "/mydir/DWH_CUSTOMER_ACCOUNT_FULL.*"
    }

    # TODO There are couple pylint false-positive :(
    # The escape backslash will not be remove. We don't to magically change the string.
    xxx = cfg["escape"]
    aaa = xxx["no_replace"]     # pylint: disable=unsubscriptable-object
    assert aaa == r"\{project_root\}"
    assert xxx["no_replace"] == r"\{project_root\}" # pylint: disable=unsubscriptable-object
    assert cfg["escape"]["no_replace"] == r"\{project_root\}"   # pylint: disable=unsubscriptable-object

    # These are obvious that they should be working (replace the placeholder)
    assert cfg["git.manual_files_git_repo"] == "C:\\source_code\\my_project\\files"
    assert cfg.get(["git", "manual_files_git_repo"]) == "C:\\source_code\\my_project\\files"
    assert cfg.get("git.manual_files_git_repo") == "C:\\source_code\\my_project\\files"

    # These one are working as well!! And that is because get("git") returns a map,
    # which calls substitute_placeholder() and that works recursively.
    assert cfg["git"]["manual_files_git_repo"] == "C:\\source_code\\my_project\\files"  # pylint: disable=unsubscriptable-object
    assert cfg.get("git")["manual_files_git_repo"] == "C:\\source_code\\my_project\\files"

    # This is a more extrem example of the same: get() recursively substitues the placeholders
    # This is also a good example for params to replace or amend config values
    cfg.set("timestamp", 123)
    assert cfg.config[0]["timestamp"] == 123
    assert cfg.get("logging")["handlers"]["my_app"]["filename"] == "/temp/logs/my_app.123.log"

def test_set():
    cfg = Config(search_path=data_dir, user_config="dev")

    cfg.set("logging.handlers.my_app.filename", "this is a deep test")
    assert cfg.get("logging.handlers.my_app.filename") == "this is a deep test"
    assert cfg.config[0]["logging"]["handlers"]["my_app"]["filename"] == "this is a deep test"

# Test implement where() which hints at the __file__ used
