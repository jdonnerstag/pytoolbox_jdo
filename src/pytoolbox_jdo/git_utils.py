#!/usr/bin/env python
# encoding: utf-8

"""git utilities"""

import os
from datetime import datetime
from subprocess import Popen, PIPE
from pathlib import Path

from . import logging
from . import file_utils


logger = logging.get_logger(__name__, logging.DEBUG)


def execute_child_process(cmd: list[str], cwd: Path):
    """Change the current working directory and execute the program"""

    cwd = Path(file_utils.create_filename(cwd))
    logger.debug("Exec (cwd: %s): %s", str(cwd), " ".join(cmd))
    with Popen(
        cmd, cwd=cwd, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE
    ) as child:
        outs, errs = child.communicate()
        rtn_code = child.returncode
        rtn = None
        if outs:
            lines = outs.decode().splitlines()
            if lines:
                rtn = lines[0]

            for elem in lines:
                logger.debug(elem)

        if errs:
            lines = errs.decode().splitlines()
            for elem in lines:
                logger.debug(elem)

    if rtn_code:
        raise ChildProcessError(f"Execution failed. cmd={cmd}, error(s)={errs}")

    return rtn


class Git:
    """A couple Git utility functions"""

    def __init__(self, cwd: str | os.PathLike, git_exe="git") -> None:
        self.cwd = cwd
        self.git_exe = git_exe

        if not os.path.isdir(self.cwd):
            raise AttributeError(f"'cwd' must be an existing directory: {self.cwd}")

        self.cwd = Path(self.cwd)

    def git_exec(self, git_args: list[str]):
        """Execute git applying the 'git_args' in the directory specified"""

        cmd = [self.git_exe] + git_args
        assert isinstance(self.cwd, Path)
        return execute_child_process(cmd, self.cwd)

    def determine_revision(self, effective_date: None | datetime, branch: None | str):
        """Determine which revision was effective in the branch at that time"""
        logger.debug(
            "Determine GIT revision for repo: %s; branch: %s, effective date: %s",
            self.cwd,
            branch,
            effective_date,
        )

        cmd = ["rev-list", "-n", "1"]
        if effective_date:
            # git rev-list -n 1 --before="2018-09-01 23:59:59" master
            # str() convert datetime nicely into "2018-09-01 23:59:59"
            date = str(effective_date)
            date = date.replace("9999-", "2099-")
            cmd += [f'--before="{date}"']

        if branch:
            cmd += [branch]

        return self.git_exec(cmd)
