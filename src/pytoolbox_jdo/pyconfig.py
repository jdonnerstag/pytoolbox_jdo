#!/usr/bin/env python
# encoding: utf-8

"""Read the default and environment specific configurations"""

import os
import re
import json
from pathlib import Path
from typing import Mapping, Match, MutableMapping, TypeVar, Any, cast

from .import_module import import_module_from_file
from . import dict_utils as du


T = TypeVar("T")

def force_list(item_or_list: T|list[T]) -> list[T]:
    """If item is a single item of type T, then create a list[T] from it"""
    return item_or_list if isinstance(item_or_list, list) else [item_or_list]


__MISSING__ = object()

# Pil config specific exception
class ConfigException(Exception):
    """ConfigException"""


class Config:
    """Application Configurations

    The config conists of at least 3 layers, but can be more
    layer 1 - any changes or additions made by the user manually
    layer 2 - (N-1) - 1+ user provided configs from whatever source
    layer N - System defaults imported from ./config.py
    Originally we used ChainMap, but ChainMap doesn't work 'deep'
    """

    def __init__(
        self,
        user_config: None | str | list[str],
        *,
        search_path: Path|list[Path] = Path("."),
        default_config: None|str = "config",
        separator: str = "."
    ):
        self.default_config = default_config
        self.user_config = self._init_user_config(user_config)
        self.search_path = force_list(search_path)
        self.separator = separator

        self.config = [{}]

        # Validate that all search path elements exist
        for _dir in self.search_path:
            if not _dir.is_dir():
                raise ConfigException(
                    f"Directory not found: '{_dir}' ({_dir.resolve()})"
                )

        # Import the default config
        if self.default_config:
            file = self.find_file(self.default_config)
            self.load_config(file)

        # Import the user config(s)
        for config in self.user_config:
            self.load_user_config(config)

    def _init_user_config(self, user_config: None|str|list[str]) -> list[str]:
        """Create a list of user config names, from whatever the user provided"""

        if user_config is None:
            return []

        if isinstance(user_config, str):
            if user_config.startswith("env:"):
                user_config = user_config[4:]
                try:
                    user_config = os.environ[user_config]
                except:     # pylint: disable=raise-missing-from
                    raise ConfigException(f"Environment variable not found: '{user_config}'")

            user_config = [x.strip() for x in user_config.split(",")]

        return user_config

    def find_file(self, fname: str) -> Path:
        """Find the file by searching along the configured search path"""

        fname += ".py"
        for _dir in self.search_path:
            file = Path(f"{_dir}/{fname}")
            if file.is_file():
                return file

        raise ConfigException(
            f"File not found in search path: file='{fname}', path={self.search_path}")

    def load_config(self, file: Path):
        """Load a config from the file specified"""

        if not file.is_file():
            raise ConfigException(f"Config file not found: '{file}'")

        try:
            module = import_module_from_file(file)
        except Exception as exc:
            raise ConfigException(f"Failed to import config file: {file}") from exc

        if not hasattr(module, "CONFIG"):
            raise ConfigException(
                f"Not a valid config file. Is missing the CONFIG variable: '{file}'"
            )

        if not isinstance(module.CONFIG, dict):
            raise ConfigException(
                f"CONFIG must be a Mapping: '{file}', CONFIG={module.CONFIG}"
            )

        module.CONFIG["__file__"] = file.resolve()
        config = module.CONFIG
        self.config.insert(1, config)
        return config

    def load_user_config(self, config_name: str):
        """Add a config which name is like 'config-<name>.py'"""

        file = f"{self.default_config}-{config_name}"
        file = self.find_file(file)
        return self.load_config(file)

    def _deep_dict_update(self,
        dest: MutableMapping[str, Any],
        source: Mapping[str, Any],
        substitute: bool=False,
    ) -> MutableMapping[str, Any]:
        """Deep update dict 'd' with all elements from dict 'u' (recursively)"""

        for key, value, parents in du.deep_iter(source):
            if substitute:
                value = self.substitute_placeholders(value)

            parents = parents + [key]
            du.deep_set(dest, parents, value)

        return dest


    def _path_split(self, path: str|list[str]) -> list[str]:
        """Split the path by the configured separator, and remove empty elements"""

        if isinstance(path, str):
            path = path.split(self.separator)

        return [x for x in path if x]

    def to_dict(self,
        root: None|str|list[str] = None,
        substitute: bool=False
    ):
        """Create a dict of all the visible data. With 'root' provided,
        only the config below this path are copied into a dir.
        """
        if root is not None:
            root = self._path_split(root)

        rtn: dict[str, Any] = {}
        for level in reversed(self.config):
            if root:
                try:
                    level = du.deep_get(level, root)
                except KeyError:
                    continue

            if not isinstance(level, Mapping):
                raise ConfigException(f"Expected a Mapping but got: {level}")

            if level:
                self._deep_dict_update(rtn, level, substitute)

        return rtn

    def get_value(self, path: str|list[str]):
        """Get the config value corresponding to the 'path' provided.

        The path separator can be provided. Default separator is '.'.
        If the 'path' does not exist, return the 'default' value, which is
        None by default.

        get_value() return the raw-value. Consider using get() instead.
        """
        path = self._path_split(path)

        for level in self.config:
            try:
                return du.deep_get(level, path)
            except KeyError:
                pass

        raise KeyError(f"Key not found: '{path}'")

    def __contains__(self, path: str|list[str]) -> bool:
        """Check if value referred to by 'path' exists in the config.
        The path separator can be provided. Default separator is '.'.
        If the 'path' does exist, return True else False.
        """
        try:
            self.get_value(path)
            return True
        except:  # pylint: disable=bare-except
            return False

    def __getitem__(self, path: str):
        return self.get(path)

    def __len__(self) -> int:
        return len(self.to_dict())

    def substitute_placeholders_in_str(self, value: str) -> str:
        """Substitute placeholders {..} in 'v'. 'v' can be of type str or list. Placeholders
        will be replaced either with values from 'params' or other config entries.
        """

        def do_replace(name: str) -> str:
            value = self.get_value(name.split("."))

            if callable(value):
                value = value()

            return str(value)

        def replacer(re_match: Match[str]) -> str:
            match = re_match.group()
            name = match[1:-1].strip()

            try:
                return do_replace(name)
            except:  # pylint: disable=bare-except
                # Some are lazy resolved. So it is perfectly ok to not resolve all.
                return match

        count = 1
        while count > 0:
            last_value = value
            # "{..}", but ignore \{ and \}
            value, count = re.subn(r"(?<!\\)[{].*?(?<!\\)[}]", replacer, value)
            if count > 0 and last_value == value:
                raise ConfigException(f"Unable to replace all placeholders: '{value}'")

        return value

    def substitute_placeholders(self, value: T) -> T:
        """Return a new dict with all placeholders replaced"""
        if isinstance(value, Mapping):
            return cast(T, {
                key: self.substitute_placeholders(value) for key, value in value.items()
            })
        if isinstance(value, list):
            return cast(T, [self.substitute_placeholders_in_str(x) for x in value])
        if isinstance(value, str):
            return cast(T, self.substitute_placeholders_in_str(value))
        if callable(value):
            value = value()
            return self.substitute_placeholders(value)

        return value

    def get(self, path: str | list[str], default: Any=__MISSING__):
        """Get the config value referred to by 'path'.

        You may change the separator by providing a 'separator' parameter. Default is '.'.

        Config values support placeholders {..} which will be replaced either with
        data provided in 'params' or other config entries. 'params' must be a dict.
        'default' is another supported argument, which will be returned, if the 'path'
        does not resolve to a valid config entry.

        If a path cannot be resolved, an exception is thrown if no 'default' parameter
        has been provided.
        """
        path = self._path_split(path)

        try:
            rtn = self.get_value(path)
        except KeyError as exc:
            if default is not __MISSING__:
                return default

            raise ConfigException(f"Config element not found: '{path}'") from exc

        try:
            rtn = self.substitute_placeholders(rtn)
        except Exception as exc:
            raise ConfigException(f"Error while replacing placeholder: '{path}'") from exc

        return rtn

    def get_file(self, name: str, file: str):
        """Often a config value represents a file name. Sometimes the target
        filename can be constructed with a filename. In file rename
        scenarios that is often the case.

        E.g. { xyz_file: "{backup_dir}/{filedir}/{filename}.{now}" }
        """
        data = dict(filename=os.path.basename(file), filedir=os.path.dirname(file))
        self.config.insert(0, data)
        try:
            return self.get(name)
        finally:
            del self.config[0]

    def set(self, path: str | list[str], value) -> None:
        """Set a config value at 'path'"""

        obj = self.config[0]

        path = self._path_split(path)
        if len(path) == 0:
            raise ConfigException("Argument 'path' must not be empty")

        leaf = path.pop()
        for elem in path:
            obj = obj.setdefault(elem, {})

        if not isinstance(obj, MutableMapping):
            raise ConfigException(f"Invalid config path. Parent must be a mapping: '{path}'")

        obj[leaf] = value


    def __str__(self) -> str:
        return json.dumps(self.config, indent=4, sort_keys=False, default=str)

    def __repr__(self) -> str:
        return (
            self.__class__.__name__
            + "("
            + self.__str__()
            + f", name={self.user_config}, dir={self.search_path})"
        )
