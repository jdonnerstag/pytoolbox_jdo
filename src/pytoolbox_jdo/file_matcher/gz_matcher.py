#!/usr/bin/env python
# encoding: utf-8

"""GzFileMatcher"""

from pathlib import Path
import os
from os import PathLike
import gzip
from typing import Any, Mapping
from .base_file_matcher import BaseFileMatcher


class GzFileMatcher(BaseFileMatcher):
    """Unzip GZ files and cache for faster access"""

    def cache_filename(self, fname: str|PathLike) -> str:
        """Determine the cache file name, e.g. myfiles.csv.gz => myfiles.csv"""
        return Path(fname).stem

    def open_uncached(self, fname: str|PathLike, *args, **kvargs) -> Any:
        return gzip.open(fname, *args, **kvargs)

    def resolve(self, fname: str|PathLike, **kvargs) -> tuple[None|Path, Mapping[str, Any]]:
        # We also want to support ./dir/my.tar.gz/subdir/file.txt
        fname = str(fname)
        if not os.path.isfile(fname) or not fname.endswith(".gz"):
            return None, kvargs

        return self.get_or_update_cache(fname, **kvargs), kvargs
