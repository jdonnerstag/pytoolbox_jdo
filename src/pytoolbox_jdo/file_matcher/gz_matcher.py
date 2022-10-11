#!/usr/bin/env python
# encoding: utf-8

"""GzFileMatcher"""

import os
from os import PathLike
import gzip
from typing import Any
from .base_file_matcher import BaseFileMatcher


class GzFileMatcher(BaseFileMatcher):
    """Unzip GZ files and cache for faster access"""

    def match(self, fname: str | PathLike, **kvargs) -> bool:
        # We also want to support ./dir/my.tar.gz/subdir/file.txt
        fname = str(fname).replace(r"\\", "/")
        if ".gz/" in fname:
            return True

        return fname.endswith(".gz") and os.path.isfile(fname)

    def open_uncached(self, fname: str|PathLike, *args, **kvargs) -> Any:
        return gzip.open(fname, *args, **kvargs)

    def open(self, fname: str|PathLike, *args, **kvargs) -> Any:
        gz_file, fpath = self.split_container(fname, "gz")
        file = super().open(gz_file, *args, **kvargs)

        # Convert e.g. ./my.tar.gz/myfile.txt => ./my.tar/myfile.txt
        fspath = getattr(file, "fspath", None)
        if fspath is not None and fpath:
            setattr(file, "fspath", fspath / fpath)

        return file
