import os
from functools import wraps

import pandas as pd
import xarray as xr

from .backend import Backend
from .utils import (
    find_runs,
    get_abs_filepaths,
    prep_file_input,
    print_file_item,
    stopwatch,
)

# -----------------------------------------------------------------------
# Wrapper around xarray functions
# -----------------------------------------------------------------------

# TODO: add custom merge, concat, etc functions that are careful with mixing data_origin and pic_data_type


def ozzy_wrapper(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)

        # # Maintain class of input objects

        # for arg in args:
        #     if any([isinstance(arg, itertype) for itertype in [list, tuple, dict]]):
        #         for obj in arg:
        #             if isinstance(obj, xr.Dataset):
        #                 break
        #         else:
        #             for obj in kwargs.values():
        #                 if isinstance(obj, xr.Dataset):
        #                     break
        #             else:
        #                 continue
        #         break

        # if isinstance(obj, xr.Dataset):
        #     ClassIn = type(obj)
        # else:
        #     ClassIn = OzzyDatasetBase  # dataset_cls_factory()

        # if type(result) is tuple:
        #     for res in result:
        #         res = (
        #             ClassIn(res)
        #             if isinstance(res, xr.Dataset) | isinstance(res, xr.DataArray)
        #             else res
        #         )
        # else:
        #     if isinstance(result, xr.Dataset) | isinstance(result, xr.DataArray):
        #         result = ClassIn(result)
        return result

    return wrapped


for name, item in xr.__dict__.items():
    if callable(item) & ~isinstance(item, type) & ~name.startswith("__"):
        exec(f"{name} = ozzy_wrapper(item)")


# -----------------------------------------------------------------------
# Core functions
# -----------------------------------------------------------------------


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
                df.at[run, quant] = ods

    print("\nDone!")

    return
