import glob
import os
import re
import time
from datetime import timedelta
from pathlib import PurePath

import numpy as np

# Decorators


def stopwatch(method):
    def timed(*args, **kw):
        ts = time.perf_counter()
        result = method(*args, **kw)
        te = time.perf_counter()
        duration = timedelta(seconds=te - ts)
        print(f"    -> {method.__name__} took: {duration}")
        return result

    return timed


# Consistent output


def print_file_item(file):
    print("  - " + file)


# String manipulation


def unpack_str(attr):
    if isinstance(attr, np.ndarray):
        result = attr[0]
    else:
        result = attr
    return result


def tex_format(str):
    if str == "":
        newstr = str
    else:
        newstr = "$" + str + "$"
    return newstr


def get_regex_snippet(pattern, string):
    return re.search(pattern, string).group(0)


# I/O


def prep_file_input(files):
    if isinstance(files, str):
        filelist = [os.path.expanduser(files)]
    else:
        filelist = [os.path.expanduser(f) for f in files]
    return filelist


def get_abs_filepaths(path, run_dir, quant_files):
    filepaths_to_read = []
    for file in quant_files:
        fileloc = glob.glob(
            "**/" + file, recursive=True, root_dir=os.path.join(path, run_dir)
        )
        fullloc = [os.path.join(path, run_dir, loc) for loc in fileloc]
        filepaths_to_read = filepaths_to_read + fullloc
    return filepaths_to_read


def find_runs(path, runs_pattern):
    dirs = []
    run_names = []

    runs_list = prep_file_input(runs_pattern)

    # Try to find directories matching runs_pattern

    for run in runs_list:
        filesindir = sorted(glob.glob(run, root_dir=path))
        dirs = dirs + [
            folder for folder in filesindir if os.path.isdir(os.path.join(path, folder))
        ]

    run_names = dirs

    # In case no run folders are found

    if len(run_names) == 0:
        print("Could not find any run folder:")
        print(" - Checking whether already inside folder... ")
        # Check whether already inside run folder
        folder = PurePath(path).parts[-1]
        try:
            assert any([folder == item for item in runs_pattern])
        except AssertionError:
            print("     ...no")
            print(" - Proceeding without a run name.")
            run_names = ["undefined"]
        else:
            print("     ...yes")
            run_names = [folder]
        finally:
            dirs.append(".")

    # Save data in dictionary

    dirs_dict = {}
    for i, k in enumerate(run_names):
        dirs_dict[k] = dirs[i]

    return dirs_dict


def find_quants():
    return
