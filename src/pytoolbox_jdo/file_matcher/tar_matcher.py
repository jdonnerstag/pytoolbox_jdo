#!/usr/bin/env python
# encoding: utf-8

"""TarFileMatcher"""

import os
from os import PathLike
from typing import Any
from pathlib import Path
import tarfile
import shutil
from .base_file_matcher import BaseFileMatcher


class TarFileMatcher(BaseFileMatcher):
    """Unpack tar files into a cache directory"""

    extension = "tar"

    def match(self, fname: str | PathLike, **kvargs) -> bool:
        if kvargs.get(self.extension, None):
            return True

        # We also want to support ./dir/my.tar/subdir/file.txt
        fname = str(fname).replace("\\", "/")
        if f".{self.extension}/" in fname:
            return True

        return fname.endswith(f".{self.extension}") and os.path.isfile(fname)

    def cache_filename(self, fname: PathLike) -> str:
        return Path(fname).name

    def update_cache(self, fname: Path, cached_file: Path, *args, **kvargs):
        """Untar the file into the directory provided"""

        outdir = cached_file
        if outdir.is_dir():
            shutil.rmtree(outdir)

        os.mkdir(outdir)

        self.extractall(fname, outdir, *args, **kvargs)

    def extractall(self, fname, outdir, *_args, **_kvargs):
        """Extract all files into outdir"""
        with self.open_uncached(fname) as tar:
            tar.extractall(path=outdir)

    def open_uncached(self, fname: str|PathLike, *args, **kvargs) -> Any:
        return tarfile.open(fname, "r")

    def open(self, fname: str|PathLike, *args, **kvargs) -> Any:
        container_file = kvargs.get(self.extension, None)
        if container_file:
            fpath = str(fname)
            if fpath[0] in "/\\":
                fpath = fpath[1:]
        else:
            container_file, fpath = self.split_container(fname, self.extension)

        file = self.get_or_update_cache(container_file, *args, **kvargs)
        if file is None or not fpath:
            return file

        # Only relevant for opening the zip file
        kvargs.pop("pwd", None)
        kvargs.pop(self.extension, None)

        file = file / fpath
        return file.open(*args, **kvargs)
