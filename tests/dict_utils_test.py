#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-function-docstring, missing-module-docstring, invalid-name

from collections import OrderedDict
import pytest

import pytoolbox_jdo.dict_utils as du


def test_path_split():
    assert du.path_split("") == []
    assert du.path_split("a.b.c.d") == ["a", "b", "c", "d"]
    assert du.path_split("a..b.c") == ["a", "b", "c"]
    assert du.path_split("/a/b/c", separator="/") == ["a", "b", "c"]
    assert du.path_split("/a/b/c/", separator="/") == ["a", "b", "c"]


def test_deep_get():
    d = dict(a=1, b=2, c="cc", d=dict(key="kkkk"))

    assert du.deep_get(d, "") == d
    assert du.deep_get(d, []) == d
    assert du.deep_get(d, ".") == d

    assert du.deep_get(d, "a") == 1
    assert du.deep_get(d, ["a"]) == 1
    assert du.deep_get(d, "d.key") == "kkkk"
    assert du.deep_get(d, ["d", "key"]) == "kkkk"

    assert du.deep_get(d, "d/key", separator="/") == "kkkk"

    assert du.deep_get(d, "aaaa", default=None) is None
    assert du.deep_get(d, "d.aaaa", default=None) is None
    assert du.deep_get(d, "d.key.aaaa", default=None) is None


def test_deep_set():
    d = dict(a=1, b=2, c="cc", d=dict(key="kkkk"))

    assert du.deep_get(d, "aa", default=None) is None
    du.deep_set(d, "aa", 11)
    assert du.deep_get(d, "aa") == 11

    # "a" already exists
    with pytest.raises(Exception):
        du.deep_set(d, "a.a", 11)

    # "b1" does not yet exist
    with pytest.raises(Exception):
        du.deep_set(d, "b1.b2", 33)

    du.deep_set(d, "b1.b2", 33, create=True)
    assert du.deep_get(d, "b1") == {"b2": 33}
    assert du.deep_get(d, "b1.b2") == 33

    du.deep_set(d, "b1.b3.b4.b5.b6", 44, create=True)
    assert du.deep_get(d, "b1.b3.b4.b5.b6") == 44

    du.deep_set(d, "b1.b3", 55, replace=True)
    assert du.deep_get(d, "b1.b3") == 55


def test_deep_del():
    d = dict(a=1, b=2, c="cc", d=dict(key="kkkk"))
    assert du.deep_get(d, "a") == 1
    assert du.deep_delete(d, "a") == 1
    assert du.deep_get(d, "a", default=None) is None

    assert du.deep_get(d, "d.key") == "kkkk"
    assert du.deep_delete(d, "d") == {"key": "kkkk"}
    assert du.deep_get(d, "d", default=None) is None


def test_deep_iter():
    d = OrderedDict(a=1, b=2, c="cc", d=OrderedDict(key="kkkk"))
    assert du.deep_str(d) == "a=1; b=2; c=cc; d; d.key=kkkk"
