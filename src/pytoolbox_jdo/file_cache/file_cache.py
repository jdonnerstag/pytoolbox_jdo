#!/usr/bin/env python
# encoding: utf-8

"""Some files are in the cloud, some local, some compressed, etc. etc.

This module aims at making it a little easier to transparently download,
cache, uncompress files, so that users don't need to worry about it
anymore.

Think of S3 or gcp files, *.gz, *.tar.gz, *.zip, git, etc.
"""

import abc
import os
from os import PathLike
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping
from .. import logging

logger = logging.get_logger(__name__, logging.DEBUG)


class FileTypeHandler(metaclass=abc.ABCMeta):
    """This is the (abstract) based class for all FileMatchers.

    Every concrete implementation may handle a differnt aspect, e.g
    one FileMatcher to download cloud files, one to uncompress *.gz
    file, one to unpack *.tar files. Multiple FileMatchers might
    get executed, e.g. to download cloud *.tar.gz files.
    """

    def __init__(self, name: str, cache_dir: None | Path) -> None:
        self.name = name
        self.cache_dir = cache_dir

    @abc.abstractmethod
    def resolve(
        self, fname: str | PathLike, **kvargs
    ) -> tuple[None | Path, Mapping[str, Any]]:
        """Do whatever is necessary to open the file.

        Note that strictly speaking the return value doesn't have to be a
        file handle. E.g. the Tar FileMatcher returns the 'Path' to
        the directory where the tar file has been unpacked.
        """


class FileCache:
    """Provide easy access to files which might be in the cloud,
    compressed (e.g. *.gz), or file containers (*.tar).

    To do whatever is necessary, FileRepo leverages a flexible list
    of FileMatcher. The sequence is important. The first matcher
    confirming that it is able to handle it, will get the request.
    The same process gets applied to the output of the previous step,
    until no more matcher is applicable.

    The general idea is that a FileMatcher create one or more
    cache files, and the cache file is the input to the next stage.
    """

    @classmethod
    def default_tempdir(cls) -> Path:
        """A utility (class) method to determine The default (root) cache directory"""
        cache_dir = Path(tempfile.gettempdir()) / "FileRepo"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.repo: list[FileTypeHandler] = []

    def register(self, matcher: FileTypeHandler, insert: int = -1):
        """Register an additional matcher"""
        if insert <= 0:
            self.repo.append(matcher)
        else:
            self.repo.insert(insert, matcher)

    def resolve(self, fname: str | PathLike, **kvargs) -> None | str | PathLike:
        """Do whatever is necessary to open the file.

        E.g. download, uncompress, unpack, etc.

        Even though the return value can be anything, it usually
        is a file handle. But e.g. the TarFileMatcher returns a Path
        to the directory where the files have been unpacked.
        Often you want to access a file from the tar or zip file,
        which is also possible, e.g. ./my.zip/subdir/file.dat,
        """
        file: None | str | PathLike = fname
        i = 0
        while i < len(self.repo):
            cached_file, kvargs = self.repo[i].resolve(file, **kvargs)
            if cached_file:
                i = 0
                file = cached_file
            else:
                i += 1

        if isinstance(file, str) and os.path.exists(file):
            file = Path(file)

        return file

    def clear_cache(self, subdir: None | str = None):
        """Delete all files in the cache-dir"""

        def on_rm_error(_func, path, _exc_info):
            # path contains the path of the file that couldn't be removed
            # let's just assume that it's read-only and unlink it.
            os.chmod(path, 0o777)
            os.unlink(path)

        if self.cache_dir:
            if subdir:
                shutil.rmtree(self.cache_dir / subdir, onerror=on_rm_error)
            else:
                shutil.rmtree(self.cache_dir, onerror=on_rm_error)
                self.cache_dir.mkdir()

    def cache_subdir(self, subdir: str):
        """When creating a FileMatcher, it must be provided a cache-dir.
        Often you want it to be a sub-directory of the repo's cache dir.
        Leveraging the FileMatcher's name is often a good idea.

        E.g. repo.register(TarFileMatcher("tar", repo.cache_subdir("tar")))
        """
        if self.cache_dir is None:
            return None

        return self.cache_dir / subdir
