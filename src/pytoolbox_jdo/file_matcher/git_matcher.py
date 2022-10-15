#!/usr/bin/env python
# encoding: utf-8

"""GitFileMatcher"""

from datetime import datetime
import os
from os import PathLike
from typing import Any
from pathlib import Path
from urllib.parse import urlparse
from .base_file_matcher import BaseFileMatcher
from ..git_utils import Git


class GitFileMatcher(BaseFileMatcher):
    """Make git files accessible"""

    def match(self, _fname: str | PathLike, git=None, **kvargs) -> bool:
        return bool(git)

    def cache_filename(self, fname: str|PathLike) -> str:
        """Determine the cache file name"""
        fname = str(fname).replace("\\", "/")
        if os.path.isdir(fname):
            return Path(fname).name

        url = urlparse(fname)
        path = url.path.split(";")[0]
        path = path.split("/")
        project = path[2] if len(path) > 2 else None
        if not project:
            raise AttributeError(f"Invalid github url. Missing 'project name' in {fname}")

        return project

    def update_cache(self, fname: str|PathLike, cached_file: Path, *args, **kvargs):
        # Github does not support "git archive --remote=http://".

        cwd = cached_file

        revision = kvargs.get("revision", None)
        branch = kvargs.get("branch", None)
        effective_date = kvargs.get("effective_date", None)

        if not cached_file.is_dir():
            Git(cached_file.parent).git_exec(["clone", str(fname)])

        git = Git(cwd)
        if not revision and effective_date:
            assert effective_date is None or isinstance(effective_date, datetime), f"Argument 'effective_date' must be a datetime: '{effective_date}'"
            revision = git.determine_revision(effective_date=effective_date, branch=branch)
        else:
            if branch:
                git.git_exec(["checkout", branch])

            if kvargs.get("pull", False):
                git.git_exec(["pull"])

        if revision:
            git.git_exec(["reset", "--hard", revision])

        # TODO If we wanted parallel access, then we may need to make a copy into
        #      a separate directory

    def is_cache_eligible(self, _cached_file: Path, _mtime_source: int) -> bool:
        return False

    def open_uncached(self, fname: str|PathLike, *args, **kvargs) -> Any:
        pass

    def open(self, fname: str|PathLike, *args, **kvargs) -> Any:
        git = kvargs.get("git", None)
        if not git:
            raise AttributeError(f"Missing the mandatory 'repo' arguments: {fname}")

        file = self.get_or_update_cache(git, *args, **kvargs)
        if file is None:
            return file

        return file / fname
