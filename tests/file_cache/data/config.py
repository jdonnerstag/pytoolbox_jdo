#!/usr/bin/env python
# encoding: utf-8

# pylint: disable=missing-function-docstring, invalid-name, line-too-long

import os
from datetime import datetime

# (Dynamic) Functions can be used to determine config values
def DB_USER():
    return os.getenv("DB_USER", "dbadmin")


def DB_PASS():
    return os.getenv("DB_PASS", "my-silly-pass")


# 1) You can pass parameter to the function
# 2) Return any value. Placeholders will be replaced if present
def FUNC(fname):
    return {
        "full": "{data_files_input_dir}/" + f"DWH_{fname}_FULL.*",
        "delta": "{data_files_input_dir}/" + f"DWH_{fname}_DELTA.*",
    }


# Constants can be defined
DB_NAME = os.getenv("DB_NAME", "mydatabase.mycompany.com")


def DB_CONNECTION_STRING():
    return f"{DB_USER()}/{DB_PASS()}@{DB_NAME}"


PROJECT_ROOT = "C:\\source_code\\my_project"

# Don't change the name "CONFIG". We expect the configs to be in their
CONFIG = {
    "version": 1,
    # Number of processes
    # Use a negative number to dynamically determine the pool size based on server
    # CPU, core and threads sizes. E.g. -1 => leave 1 core to the OS
    "process_pool": -1,
    "db": {
        # Lazy load the connection string. The actual value will never be stored in config
        "connection_string": DB_CONNECTION_STRING(),
        "batch_size": 1_000,
    },
    # Define once and re-use further down
    "log_dir": "/temp/logs",
    # This way we make it available in derived environment configs (e.g. config-dev.py)
    "project_root": PROJECT_ROOT,
    # Timestamp when the app was started
    "timestamp": lambda: datetime.now().strftime("%Y%m%d-%H%M%S"),
    "git": {
        # Given the definition from above, both are the same
        # "manual_files_git_repo": "{PROJECT_ROOT}\\files",
        "manual_files_git_repo": "{project_root}\\files",
    },
    "files": {
        # Placeholders always resolve against the root, and can be deep
        "log_file": "{git.manual_files_git_repo}/{filename}.{timestamp}.log",
    },
    "data_files_input_dir": "/mydir",
    "more-files": {
        # List are supported as well, and also resolve the placeholders
        "list_values": [
            "{data_files_input_dir}/111.dat",
            "{data_files_input_dir}/222.dat",
        ],
        "XYZ": {
            # FUNC returns a list
            "customer_account": FUNC("CUSTOMER_ACCOUNT"),
        },
    },
    "invalid": {
        "missing": "{does-not-exist}"
    },
    "escape": {
        # Escape it. Do not replace the placeholder.
        "no_replace": "\\{project_root\\}"
    },
    # We have a little log extension, that pull the config from here.
    # And like above, placeholders are resolved.
    "logging": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "my_app": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "filename": "{log_dir}/my_app.{timestamp}.log",
                "encoding": "utf8",
            },
            # "log_handler (example)": {
            #    "class": "logging.handlers.RotatingFileHandler",
            #    "level": "INFO",
            #    "formatter": "simple",
            #    "filename": "{log_dir}/info.log",
            #    "maxBytes": 10485760,
            #    "backupCount": 20,
            #    "encoding": "utf8"
            # },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "my_app"],
        },
    },
}
