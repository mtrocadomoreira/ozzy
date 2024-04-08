import os

import pandas as pd

from .backend import Backend
from .new_dataset import new_dataset as new_dataset_func
from .utils import (
    find_runs,
    get_abs_filepaths,
    prep_file_input,
    print_file_item,
    stopwatch,
)

# -----------------------------------------------------------------------
# Core functions
# -----------------------------------------------------------------------


def new_dataset(*args, **kwargs):
    return new_dataset_func(*args, **kwargs)


def open(path, file_type, axes_lims=None):
    filelist = prep_file_input(path)

    # initialize the backend object (it deals with the error handling)
    bknd = Backend(file_type, axes_lims, as_series=False)

    ods = bknd.parse_data(filelist)

    return ods


@stopwatch
def open_series(files, file_type, axes_lims=None, nfiles=None):
    filelist = prep_file_input(files)

    bknd = Backend(file_type, axes_lims, as_series=True)

    ods = bknd.parse_data(filelist[:nfiles])

    return ods


@stopwatch
def open_compare(file_types, path=os.getcwd(), runs="*", quants="*", axes_lims=None):
    # Make sure file_type is a list
    if isinstance(file_types, str):
        file_types = [file_types]

    path = prep_file_input(path)[0]

    # Search for run folders

    print(f"\nScanning directory:\n {path}")
    dirs_runs = find_runs(path, runs)
    print(f"Found {len(dirs_runs)} run(s):")
    [print_file_item(item) for item in dirs_runs.keys()]

    # Search for quantities and read data

    bknds = [Backend(ftype, axes_lims) for ftype in file_types]
    for bk in bknds:
        files_quants = bk._load_quant_files(path, dirs_runs, quants)
        print(f"\nFound {len(files_quants)} quantities with '{bk.name}' backend:")
        (print_file_item(item) for item in files_quants.keys())

    # Read all data

    df = pd.DataFrame()

    for run, run_dir in dirs_runs.items():
        for bk in bknds:
            for quant, quant_files in bk._quant_files.items():
                filepaths = get_abs_filepaths(path, run_dir, quant_files)
                ods = bk.parse_data(filepaths, axes_lims=axes_lims, quant_name=quant)
                ods.attrs["run"] = run

                if quant not in df.columns:
                    df[quant] = pd.Series(dtype=object)
                if run not in df.index:
                    df.loc[run] = pd.Series(dtype=object)
                df.at[run, quant] = ods

    print("\nDone!")

    return df
