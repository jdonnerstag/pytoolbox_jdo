#!/usr/bin/env python
# encoding: utf-8

"""File utilities"""

# TODO Several functions are not really generic

import os
import re
import io
import gzip
from pathlib import Path
import multiprocessing as mp
from contextlib import contextmanager
from cloudpathlib import AnyPath
from typing import Any

from . import logging

logger = logging.get_logger(__name__, logging.DEBUG)


def create_filename(*paths):
    """Join the elements into a path, expand ~user and envvars,
    and standardize on "/" as separator"""

    file = os.path.join(*paths)
    file = os.path.expandvars(file)
    file = AnyPath(file)
    if isinstance(file, Path):
        file = file.expanduser()

    return file


def split_path(file: str) -> tuple[AnyPath, str | None]:
    """Split the filename into the static part and flexible part

    E.g. it is possible to have **/*.xlsx in the flexible part
    """
    res = re.match(r"([^\*]+[/\\])(.*)", file)
    if not res:
        return AnyPath("."), file

    dirpart = res.group(1)
    filepart = res.group(2)
    if not dirpart and filepart:
        return AnyPath(filepart), None

    return AnyPath(dirpart), filepart


def glob_argv_files(files: None | str | list[str]):
    """On Linux cmdline args are globbed. On Windows they are not."""
    if not files:
        return None

    if isinstance(files, str):
        files = [files]

    rtn: list[AnyPath] = []
    for file in files:
        if not files:
            continue

        file = os.path.expandvars(file)
        file = os.path.expanduser(file)
        dirpart, filepart = split_path(file)

        # Pylint false-positive :(#
        # pylint: disable=no-member
        gen = (dirpart / file for file in dirpart.glob(filepart))  # type: ignore
        rtn.extend(gen)

    return rtn


def mkdir(fname, mode=0o777, deep=False):
    """Create a directory for the FILE provided"""
    dirname = os.path.dirname(fname)
    if not os.path.exists(dirname):
        if deep:
            os.makedirs(dirname, mode=mode)
        else:
            os.mkdir(dirname, mode=mode)


"""
def filterFilesByDate(files, dt):
    if not dt:
        return files

    ar = []
    for file in files:
        filedate = getDateFromFile(file)
        if dt and filedate and dt >= filedate:
            ar.append(file)
        else:
            logger.debug("Ignore file because of effective date: %s - %s", dt, file)

    return ar


def cleanupFilesByType(filesByType):
    return {cat: files for cat, files in filesByType.items() if files}


def sortFilesByDate(files):
    return sorted(files, key=getDateFromFile)


def getFileTypes(files):
    logger.debug("Determine the PIL file config for each file")
    return [module_finder.getModuleClass(file) for file in files]


def file_info2(fname, ftype=None):
    ftype = ftype or pil.module_finder.getModuleClass(fname)
    full = isFullFile(fname)
    date = getDateFromFile(fname)

    return {"name": fname, "class": ftype, "isFull": full, "date": date}


def groupFilesByType(files, fileTypes):
    rtn = {}
    for i, file in enumerate(files):
        ftype = fileTypes[i]
        info = file_info2(file, ftype)
        info["idx"] = i
        name = ftype.filetype()

        if name not in rtn:
            rtn[name] = [info]
        else:
            rtn[name].append(info)

    return rtn


def findLastMatchingFull(files, commissionPeriod):
    commissionPeriod = int(commissionPeriod)

    idx = None
    for i, file in enumerate(files):
        if file["isFull"]:
            date = file["date"]
            if date:
                date = int(date[0:6])
                if date <= commissionPeriod:
                    idx = i

    return idx


def getLatestFullAndDeltas(filesByType, comPeriod):
    for cat, files in filesByType.items():
        idx = findLastMatchingFull(files, comPeriod)
        if idx is None:
            logger.warn("No Full or VTAG file found for type: %s", cat)
            filesByType[cat] = None
        elif idx > 0:
            for file in files[0:idx]:
                logger.debug("Ignore as newer FULL/VTAG file found: %s", file["name"])

            filesByType[cat] = [
                file
                for i, file in enumerate(files[idx:])
                if i == 0 or not file["isFull"]
            ]

    return filesByType


def prepareFilesFromCmdLine(files, commissionPeriod, effectiveDate):
    logger.debug("Input files: %s", files)
    files = globArgvFiles(files)
    if not files:
        logger.warn("No input files found")

    files = filterFilesByDate(files, effectiveDate)
    if not files:
        logger.warn("No files left after applying effective date criteria")

    files = sortFilesByDate(files)
    fileTypes = getFileTypes(files)
    filesByType = groupFilesByType(files, fileTypes)
    filesByType = getLatestFullAndDeltas(filesByType, commissionPeriod)
    filesByType = cleanupFilesByType(filesByType)

    return filesByType


def removeEventFiles(filesByType):
    ar = []
    for k, v in filesByType.items():
        for file in v:
            ftype = file["class"]
            if ftype.EVENT_FILE:
                ar.append(k)
            break

    for k in ar:
        del filesByType[k]



def prepareArgvFiles(config, groupByFileType=False, fullDelta=False, fileType=None):
    if fileType or fullDelta:
        groupByFileType = True

    if isinstance(config, argparse.Namespace):
        config = vars(config)

    files = globArgvFiles(config["files"])
    if not files:
        logger.warn("No input files found")

    date = config.get("effectiveDate", None)
    if date:
        files = filterFilesByDate(files, date)
        if not files:
            logger.warn("No files left after applying effective date criteria")

    files = sortFilesByDate(files)
    if not groupByFileType:
        return files

    fileTypes = getFileTypes(files)
    filesByType = groupFilesByType(files, fileTypes)

    # If true, only keep files where FULL/DELTA is used (and make sense).
    # E.g. it doesn't make sense for event files
    if fullDelta:
        removeEventFiles(filesByType)

        # Select only the files relevant for a specific commission period. With respect to
        # FULL/DELTA files, it means, we only need the latest FULL before the end of the
        # commission period, and the deltas until then.
        if "commissionPeriod" in config:
            filesByType = getLatestFullAndDeltas(
                filesByType, config["commissionPeriod"]
            )
        else:
            raise Exception("'fullDelta' requires args.commissionPeriod")

    filesByType = cleanupFilesByType(filesByType)

    if fileType:
        return filesByType.get(fileType, [])

    return filesByType


def determineOutFileName(
    infile, outfile, fileConfig=None, extension=None, dateSubdir=False, subdir=None
):
    if isinstance(infile, dict):
        infile = infile["name"]

    if os.path.isdir(outfile):
        if subdir:
            outfile = os.path.join(outfile, subdir)
            if not os.path.exists(outfile):
                os.mkdir(outfile)

        if fileConfig:
            ftype = fileConfig.filetype()
            outfile = os.path.join(outfile, ftype)
        else:
            # Default: Use the filename as file type
            outfile = os.path.join(outfile, os.path.basename(infile))
            outfile = re.sub(r"\.(xlsx|xls|csv|gz|tar|tar\.gz)$", "", outfile)

        if not os.path.exists(outfile):
            os.mkdir(outfile)

        if dateSubdir:
            date = getDateFromFile(infile)[0:6]
            outfile = os.path.join(outfile, date)

            if not os.path.exists(outfile):
                os.mkdir(outfile)

        root_dir = None
        if root_dir:
            subdir = os.path.relpath(infile, root_dir)
            if os.path.pardir in subdir:
                raise Exception(
                    "File must in root_dir (recursive): file={}  root_dir={}".format(
                        infile, root_dir
                    )
                )

            subdir = os.path.dirname(subdir)
            outfile = os.path.join(outfile, subdir)
            os.makedirs(outfile, exist_ok=True)

        outfile = os.path.join(outfile, os.path.basename(infile))

    if extension:
        (name, ext) = os.path.splitext(outfile)
        if ext in [".gz", ".xls", ".xlsx"]:
            outfile = name

        outfile += extension

    outfile = pil.file_utils.abspath(outfile)
    return outfile



def combineOutFile(name, date, extension):
    if date:
        name += "." + date.strftime("%Y%m%d%H%M%S")

    if extension:
        name += extension

    return name


def getDateString(ts, format=None, withTime=False):
    if isinstance(ts, str):
        return ts

    if not ts:
        ts = datetime.datetime.now()

    if not format:
        if not withTime:
            format = "%Y%m%d"
        else:
            format = "%Y%m%d%H%M%S"

    ts = ts.strftime(format)
    return ts


def execFiles(func, files, process_pool, globFiles=True):
    if globFiles:
        files = globArgvFiles(files)

    if process_pool > 0 and len(files) > 1:
        process_pool = min(process_pool, files)
        with mp.Pool(processes=process_pool) as pool:
            pool.map(func, files)
    else:
        logger.info("%d files to process", len(files))
        for file in files:
            func(file)


gFS = []


def find_fs(root_dir):
    global gFS

    if not gFS:
        return (None, root_dir)
        # raise Exception("You must invoke pil.file_utils.init_fs(some_dir) to initialize the virtual file system")

    root_dir = root_dir.replace("\\", "/")
    for elem in gFS:
        fs_root_dir = getattr(elem, "root_path", None)
        fs_root_dir = fs_root_dir or getattr(elem, "root_dir", None)
        fs_root_dir = fs_root_dir.replace("\\", "/")
        if root_dir.startswith(fs_root_dir):
            rest = root_dir[len(fs_root_dir) :]
            return (elem, rest)

    return (None, None)


def init_fs(root_dir):
    global gFS

    root_dir = root_dir.replace("\\", "/")
    newFS, _ = find_fs(root_dir) if gFS else (None, None)
    if not newFS:
        if not root_dir.endswith("/"):
            root_dir += "/"

        newFS = vfs.open_fs(root_dir)
        gFS.append(newFS)
        logger.debug("Registered virtual filesystem: %s", newFS)

    return newFS


# Incl. S3 support
def exists(file):
    file = file.replace("\\", "/")
    fs, fname = find_fs(file)
    if fs:
        info = fs.getinfo(fname)
        return info
    else:
        return os.path.exists(file)


# Incl. S3 support
def file_info(file):
    if isinstance(file, dict):
        file = file["name"]

    file = file.replace("\\", "/")
    fs, fname = find_fs(file)
    if not fs:
        fs = vfs.open_fs(os.path.dirname(fname))
        fname = os.path.basename(fname)

    try:
        return fs.getinfo(fname, namespaces=["details"])
    except vfs.errors.ResourceNotFound:
        return None


def fileRequiresUpdate(infile, outfile, config):
    if config and config.get("force_update"):
        return True

    infoB = file_info(outfile)
    if not infoB:
        return True

    infoA = file_info(infile)
    rtn = infoA.modified > infoB.modified

    if not rtn:
        logger.debug("Out-file already up-to-date")

    return rtn


def prependRootPath(args, *argv):
    if argv and isinstance(argv[-1], list):
        fixed = argv[0:-1]
        ar = argv[-1]
        rtn = [os.path.join(args.root_dir, *fixed, last) for last in ar]
    else:
        rtn = os.path.join(args.root_dir, *argv)

    placeholder = {}
    placeholder["com_period"] = getCommissionPeriodDirectoryName(
        args.commissionPeriod, args.effectiveDate
    )
    if isinstance(rtn, list):
        return [pil_utils.replacePlaceholder(v, placeholder) for v in rtn]
    else:
        return pil_utils.replacePlaceholder(rtn, placeholder)


def names_from_fileConfig(fileConfig):
    return [field["name"] for field in fileConfig.FIELDSPECS]


def len_from_fileConfig(fileConfig):
    return [field["len"] for field in fileConfig.FIELDSPECS]


def dtypes_from_fileConfig(fileConfig):
    return {field["name"]: field.get("dtypes") for field in fileConfig.FIELDSPECS}


def converters_from_fileConfig(fileConfig):
    return {
        field["name"]: field.get("pd.read.converters")
        for field in fileConfig.FIELDSPECS
    }
"""
