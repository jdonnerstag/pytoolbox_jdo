#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pylint: disable=missing-function-docstring, missing-module-docstring

from datetime import datetime
from pathlib import Path

import pytest

from pytoolbox_jdo import FileCache, GzFileMatcher, TarFileMatcher
from pytoolbox_jdo import ZipFileMatcher, GitFileMatcher
from pytoolbox_jdo import CloudFileMatcher


data_dir = Path(__file__).parent / "data"


def test_constructor():
    repo = FileCache(cache_dir=FileCache.default_tempdir())
    assert repo.cache_dir and repo.cache_dir.is_dir()


def test_gz():
    repo = FileCache(cache_dir=FileCache.default_tempdir())
    assert repo.cache_dir is not None
    repo.register(GzFileMatcher("gz", repo.cache_subdir("gz")))

    repo.clear_cache()
    file = data_dir / "compress_test_file.txt"
    cached_file = repo.resolve(str(file) + ".gz")
    assert isinstance(cached_file, Path)
    assert cached_file.exists()
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(file, mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    # Opening it the 2nd time, should give me the cached one
    cached_file = repo.resolve(str(file) + ".gz")
    assert isinstance(cached_file, Path)
    assert cached_file.exists()
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(file, mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_tar():
    repo = FileCache(cache_dir=FileCache.default_tempdir())
    assert repo.cache_dir
    repo.register(TarFileMatcher("tar", repo.cache_subdir("tar")))
    file = data_dir / "data.tar"
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    assert cached_file.samefile(repo.cache_dir / "tar" / "data.tar")

    # Run it a 2nd time, to definitely use the cache
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    assert cached_file.samefile(repo.cache_dir / "tar" / "data.tar")

    file = data_dir / "data.tar/data/config.py"
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    # Run it a 2nd time, to definitely use the cache
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    cached_file = repo.resolve("data/config.py", tar=data_dir / "data.tar")
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_tar_gz():
    repo = FileCache(cache_dir=FileCache.default_tempdir())
    repo.clear_cache()

    repo.register(TarFileMatcher("tar", repo.cache_subdir("tar")))
    repo.register(GzFileMatcher("gz", repo.cache_subdir("gz")))

    file = data_dir / "data.tar.gz"
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "tar" / "data.tar.gz")

    # 2nd attempt with cache already loaded
    file = data_dir / "data.tar.gz"
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "tar" / "data.tar.gz")

    file = data_dir / "data.tar.gz/data/config.py"
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "./config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    # 2nd attempt with cache loaded
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "./config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    file = "./data/config.py"
    cached_file = repo.resolve(file, tar=data_dir / "data.tar.gz")
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "./config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_plain():
    repo = FileCache(cache_dir=FileCache.default_tempdir())
    repo.clear_cache()

    repo.register(TarFileMatcher("tar", repo.cache_subdir("tar")))
    repo.register(GzFileMatcher("gz", repo.cache_subdir("gz")))

    # No tar, no gz, no nothing. Should still work.
    file = data_dir / "config.py"
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_zip():
    repo = FileCache(cache_dir=FileCache.default_tempdir())
    repo.clear_cache()

    repo.register(ZipFileMatcher("zip", repo.cache_subdir("zip")))

    file = data_dir / "data.zip"
    cached_file = repo.resolve(file, pwd="test")
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "zip" / "data.zip")

    # 2nd attempt with cache already loaded
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "zip" / "data.zip")

    file = data_dir / "data.zip/data/config.py"
    cached_file = repo.resolve(file, pwd="test")
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "./config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    # 2nd attempt with cache loaded
    cached_file = repo.resolve(file, pwd="test")
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "./config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()

    file = data_dir / "config.py"
    cached_file = repo.resolve(file, zip=data_dir / "data.zip", pwd="test")
    assert isinstance(cached_file, Path)
    with cached_file.open(mode="rt", encoding="utf-8") as fd1:
        with open(data_dir / "./config.py", mode="rt", encoding="utf-8") as fd2:
            assert fd1.read() == fd2.read()


def test_git():
    repo = FileCache(cache_dir=FileCache.default_tempdir())
    repo.clear_cache()

    repo.register(GitFileMatcher("git", repo.cache_subdir("git")))

    # Works with revision, but also branches
    # https://github.com/<user>/<project>/tree/<commit-hash>
    cached_file = repo.resolve(
        ".gitignore",
        git="https://github.com/jdonnerstag/pyfile_spec",
        revision="master",
    )
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")

    # 2nd attempt with cache already loaded
    cached_file = repo.resolve(
        ".gitignore",
        git="https://github.com/jdonnerstag/pyfile_spec",
        revision="master",
    )
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")

    # Pull is rather expensive, hence do it only on request
    cached_file = repo.resolve(
        ".gitignore", git="https://github.com/jdonnerstag/pyfile_spec", pull=True
    )
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")

    # The 'initial' branch is remotely available, but not yet locally. Hence pull=True
    cached_file = repo.resolve(
        ".gitignore",
        git="https://github.com/jdonnerstag/pyfile_spec",
        branch="initial",
        pull=True,
    )
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")

    cached_file = repo.resolve(
        ".gitignore",
        git="https://github.com/jdonnerstag/pyfile_spec",
        branch="master",
        effective_date=datetime(2022, 9, 1),
    )
    assert isinstance(cached_file, Path)
    assert repo.cache_dir
    assert cached_file.samefile(repo.cache_dir / "git/pyfile_spec/.gitignore")


@pytest.mark.slow
def test_cloudpath():
    print("Run (slow) cloud test")

    repo = FileCache(cache_dir=FileCache.default_tempdir())
    repo.clear_cache()

    repo.register(TarFileMatcher("tar", repo.cache_subdir("tar")))
    repo.register(GzFileMatcher("gz", repo.cache_subdir("gz")))
    repo.register(CloudFileMatcher("cloud", repo.cache_subdir("cloud")))

    # For this to work, you must have ~\.aws\config properly set up
    file = "s3://genome-idx/lev/chm13v2-grch38.tar.gz"
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    for file in cached_file.glob("**/*.*"):
        print(file)

    file = "s3://genome-idx/lev/chm13v2-grch38.tar.gz"
    cached_file = repo.resolve(file)
    assert isinstance(cached_file, Path)
    for file in cached_file.glob("**/*.*"):
        print(file)
