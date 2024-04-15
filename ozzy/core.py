"""
Core functions for the Ozzy library.

This module contains the main entry points for working with Ozzy, including
functions to create new DataArray and Dataset objects, and to open data files
of various types.

The `open()` function is the primary way to load data into Ozzy, and supports
a variety of file types. The `open_series()` function can be used to load a
series of files, and `open_compare()` can be used to compare data across
multiple file types and runs.

These functions handle the low-level details of parsing the data files and
creating the appropriate Ozzy data objects.
"""

import os

import pandas as pd
import xarray as xr

from .backend import Backend
from .new_dataobj import new_dataarray, new_dataset
from .ozzy_accessor import *  # noqa: F403
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

# TODO: add progress bars
# TODO: add examples to docstrings


def Dataset(
    pic_data_type: str | list[str] | None = None,
    data_origin: str | list[str] | None = None,
    *args,
    **kwargs,
) -> xr.Dataset:
    """
    Create a new [xarray.Dataset][] object with added Ozzy functionality.

    !!! info

        This function should be used instead of `xarray.Dataset()` to create a new Dataset object, since it sets attributes that enable access to Ozzy-specific methods.

    Parameters
    ----------
    pic_data_type : str | list[str] | None, optional
        Type of data contained in the Dataset. Current options: `'grid'` (data defined on an n-dimensional grid, as a function of some coordinate(s)), or `'part'` (data defined on a particle-by-particle basis).
    data_origin : str | list[str] | None, optional
         Type of simulation data. Current options: `'ozzy'`, `'osiris'`, or `'lcode'`.
    *args
        Positional arguments passed to [xarray.Dataset][].
    **kwargs
        Keyword arguments passed to [xarray.Dataset][].

    Returns
    -------
    xarray.Dataset
        The newly created Dataset object.

    Examples
    --------
    ??? example "Example 1"

        ```python
        >>> This is an example
        3
        ```

        And this is some explaining
    """
    return new_dataset(*args, **kwargs)


def DataArray(
    pic_data_type: str | list[str] | None = None,
    data_origin: str | list[str] | None = None,
    *args,
    **kwargs,
):
    """
    Create a new [xarray.DataArray][] object with added Ozzy functionality.

    !!! info

        This function should be used instead of `xarray.DataArray()` to create a new DataArray object, since it sets attributes that enable access to Ozzy-specific methods.

    Parameters
    ----------
    pic_data_type : str | None, optional
        Type of data in the DataArray. Current options: `'grid'` (data defined on an n-dimensional grid, as a function of some coordinate(s)), or `'part'` (data defined on a particle-by-particle basis).
    data_origin : str | None, optional
         Type of simulation data. Current options: `'ozzy'`, `'osiris'`, or `'lcode'`.
    *args
        Positional arguments passed to [xarray.DataArray][].
    **kwargs
        Keyword arguments passed to [xarray.DataArray][].

    Returns
    -------
    xarray.DataArray
        The newly created DataArray object.

    Examples
    --------
    ??? example "Example 1"

        ```python
        >>> This is an example
        3
        ```

        And this is some explaining
    """
    return new_dataarray(*args, **kwargs)


@stopwatch
def open(
    file_type: str,
    path: str | list[str],
    axes_lims: dict[str, tuple[float, float]] | None = None,
) -> xr.Dataset | xr.DataArray:
    """
    !!! warning

        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla et euismod
        nulla. Curabitur feugiat, tortor non consequat finibus, justo purus auctor
        massa, nec semper lorem quam in massa.

    Open a data file and return an Ozzy data object. Here is a footnote [^1].

    [^1]: Here is my footnote.

    Parameters
    ----------
    file_type : str
        The type of data file to open. Current options: `'ozzy'`, `'osiris'`, or `'lcode'`.
    path : str | list[str]
        The path to the data file(s) to open. Can be a single path or a list of paths. Paths can be absolute or relative, but cannot contain wildcards or glob patterns.
    axes_lims : dict[str, tuple[float, float]] | None, optional
        A dictionary specifying the limits for each axis in the data (only used for `'lcode'` data type, optionally). Keys are axis names, and values are tuples of (min, max) values.

    Returns
    -------
    xarray.Dataset | xarray.DataArray
        The Ozzy data object containing the data from the opened file(s).


    Examples
    --------
    >>> np.add(1, 2)
    3

    Comment explaining the second example.

    >>> np.add([1, 2], [3, 4])
    array([4, 6])
    """
    filelist = prep_file_input(path)

    # initialize the backend object (it deals with the error handling)
    bknd = Backend(file_type, axes_lims, as_series=False)

    ods = bknd.parse_data(filelist)

    return ods


# TODO: check whether as_series parameter is even used by any backend
# TODO: check whether open_series is redundant
# TODO: check whether there is a better docstring format that makes default values clearer


@stopwatch
def open_series(file_type, files, axes_lims=None, nfiles=None):
    """
    Open a series of data files and return an Ozzy data object (xarray.DataArray or xarray.Dataset).

    Parameters:
        file_type (str): The type of data files to open (currently: `'ozzy'`, `'osiris'`, or `'lcode'`).
        files (str or list): The path(s) to the data file(s) to open. Can be a single
            path or a list of paths. Paths can be absolute or relative, but cannot contain wildcards or glob patterns.
        axes_lims (dict, optional): A dictionary specifying the limits for each
            axis in the data (only used for `'lcode'` data type, optionally). Keys are axis names, and values are tuples of (min, max) values.
        nfiles (int, optional): The maximum number of files to open. If not provided, all files will be opened.

    Returns:
        xarray.DataArray or xarray.Dataset: The Ozzy data object containing the data from the
            opened file(s).
    """
    filelist = prep_file_input(files)

    bknd = Backend(file_type, axes_lims, as_series=True)

    ods = bknd.parse_data(filelist[:nfiles])

    return ods


# TODO: check whether this really accepts a list of file_types
# TODO: check whether 'runs' and 'path' parameters also accept a list of strings


@stopwatch
def open_compare(
    file_types: str | list[str],
    path: str = os.getcwd(),
    runs: str = "*",
    quants: str = "*",
    axes_lims: dict[str, tuple[float, float]] | None = None,
) -> pd.DataFrame:
    """
    Open and compare data files of different types and from different runs.

    Parameters
    ----------
    file_types : str | list[str]
        The type(s) of data files to open. Current options are: `'ozzy'`, `'osiris'`, or `'lcode'`.
    path : str, optional
        The path to the directory containing the run folders. Default is the current working directory.
    runs : str, optional
        A string or pattern to match the run folder names. Default is '*' to match all folders.
    quants : str, optional
        A string or pattern to match the quantity names. Default is '*' to match all quantities.
    axes_lims : dict[str, tuple[float, float]] | None, optional
        A dictionary specifying the limits for each axis in the data (only used for `'lcode'` data type, optionally). Keys are axis names, and values are tuples of (min, max) values.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the data objects for each run and quantity, with runs as rows and quantities as columns.
    """

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
