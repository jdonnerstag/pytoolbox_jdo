#!/usr/bin/env python
# encoding: utf-8

"""
"""

from os import PathLike
from typing import Any
from cloudpathlib import CloudPath, AnyPath
from ..file_repo import FileMatcher


class CloudFileMatcher(FileMatcher):
    """Files stored somewhere in S3 or other providers

    TODO This implementation is without caching. You need to configure
    the CloudPath default clients to enable caching.
    """
    def match(self, _fname: str | PathLike, **kvargs) -> bool:
        """True, if the matcher is able to handle this file"""
        return isinstance(AnyPath(_fname), CloudPath)

    def open_uncached(self, fname: str|PathLike, *args, **kvargs) -> Any:
        return self.open(fname, *args, **kvargs)

    def open(self, fname: str|PathLike, *args, **kvargs) -> Any:
        """Open the (cached) file"""
        file = CloudPath(str(fname))
        return file.open(*args, **kvargs)
