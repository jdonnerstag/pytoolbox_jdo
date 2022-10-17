#!/usr/bin/env python
# encoding: utf-8

"""BaseFileMatcher"""

import abc
from os import PathLike
from pathlib import Path
from typing import Any, Mapping
from ..file_cache.file_cache import FileTypeHandler


class BaseFileMatcher(FileTypeHandler, metaclass=abc.ABCMeta):
    """An abstract base class, extending FileMatcher, providing
    common functionalities for a number of concrete FileMatcher
    implementations.
    """

    def cache_filename(self, fname: str|PathLike) -> str:
        """Determine the cache file name, e.g. myfiles.csv.gz => myfiles.csv"""
        return Path(fname).name

    def cache_path(self, fname: str|PathLike) -> None|Path:
        """Cache directory + cache file"""
        if not self.cache_dir:
            return None

        return self.cache_dir / self.cache_filename(fname)


    def mtime(self, fname: str|PathLike) -> int:
        """Determine when the (local) cached file was last modified"""
        fname = Path(fname)
        return int(fname.stat().st_mtime)

    def is_cache_eligible(self, cached_file: Path, fname: str|PathLike) -> bool:
        """True, if the cached file is up-to-date"""
        mtime_source = int(self.mtime(fname))
        mtime_cached = int(cached_file.stat().st_mtime)
        return mtime_cached > mtime_source

    def delete_cache(self, fname: str | PathLike) -> None:
        """Delete the cache file if existing"""

        cached_file = self.cache_path(fname)

        if cached_file and cached_file.exists():
            cached_file.unlink()

    @abc.abstractmethod
    def open_uncached(self, fname: str|PathLike, *args, **kvargs) -> Any:
        """Open the uncached file"""

    def update_cache(self, fname: str|PathLike, cached_file: Path, **kvargs):
        """Update the cache"""
        with self.open_uncached(fname, "rb", **kvargs) as infile:
            with open(cached_file, "wb") as outfile:
                outfile.write(infile.read())

    def get_or_update_cache(self, fname: str|PathLike, **kvargs) -> None|Path:
        """Update the cache if necessary and return the cache file"""
        if not self.cache_dir:
            return None

        cached_file = self.cache_path(fname)
        if not cached_file:
            return None

        if self.cache_dir and not self.cache_dir.exists():
            self.cache_dir.mkdir()

        if not cached_file.exists():
            self.update_cache(fname, cached_file, **kvargs)
        elif not self.is_cache_eligible(cached_file, fname):
            self.update_cache(fname, cached_file, **kvargs)

        return cached_file if cached_file.exists() else None

    def resolve(self, fname: str|PathLike, **kvargs) -> tuple[None|Path, Mapping[str, Any]]:
        return self.get_or_update_cache(fname, **kvargs), kvargs


    def split_container(self, fname, extensions: list[str]):
        """Split e.g. ./my.tar.gz/file.txt into (./my.tar.gz, file.txt)"""

        fname = str(fname).replace("\\", "/")
        for ext in extensions:
            if fname.endswith(f".{ext}"):
                return fname, None

            pos = fname.find(f".{ext}/")
            if pos != -1:
                pos = pos + len(ext) + 1
                return fname[:pos], fname[pos + 1:]

        return None, None
