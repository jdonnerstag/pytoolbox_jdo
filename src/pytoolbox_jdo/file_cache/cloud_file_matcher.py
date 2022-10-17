#!/usr/bin/env python
# encoding: utf-8

"""CloudFileMatcher"""

from os import PathLike
from pathlib import Path
from typing import Any, Mapping
from cloudpathlib import CloudPath, AnyPath
from ..file_cache.file_cache import FileTypeHandler


class CloudFileMatcher(FileTypeHandler):
    """Files stored somewhere in S3 or other providers

    TODO This implementation is without caching. You need to configure
    the CloudPath default clients to enable caching.
    """

    def resolve(
        self, fname: str | PathLike, **kvargs
    ) -> tuple[None | Path, Mapping[str, Any]]:
        """Open the (cached) file"""
        fpath = AnyPath(fname)
        if isinstance(fpath, CloudPath):
            with fpath.open("rb", **kvargs):
                return Path(fpath.fspath), kvargs

        return None, kvargs
