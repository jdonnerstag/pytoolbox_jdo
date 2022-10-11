#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-function-docstring, missing-module-docstring

from datetime import datetime
from pathlib import Path

import pytest

from pytoolbox_jdo import FileRepo, GzFileMatcher, TarFileMatcher
from pytoolbox_jdo.file_matcher.zip_matcher import ZipFileMatcher
from pytoolbox_jdo.file_matcher.git_matcher import GitFileMatcher

def test_constructor():
    repo = FileRepo(cache_dir=FileRepo.default_tempdir())
    assert repo.cache_dir and repo.cache_dir.is_dir()

    repo = FileRepo(cache_dir=None)
    assert repo.cache_dir is None

def test_gz_no_cache_dir():
    repo = FileRepo(cache_dir=None)
    repo.register(GzFileMatcher("gz", repo.cache_subdir("gz")))

    file = "./tests/data/compress_test_file.txt"
    with repo.open(file + ".gz", mode="rt", encoding="utf-8") as fd1:
        with open(file, mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_gz_with_cache_dir():
    repo = FileRepo(cache_dir=FileRepo.default_tempdir())
    assert repo.cache_dir is not None
    repo.register(GzFileMatcher("gz", repo.cache_subdir("gz")))

    repo.clear_cache()
    file = "./tests/data/compress_test_file.txt"
    with repo.open(file + ".gz", mode="rt", encoding="utf-8") as fd1:
        with open(file, mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()
            fspath = getattr(fd1, "fspath", None)
            assert fspath
            assert Path(file).name == fspath.name
            assert repo.cache_dir
            assert repo.cache_dir.samefile(fspath.parent.parent)

    # Opening it the 2nd time, should give me the cached one
    with repo.open(file + ".gz", mode="rt", encoding="utf-8") as fd1:
        with open(file, mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()
            fspath = getattr(fd1, "fspath", None)
            assert fspath
            assert Path(file).name == fspath.name
            assert repo.cache_dir
            assert repo.cache_dir.samefile(fspath.parent.parent)

def test_tar():
    repo = FileRepo(cache_dir=FileRepo.default_tempdir())
    repo.register(TarFileMatcher("tar", repo.cache_subdir("tar")))
    file = "./tests/data/tests.tar"
    cache = repo.open(file)
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "tar" / "tests.tar")

    # Run it a 2nd time, to definitely use the cache
    cache = repo.open(file)
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "tar" / "tests.tar")

    file = "./tests/data/tests.tar/tests/data/config.py"
    with repo.open(file, mode="rt", encoding="utf-8") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    # Run it a 2nd time, to definitely use the cache
    with repo.open(file, mode="rt", encoding="utf-8") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    with repo.open("tests/data/config.py", mode="rt", encoding="utf-8", tar="./tests/data/tests.tar") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_tar_gz():
    repo = FileRepo(cache_dir=FileRepo.default_tempdir())
    repo.clear_cache()

    repo.register(TarFileMatcher("tar", repo.cache_subdir("tar")))
    repo.register(GzFileMatcher("gz", repo.cache_subdir("gz")))

    file = "./tests/data/tests.tar.gz"
    cache = repo.open(file)
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "tar" / "tests.tar")

    # 2nd attempt with cache already loaded
    file = "./tests/data/tests.tar.gz"
    cache = repo.open(file)
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "tar" / "tests.tar")

    file = "./tests/data/tests.tar.gz/tests/data/config.py"
    with repo.open(file, mode="rt", encoding="utf-8") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    # 2nd attempt with cache loaded
    with repo.open(file, mode="rt", encoding="utf-8") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    file = "./tests/data/tests.tar.gz/tests/data/config.py"
    with repo.open("/tests/data/config.py", mode="rt", encoding="utf-8", tar="./tests/data/tests.tar.gz") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_plain():
    repo = FileRepo(cache_dir=FileRepo.default_tempdir())
    repo.clear_cache()

    repo.register(TarFileMatcher("tar", repo.cache_subdir("tar")))
    repo.register(GzFileMatcher("gz", repo.cache_subdir("gz")))

    # No tar, no gz, no nothing. Should still work.
    file = "./tests/data/config.py"
    with repo.open(file, mode="rt", encoding="utf-8") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_zip():
    repo = FileRepo(cache_dir=FileRepo.default_tempdir())
    repo.clear_cache()

    repo.register(ZipFileMatcher("zip", repo.cache_subdir("zip")))

    file = "./tests/data/tests.zip"
    cache = repo.open(file, pwd="test")
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "zip" / "tests.zip")

    # 2nd attempt with cache already loaded
    file = "./tests/data/tests.zip"
    cache = repo.open(file)
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "zip" / "tests.zip")

    file = "./tests/data/tests.zip/tests/data/config.py"
    with repo.open(file, mode="rt", encoding="utf-8", pwd="test") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    # 2nd attempt with cache loaded
    with repo.open(file, mode="rt", encoding="utf-8") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    with repo.open("./tests/data/config.py", mode="rt", encoding="utf-8", zip="./tests/data/tests.zip", pwd="test") as fd1:
        with open("./tests/data/config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

def test_git():
    repo = FileRepo(cache_dir=FileRepo.default_tempdir())
    repo.clear_cache()

    repo.register(GitFileMatcher("git", repo.cache_subdir("git")))

    # Works with revision, but also branches
    # https://github.com/<user>/<project>/tree/<commit-hash>
    cache = repo.open(".gitignore", git="https://github.com/jdonnerstag/pyfile_spec", revision="master")
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")

    # 2nd attempt with cache already loaded
    cache = repo.open(".gitignore", git="https://github.com/jdonnerstag/pyfile_spec", revision="master")
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")

    # Pull is rather expensive, hence do it only on request
    cache = repo.open(".gitignore", git="https://github.com/jdonnerstag/pyfile_spec", pull=True)
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")

    # The 'initial' branch is remotely available, but not yet locally. Hence pull=True
    cache = repo.open(".gitignore", git="https://github.com/jdonnerstag/pyfile_spec", branch="initial", pull=True)
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")

    cache = repo.open(".gitignore", git="https://github.com/jdonnerstag/pyfile_spec", branch="master", effective_date=datetime(2022, 9, 1))
    assert cache
    assert repo.cache_dir
    assert cache.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")
