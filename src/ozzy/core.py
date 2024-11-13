# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

"""
Core functions of the ozzy library.

This module contains the main entry points for working with ozzy, including
functions to create new [DataArray][xarray.DataArray] and [Dataset][xarray.Dataset] objects, and to open data files of various types.

The `open()` function is the primary way to load data into ozzy, and supports
a variety of file types. The `open_series()` function can be used to load a
series of files, and `open_compare()` can be used to compare data across
multiple file types and runs.

"""

import os

import dask
import pandas as pd
import xarray as xr

# from .accessors import *  # noqa: F403
from . import accessors  # noqa
from .backend_interface import Backend, _list_avail_backends
from .new_dataobj import new_dataarray, new_dataset
from .utils import (
    find_runs,
    path_list_to_pars,
    prep_file_input,
    print_file_item,
    recursive_search_for_file,
    stopwatch,
)


def Dataset(
    *args,
    pic_data_type: str | list[str] | None = None,
    data_origin: str | list[str] | None = None,
    **kwargs,
) -> xr.Dataset:
    """
    Create a new [Dataset][xarray.Dataset] object with added ozzy functionality. See [xarray.Dataset][] for more information on `*args` and `**kwargs`.

    !!! warning

        This function should be used instead of `xarray.Dataset()` to create a new Dataset object, since it sets attributes that enable access to ozzy-specific methods.

    Parameters
    ----------
    *args
        Positional arguments passed to [xarray.Dataset][].
    pic_data_type : str | list[str] | None, optional
        Type of data contained in the Dataset. Current options: `'grid'` (data defined on an n-dimensional grid, as a function of some coordinate(s)), or `'part'` (data defined on a particle-by-particle basis). If given, this overwrites the corresponding attribute in any data objects passed as positional arguments (*args).
    data_origin : str | list[str] | None, optional
         Type of simulation data. Current options: `'ozzy'`, `'osiris'`, or `'lcode'`.
    **kwargs
        Keyword arguments passed to [xarray.Dataset][].

    Returns
    -------
    xarray.Dataset
        The newly created Dataset object.

    Examples
    --------
    ???+ example "Empty Dataset"

        ```python
        import ozzy as oz
        ds = oz.Dataset()
        ds
        # <xarray.Dataset> Size: 0B
        # Dimensions:  ()
        # Data variables:
        #     *empty*
        # Attributes:
        #     pic_data_type:  None
        #     data_origin:    None
        ```

    ???+ example "Dummy Dataset"

        ```python
        import ozzy as oz
        import numpy as np
        ds = oz.Dataset({'var1': (['t','x'], np.random.rand(10,30))}, coords={'x': np.linspace(-5,0,30)}, pic_data_type='grid', data_origin='ozzy')
        ds
        # <xarray.Dataset> Size: 3kB
        # Dimensions:  (t: 10, x: 30)
        # Coordinates:
        # * x        (x) float64 240B -5.0 -4.828 -4.655 -4.483 ... -0.3448 -0.1724 0.0
        # Dimensions without coordinates: t
        # Data variables:
        #     var1     (t, x) float64 2kB 0.9172 0.3752 0.1873 ... 0.5211 0.8016 0.335
        # Attributes:
        #     pic_data_type:  grid
        #     data_origin:    ozzy
        ```
    """
    return new_dataset(
        *args, pic_data_type=pic_data_type, data_origin=data_origin, **kwargs
    )


def DataArray(
    *args,
    pic_data_type: str | list[str] | None = None,
    data_origin: str | list[str] | None = None,
    **kwargs,
):
    """
    Create a new [DataArray][xarray.DataArray] object with added Ozzy functionality. See [xarray.DataArray][] for more information on `*args` and `**kwargs`.

    !!! warning

        This function should be used instead of `xarray.DataArray()` to create a new DataArray object, since it sets attributes that enable access to ozzy-specific methods.

    Parameters
    ----------
    *args
        Positional arguments passed to [xarray.DataArray][].
    pic_data_type : str | None, optional
        Type of data in the DataArray. Current options: `'grid'` (data defined on an n-dimensional grid, as a function of some coordinate(s)), or `'part'` (data defined on a particle-by-particle basis). If given, this overwrites the corresponding attribute in any data objects passed as positional arguments (*args).
    data_origin : str | None, optional
         Type of simulation data. Current options: `'ozzy'`, `'osiris'`, or `'lcode'`.
    **kwargs
        Keyword arguments passed to [xarray.DataArray][].

    Returns
    -------
    xarray.DataArray
        The newly created DataArray object.

    Examples
    --------
    ???+ example "Empty DataArray"

        ```python
        import ozzy as oz
        da = oz.DataArray()
        print(da)
        # <xarray.DataArray ()> Size: 8B
        # array(nan)
        # Attributes:
        #     pic_data_type:  None
        #     data_origin:    None
        da.size, da.shape
        # (1, ())
        ```

        A DataArray cannot be empty, so it is initialized as a NaN variable (zero array dimensions).

    ???+ example "Dummy DataArray"

        ```python
        import ozzy as oz
        import numpy as np
        da = oz.DataArray(np.random.rand(10,30), dims=['t','x'], coords={'x': np.linspace(-5,0,30)}, name='var1', pic_data_type='grid', data_origin='ozzy')
        da
        # <xarray.DataArray 'var1' (t: 10, x: 30)> Size: 2kB
        # array([[0.64317574, 0.24791049, 0.54208619, 0.27064002, 0.65152958,
        # ...
        #         0.28523593, 0.76475677, 0.86068012, 0.03214018, 0.55055121]])
        # Coordinates:
        # * x        (x) float64 240B -5.0 -4.828 -4.655 -4.483 ... -0.3448 -0.1724 0.0
        # Dimensions without coordinates: t
        # Attributes:
        #     pic_data_type:  grid
        #     data_origin:    ozzy
        ```
    """
    return new_dataarray(
        *args, pic_data_type=pic_data_type, data_origin=data_origin, **kwargs
    )


def available_backends():
    """List available backend options for reading simulation data.

    Returns
    -------
    list[str]
        Available backend names.

    Examples
    --------
    ???+ example "Show available file backends"

        ```python
        import ozzy as oz
        backends = oz.available_backends()
        print(backends)
        # ['osiris', 'lcode', 'ozzy']
        ```
    """
    return _list_avail_backends()


@stopwatch
def open(
    file_type: str,
    path: str | list[str],
    axes_lims: dict[str, tuple[float, float]] | None = None,
    **kwargs,
) -> xr.Dataset | xr.DataArray:
    """
    Open a data file and return a data object ([DataArray][xarray.DataArray] or [Dataset][xarray.Dataset]).

    Parameters
    ----------
    file_type : str
        The type of data file to open. Current options: `'ozzy'`, `'osiris'`, or `'lcode'`.
    path : str | list[str]
        The path to the data file(s) to open. Can be a single path or a list of paths. Paths can be absolute or relative, but cannot contain wildcards or glob patterns.
    **kwargs :
        Additional keyword arguments to be passed to the backend-specific reader function.

        See available keyword arguments for each backend:

        * [LCODE][ozzy.backends.lcode_backend.read]
        * [OSIRIS][ozzy.backends.osiris_backend.read]
        * [ozzy][ozzy.backends.ozzy_backend.read]

    Returns
    -------
    xarray.Dataset | xarray.DataArray
        The Ozzy data object containing the data from the opened file(s).


    Examples
    --------

    ???+ example "Read Osiris field data"

        ```python
        import ozzy as oz
        ds = oz.open('osiris', 'path/to/file/e1-000020.h5')
        ```

    ???+ example "Read LCODE field data"

        LCODE simulation files do not contain any axis information, so we must supply the simulation window size in order to define the axis coordinates (this is optional).

        ```python
        import ozzy as oz
        ds = oz.open('lcode', 'path/to/file/ez02500.swp', axes_lims = {'x1': (-100,0.0), 'x2': (0.0, 6.0)})
        ```

    """
    filelist = prep_file_input(path)

    if len(filelist) > 1:
        print(
            "\nWARNING: Found multiple files matching path. Reading only the first file in list.\n"
        )
        filelist = filelist[0]

    # initialize the backend object (it deals with the error handling)
    bknd = Backend(file_type, as_series=False)

    ods = bknd.parse_data(filelist, axes_lims=axes_lims, **kwargs)

    return ods


@stopwatch
def open_series(file_type, files, nfiles=None, **kwargs):
    """
    Open a series of data files and return a data object ([DataArray][xarray.DataArray] or [Dataset][xarray.Dataset]).

    Parameters
    ----------
    file_type : str
        The type of data files to open (currently: `'ozzy'`, `'osiris'`, or `'lcode'`).
    files : str | list
        The path(s) to the data file(s) to open. Can be a single path or a list of paths. Paths can be absolute or relative, but cannot contain wildcards or glob patterns.
    nfiles : int, optional
        The maximum number of files to open. If not provided, all files will be opened.
    **kwargs :
        Additional keyword arguments to be passed to the backend-specific reader function.

        See available keyword arguments for each backend:

        * [LCODE][ozzy.backends.lcode_backend.read]
        * [OSIRIS][ozzy.backends.osiris_backend.read]
        * [ozzy][ozzy.backends.ozzy_backend.read]

    Returns
    -------
    xarray.DataArray | xarray.Dataset
        The Ozzy data object containing the data from the opened file(s).


    Examples
    --------

    ???+ example "Open time series of data"

        Let's say we are located in the following directory, which contains a time series of ozzy data in HDF5 format:
        ```text
        .
        └── my_data/
            ├── Ez_0001.h5
            ├── Ez_0002.h5
            ├── Ez_0003.h5
            ├── ...
            └── Ez_0050.h5
        ```

        We want to open only the first three files.

        ```python
        import ozzy as oz
        ds = oz.open_series('ozzy', 'my_data/Ez_*.h5', nfiles=3)
        ```
        The three files have been put together in a single dataset with a new time dimension.

    """
    filelist = prep_file_input(files)
    bknd = Backend(file_type, as_series=True)
    common_dir, dirs_runs, quants = path_list_to_pars(filelist)

    quant_files = bknd._load_quant_files(
        path=common_dir, dirs_runs=dirs_runs, quants=quants
    )

    ds = []
    for run, run_dir in dirs_runs.items():
        for quant, quant_files in bknd._quant_files.items():
            filepaths = [os.path.join(run_dir, qfile) for qfile in quant_files]
            ds.append(bknd.parse_data(filepaths[:nfiles], **kwargs))

    with dask.config.set({"array.slicing.split_large_chunks": True}):
        ods = xr.merge(ds)

    return ods


# HACK: maybe it's more correct to hide backend-specific arguments such as "axes_lims" in the general open functions, and simply pass everything on as **kwargs. The only downside is that these arguments will not show up in the documentation other than as an intentional note. But the Backend class and everything downstream should not have to know what each different backend module requires as extra parameters, which is the current status.


@stopwatch
def open_compare(
    file_types: str | list[str],
    path: str = os.getcwd(),
    runs: str | list[str] = "*",
    quants: str | list[str] = "*",
    **kwargs,
) -> pd.DataFrame:
    """
    Open and compare data files of different types and from different runs.

    Parameters
    ----------
    file_types : str | list[str]
        The type(s) of data files to open. Current options are: `'ozzy'`, `'osiris'`, or `'lcode'`.
    path : str, optional
        The path to the directory containing the run folders. Default is the current working directory.
    runs : str | list[str], optional
        A string or [glob](https://en.wikipedia.org/wiki/Glob_(programming)) pattern to match the run folder names. Default is '*' to match all folders.
    quants : str | list[str], optional
        A string or [glob](https://en.wikipedia.org/wiki/Glob_(programming)) pattern to match the quantity names. Default is '*' to match all quantities.
    **kwargs :
        Additional keyword arguments to be passed to the backend-specific reader function.

        See available keyword arguments for each backend:

        * [LCODE][ozzy.backends.lcode_backend.read]
        * [OSIRIS][ozzy.backends.osiris_backend.read]
        * [ozzy][ozzy.backends.ozzy_backend.read]

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the data objects for each run and quantity, with runs as rows and quantities as columns.

    Examples
    --------

    ???+ example "Opening files across different folders"

        Let's say we have the following directory:
        ```text
        .
        └── parameter_scans/
            ├── run_a/
            │   ├── e1-000000.h5
            │   ├── e1-000001.h5
            │   ├── e1-000002.h5
            │   ├── ...
            │   └── e1-000100.h5
            ├── run_b/
            │   ├── e1-000000.h5
            │   ├── e1-000001.h5
            │   ├── e1-000002.h5
            │   ├── ...
            │   └── e1-000100.h5
            └── test_run/
                └── ...
        ```

        We want to compare the simulations results for the longitudinal field from two different simulations, `run_a` and `run_b`.

        ```python
        import ozzy as oz
        df = oz.open_compare('osiris', path='parameter_scans', runs='run_*', quants='e1')
        df
        ```
        This function returns a [pandas.DataFrame][]. Each dataset can be accessed with a standard Pandas lookup method like [`.at`][pandas.DataFrame.at]/[`.iat`][pandas.DataFrame.iat] or [`.loc`][pandas.DataFrame.loc]/[`.iloc`][pandas.DataFrame.iloc]:
        ```python
        ds = df.at['run_b', 'e1']
        ```

    ???+ example "Opening files with two different backends"

        Let's say we have the following directory:
        ```text
        /MySimulations/
        ├── OSIRIS/
        │   └── my_sim_1/
        │       └── MS/
        │           └── DENSITY/
        │               └── electrons/
        │                   └── charge/
        │                       ├── charge-electrons-000000.h5
        │                       ├── charge-electrons-000001.h5
        │                       ├── charge-electrons-000002.h5
        │                       └── ...
        └── LCODE/
            └── my_sim_2/
                ├── ez00200.swp
                ├── ez00400.swp
                ├── ez00600.swp
                └── ...
        ```
        We can read two quantities produced by two different simulation codes:

        ```python
        import ozzy as oz
        df = oz.open_compare(
            ["osiris", "lcode"],
            path='/MySimulations',
            runs=["OSIRIS/my_sim_1", "LCODE/my_sim_2"],
            quants=["charge", "ez"],
        )
        # ...
        print(df)
        #                   charge-electrons    ez
        # OSIRIS/my_sim_1           [charge]    []
        # LCODE/my_sim_2                  []  [ez]
        ```
    """

    # Make sure file_type is a list
    if isinstance(file_types, str):
        file_types = [file_types]

    path = prep_file_input(path)[0]

    # Search for run folders

    print(f"\nScanning directory:\n {path}")
    dirs_runs = find_runs(path, runs)
    print(f"\nFound {len(dirs_runs)} run(s):")
    [print_file_item(item) for item in dirs_runs.keys()]

    # Search for quantities and read data

    bknds = [Backend(ftype) for ftype in file_types]
    for bk in bknds:
        files_quants = bk._load_quant_files(path, dirs_runs, quants)
        print(f"Found {len(files_quants)} quantities with '{bk.name}' backend:")
        [print_file_item(item) for item in files_quants.keys()]

    # Read all data

    df = pd.DataFrame()

    for run, run_dir in dirs_runs.items():
        for bk in bknds:
            for quant, quant_files in bk._quant_files.items():
                # Get absolute paths to files that should be read
                rel_filepaths = []
                for qfile in quant_files:
                    query = recursive_search_for_file(qfile, run_dir)
                    rel_filepaths = rel_filepaths + query
                filepaths = [
                    os.path.join(run_dir, relfile) for relfile in rel_filepaths
                ]

                # Read found files
                ods = bk.parse_data(filepaths, **kwargs)
                ods.attrs["run"] = run

                if quant not in df.columns:
                    df[quant] = pd.Series(dtype=object)
                if run not in df.index:
                    df.loc[run] = pd.Series(dtype=object)
                df.at[run, quant] = ods

    print("\nDone!")

    return df
