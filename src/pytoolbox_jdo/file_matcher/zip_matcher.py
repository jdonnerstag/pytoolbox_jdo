#!/usr/bin/env python
# encoding: utf-8

"""ZipFileMatcher"""

from os import PathLike
from typing import Any
import zipfile
from .tar_matcher import TarFileMatcher


class ZipFileMatcher(TarFileMatcher):
    """Unpack zip files into a cache directory"""

    extension = "zip"

    def extractall(self, fname, outdir, *args, **kvargs):
        """Extract all files into outdir"""
        with self.open_uncached(fname, *args, **kvargs) as zipfd:
            zipfd.extractall(path=outdir)

    def open_uncached(self, fname: str|PathLike, *args, **kvargs) -> Any:
        password = kvargs.pop("pwd", None)
        rtn = zipfile.ZipFile(fname, "r")
        if password:
            password = bytes(password, "utf-8")
            rtn.setpassword(password)

        return rtn
