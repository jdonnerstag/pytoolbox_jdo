#!/usr/bin/env python
# encoding: utf-8

"""Utilities for deep dict like structures"""

from typing import Any, Mapping, MutableMapping


def path_split(path: str|list[str], *, separator:str=".") -> list[str]:
    """Split the path by the configured separator, and remove empty elements"""

    if isinstance(path, str):
        path = path.split(separator)

    return [x for x in path if x]


__MISSING__ = object()

def deep_get(
    _dict: Mapping[str, Any], _keys: str | list[str], *, default=__MISSING__, separator: str = "."
) -> Any:
    """Walk the keys to determine the value.

    Keys might be a list, or a string which will be splitted by the separator.

    if the key was not found, and default has been provided, then return the
    default value. Else raise an exception.

    E.g. deep_get(my_config, "this.is.what.I.want", None) or
    deep_get(my_config, ["this", "is", "what", "I", "want"], None) which is the same
    """
    _keys = path_split(_keys, separator=separator)
    if not _keys:
        if default != __MISSING__:
            return default

        raise KeyError("deep_get(): 'key' must not be empty")

    try:
        for _elem in _keys:
            _dict = _dict[_elem]

        return _dict
    except (KeyError, TypeError):
        if default != __MISSING__:
            return default

        raise

def deep_set(
    _dict: MutableMapping[str, Any],
    _keys: str | list[str],
    value: Any,
    *,
    create: bool = False,
    replace: bool = True,
    separator: str = "."
):
    """Set the value for the (deep) key

    If 'create' is True, then missing elems in the path are
    automatically created.

    If 'replace' is True, then any existing value will be replaced
    with the new one.
    """

    _keys = path_split(_keys, separator=separator)

    last = _keys.pop()
    for key in _keys:
        if not create:
            _dict = _dict[key]
        elif key in _dict:
            _dict = _dict[key]
        else:
            new_value = {}
            _dict[key] = new_value
            _dict = new_value

    if last not in _dict:
        _dict[last] = value
    elif replace:
        _dict[last] = value
    else:
        raise KeyError(
            f"Entry already exists: {_keys}. "
            "Use 'replace=True' to replace")


def deep_delete(
    _dict: MutableMapping,
    _keys: str | list[str],
    separator: str = ".",
    exception: bool = True,
):
    """Delete the entry related to key.

    No matter what the value is, the entry will be removed.
    """

    _keys = path_split(_keys, separator=separator)
    last = _keys.pop()
    obj = _dict
    if _keys:
        try:
            obj = deep_get(_dict, _keys, separator=separator)
        except KeyError:
            if not exception:
                return None

            raise

    rtn = obj[last]
    del obj[last]
    return rtn


def deep_iter(_dict: Mapping, parent:None|list=None):
    """Recursively iterate through all key/value pairs"""

    parent = parent or []

    for key, value in _dict.items():
        yield key, value, parent

        if isinstance(value, Mapping):
            parent.append(key)
            yield from deep_iter(value, parent)
            parent.pop()


def deep_str(_dict: Mapping) -> str:
    """Create a string representation"""

    rtn = ""
    for key, value, parents in deep_iter(_dict):
        if rtn:
            rtn += "; "

        parents = parents + [key]
        rtn += f"{'.'.join(parents)}"
        if not isinstance(value, dict):
            rtn += "=" + str(value)

    return rtn
