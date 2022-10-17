#!/usr/bin/env python
# encoding: utf-8

"""TarFileMatcher"""

import os
from os import PathLike
from typing import Any, Mapping
from pathlib import Path
import tarfile
import shutil
from .base_file_matcher import BaseFileMatcher


class TarFileMatcher(BaseFileMatcher):
    """Unpack tar files into a cache directory"""

    extension = ["tar", "tar.gz"]

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
        suffix = str(fname).rsplit(".", maxsplit=1)[-1]
        read = "r"
        if suffix != "tar":
            read = "r:" + suffix

        return tarfile.open(fname, read)

    def resolve(self, fname: str|PathLike, **kvargs) -> tuple[None|Path, Mapping[str, Any]]:
        container_file = kvargs.pop(self.extension[0], None)
        if container_file:
            fpath = fname
        else:
            # We also want to support ./dir/my.tar/subdir/file.txt
            container_file, fpath = self.split_container(fname, self.extension)
            if container_file is None:
                return None, kvargs

        if not os.path.isfile(container_file):
            return None, kvargs

        file = self.get_or_update_cache(container_file, **kvargs)
        if file is None:
            return None, kvargs

        if fpath is None:
            return file, kvargs

        return file / fpath, kvargs
