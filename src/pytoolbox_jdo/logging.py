#!/usr/bin/env python
# encoding: utf-8

"""Logging utilities (leveraging the standard python logging module) """

import sys
import os
import logging
import logging.config
from pathlib import Path

from .pyconfig import Config

# Nice articles
# https://www.loggly.com/ultimate-guide/python-logging-basics/


def configure(config: Config, path: str):
    """Configure logging with log configs taken from Config"""

    log_cfg = config.to_dict(path, substitute=True)
    logging.config.dictConfig(log_cfg)

    logger.info(
        "Starting with: %s %s", os.path.basename(sys.argv[0]), " ".join(sys.argv[1:])
    )

    for i in range(1, len(config.config) - 1):
        cfg = config.user_config[i - 1]
        file = config.config[i].get("__file__", "<unknown>")
        logger.info("Config: %s - %s", cfg, file)


def get_logger(name: str, level: int|str=logging.INFO):
    """Select the logger by its name"""

    mylogger = logging.getLogger(name)
    mylogger.setLevel(level)

    return mylogger


# Note: Must go last, after get_logger() has been defined !!
logger = get_logger(__name__, logging.DEBUG)


CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = logging.WARN
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET


class LogException(Exception):
    """LogException"""


class LogRedirector:
    """Log redirector

    Several of our cmdlines allow user to provide multiple input files.
    And because we want a dedicated log-file per input file, we are adding
    and removing log.handlers as required.
    """

    def __init__(self, file: Path, log_file: Path):
        # The input file being processed
        self.input_file = file

        # Configure a new FileHandler
        self._root_logger = root_logger = logging.getLogger("")
        self._file_handler = _fh = logging.FileHandler(log_file, mode="a", encoding="utf8")
        _fh.setLevel(logging.DEBUG)
        _fh.set_name("import_log")
        _fh.setFormatter(root_logger.handlers[0].formatter)

        # Register the new handler so that it gets used
        root_logger.addHandler(_fh)

        # This is the first message in the new handler. But it's also added
        # to all other handlers (if any).
        logger.info("Start processing file: %s", file)

        # Get references to the console and application handlers
        self._console_handler = self.handler_by_name("console")
        self._app_handler = self.handler_by_name("xxx_engine")

    def handler_by_name(self, name: str):
        """Find log handler by name"""
        for handler in self._root_logger.handlers:
            if handler.name == name:
                return handler

        raise LogException(f"Log handler not found: name='{name}'")

    def on_success(self):
        """Add the app handler again, which was removed previously"""
        self._root_logger.addHandler(self._app_handler)

        logger.info("Successfully finished processing: %s", self.input_file)

        # Remove the input file specific handler again
        self._root_logger.removeHandler(self._file_handler)

    def on_failure(self, exc):
        """Add the pil_engine handler again, which was removed previously"""
        self._root_logger.addHandler(self._app_handler)

        # Remove the console handler but only for the following statment
        self._root_logger.removeHandler(self._console_handler)
        logger.exception("Failed with exception: %s", exc)
        self._root_logger.addHandler(self._console_handler)

        # Remove the input file specific handler again
        self._root_logger.removeHandler(self._file_handler)

    def add_app_handler(self):
        """Add the (application) log handler"""
        self._root_logger.addHandler(self._app_handler)

    def remove_app_handler(self):
        """Remove the (application) log handler"""
        self._root_logger.removeHandler(self._app_handler)
