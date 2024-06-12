# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

"""
This submodule provides utility functions for other parts of ozzy, from simple formatting operations to more complicated file-finding tasks.
"""

import functools
import glob
import os
import re
import time
from datetime import timedelta
from pathlib import PurePath

import h5py
import numpy as np

# Decorators


def stopwatch(method):
    """
    Decorator function to measure the execution time of a method.

    Parameters
    ----------
    method : callable
        The method to be timed.

    Returns
    -------
    timed : callable
        A wrapped version of the input method that prints the execution time.

    Examples
    --------

    ???+ example "Get execution time whenever a function is called"

        ```python
        from ozzy.utils import stopwatch

        @stopwatch
        def my_function(a, b):
            return a + b

        my_function(2, 3)
        # -> 'my_function' took: 0:00:00.000001
        # 5
        ```

    """

    @functools.wraps(method)
    def timed(*args, **kw):
        ts = time.perf_counter()
        result = method(*args, **kw)
        te = time.perf_counter()
        duration = timedelta(seconds=te - ts)
        print(f"    -> '{method.__name__}' took: {duration}")
        return result

    return timed


# Consistent output


def print_file_item(file: str) -> None:
    """
    Print a file name with a leading '  - '.

    Parameters
    ----------
    file : str
        The file name to be printed.

    Examples
    --------

    ???+ example

        ```python
        import ozzy as oz
        oz.utils.print_file_item('example.txt')
        # - example.txt
        ```

    """
    print("  - " + file)


# String manipulation


def unpack_str(attr):
    """
    Unpack a string from a NumPy ndarray or return the input as is.

    !!! note
        This function is useful when reading attributes from HDF5 files, since strings are often wrapped in NumPy arrays when using [h5py](https://www.h5py.org/) to read these files.

    Parameters
    ----------
    attr : numpy.ndarray or object
        The input array or object.

    Returns
    -------
    result : str or object
        The unpacked string or the original input object.

    Examples
    --------

    ???+ example
        ```python
        import ozzy as oz
        import numpy as np
        oz.utils.unpack_str(np.array(['hello']))
        # 'hello'
        oz.utils.unpack_str('world')
        # 'world'
        ```
    """
    if isinstance(attr, np.ndarray):
        match len(attr.shape):
            case 0:
                result = str(attr)
            case 1:
                result = attr[0]
            case 2:
                result = attr[0, 0]
    else:
        result = attr
    return result


def tex_format(str: str) -> str:
    r"""
    Format a string for TeX by enclosing it with '$' symbols.

    Parameters
    ----------
    str : str
        The input string.

    Returns
    -------
    newstr : str
        The TeX-formatted string.

    Examples
    --------

    ???+ example

        ```python
        import ozzy as oz
        oz.utils.tex_format('k_p^2')
        # '$k_p^2$'
        oz.utils.tex_format('')
        # ''
        ```
    """
    if str == "":
        newstr = str
    else:
        newstr = "$" + str + "$"
    return newstr


def get_regex_snippet(pattern: str, string: str) -> str:
    r"""
    Extract a regex pattern from a string using [re.search()](https://docs.python.org/3/library/re.html#re.search).

    !!! tip
        Use [regex101.com](https://regex101.com/) to experiment with and debug regular expressions.

    Parameters
    ----------
    pattern : str
        The regular expression pattern.
    string : str
        The input string.

    Returns
    -------
    match : str
        The matched substring.

    Examples
    --------

    ???+ example "Get number from file name"

        ```python
        import ozzy as oz
        oz.utils.get_regex_snippet(r'\d+', 'field-001234.h5')
        # '001234'
        ```
    """
    return re.search(pattern, string).group(0)


# Class manipulation


def get_user_methods(clss: type) -> list[str]:
    """
    Get a list of user-defined methods in a class.

    Parameters
    ----------
    clss : class
        The input class.

    Returns
    -------
    methods : list of str
        A list of user-defined method names in the class.

    Examples
    --------

    ???+ example "Minimal class"

        ```python
        class MyClass:
            def __init__(self):
                pass
            def my_method(self):
                pass

        import ozzy as oz
        oz.utils.get_user_methods(MyClass)
        # ['my_method']
        ```
    """
    return [
        func
        for func in dir(clss)
        if callable(getattr(clss, func))
        and (func in clss.__dict__)
        and (~func.startswith("__"))
    ]


# I/O


def prep_file_input(files: str | list[str]) -> list[str]:
    """
    Prepare path input argument by expanding user paths and converting to absolute paths.

    Parameters
    ----------
    files : str or list of str
        The input file(s).

    Returns
    -------
    filelist : list of str
        A list of absolute file paths.

    Examples
    --------

    ???+ example "Expand user folder"

        ```python
        import ozzy as oz
        oz.utils.prep_file_input('~/example.txt')
        # ['/home/user/example.txt']
        oz.utils.prep_file_input(['~/file1.txt', '~/file2.txt'])
        # ['/home/user/file1.txt', '/home/user/file2.txt']
        ```
    """
    if isinstance(files, str):
        filelist = [os.path.abspath(os.path.expanduser(files))]
    else:
        filelist = [os.path.abspath(os.path.expanduser(f)) for f in files]
    return filelist


def force_str_to_list(var):
    """
    Convert a string to a list containing the string.

    Parameters
    ----------
    var : str or object
        The input variable.

    Returns
    -------
    var : list
        A list containing the input variable if it was a string, or the original object.

    Examples
    --------

    ???+ example

        ```python
        import ozzy as oz
        oz.utils.force_str_to_list('hello')
        # ['hello']
        oz.utils.force_str_to_list([1, 2, 3])
        # [1, 2, 3]
        ```
    """
    if isinstance(var, str):
        var = [var]
    return var


def get_abs_filepaths(path: str, run_dir: str, quant_files: list[str]) -> list[str]:
    """
    Get absolute file paths of data files (simulation quantities) in a run directory.

    Parameters
    ----------
    path : str
        The base path.
    run_dir : str
        The run directory name.
    quant_files : list of str
        The file names (quantity names).

    Returns
    -------
    filepaths_to_read : list of str
        A list of absolute file paths for the data files.

    Examples
    --------

    ???+ example "Simulation data organized in subfolders"

        ```python
        import ozzy as oz
        oz.utils.get_abs_filepaths('/path/to/data', 'run1', ['e1-000000.h5','e1-000001.h5'])
        # ['/path/to/data/run1/MS/FLD/e1/e1-000000.h5', '/path/to/data/run1/MS/FLD/e1/e1-000001.h5']
        ```
    """
    filepaths_to_read = []
    for file in quant_files:
        fileloc = glob.glob(
            "**/" + file, recursive=True, root_dir=os.path.join(path, run_dir)
        )
        fullloc = [os.path.join(path, run_dir, loc) for loc in fileloc]
        filepaths_to_read = filepaths_to_read + fullloc
    return filepaths_to_read


def find_runs(path: str, runs_pattern: str | list[str]) -> dict[str, str]:
    """
    Find run directories matching a [glob](https://en.wikipedia.org/wiki/Glob_(programming)) pattern.

    Parameters
    ----------
    path : str
        The base path.
    runs_pattern : str or list of str
        The run directory name or [glob](https://en.wikipedia.org/wiki/Glob_(programming)) pattern(s).

    Returns
    -------
    dirs_dict : dict
        A dictionary mapping run names to their relative directory paths.

    Examples
    --------

    ???+ example "Finding set of run folders"

        Let's say we have a set of simulations that pick up from different checkpoints of a baseline simulation, with the following folder tree:

        ```
        .
        └── all_simulations/
            ├── baseline/
            │   ├── data.h5
            │   ├── checkpoint_t_00200.h5
            │   ├── checkpoint_t_00400.h5
            │   ├── checkpoint_t_00600.h5
            │   └── ...
            ├── from_t_00200/
            │   └── data.h5
            ├── from_t_00400/
            │   └── data.h5
            ├── from_t_00600/
            │   └── data.h5
            ├── ...
            └── other_simulation
        ```

        To get the directories of each subfolder, we could use either
        ```python
        import ozzy as oz
        run_dirs = oz.utils.find_runs(path = "all_simulations", runs_pattern = "from_t_*")
        print(run_dirs)
        # {'from_t_00200': 'from_t_00200', 'from_t_00400': 'from_t_00400', ...}
        ```
        or
        ```python
        import ozzy as oz
        run_dirs = oz.utils.find_runs(path = ".", runs_pattern = "all_simulations/from_t_*")
        print(run_dirs)
        # {'from_t_00200': 'all_simulations/from_t_00200', 'from_t_00400': 'all_simulations/from_t_00400', ...}
        ```

        Note that this function does not work recursively, though it still returns the current directory if no run folders are found:
        ```python
        import ozzy as oz
        run_dirs = oz.utils.find_runs(path = ".", runs_pattern = "from_t_*")
        # Could not find any run folder:
        # - Checking whether already inside folder...
        #     ...no
        # - Proceeding without a run name.
        print(run_dirs)
        # {'undefined': '.'}
        ```

    """
    dirs = []
    run_names = []

    runs_list = force_str_to_list(runs_pattern)

    # Try to find directories matching runs_pattern

    for run in runs_list:
        filesindir = sorted(glob.glob(run, root_dir=path))
        dirs = dirs + [
            os.path.abspath(os.path.join(path, folder))
            for folder in filesindir
            if os.path.isdir(os.path.join(path, folder))
        ]

    run_names = [PurePath(rdir).parts[-1] for rdir in dirs]

    # In case no run folders are found

    if len(run_names) == 0:
        print("Could not find any run folder:")
        print(" - Checking whether already inside folder... ")
        # Check whether already inside run folder
        folder = PurePath(os.path.abspath(path)).parts[-1]
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


def check_h5_availability(path: str) -> None:
    """
    Check if an HDF5 file can be opened for writing.

    !!! note
        This method is useful for longer analysis operations that save a file at the end. Without checking the output file writeability at the beginning, there is the risk of undergoing the lengthy processing and then failing to write the result to a file at the end.

    Parameters
    ----------
    path : str
        The path to the HDF5 file.

    Raises
    ------
    FileNotFoundError
        If the file is not found.
    BlockingIOError
        If the file is in use and cannot be overwritten.
    OSError
        If there is another issue with the file.

    Examples
    --------

    ???+ example "Writing a custom analysis function"

        ```python
        import ozzy as oz

        def my_analysis(ds, output_file='output.h5'):

            # Check whether output file is writeable
            oz.utils.check_h5_availability(output_file)

            # Perform lengthy analysis
            # ...
            new_ds = 10 * ds

            # Save result
            new_ds.ozzy.save(output_file)

            return

        ```
    """
    try:
        with h5py.File(path, "a") as _:
            pass
    except FileNotFoundError:
        raise FileNotFoundError("File not found.")
    except BlockingIOError:
        raise BlockingIOError(
            "Output file is in use and cannot be overwritten. Make sure the file is not open in a different application or change the output file name."
        )
    except OSError:
        raise OSError(
            "Output file may be in use or there may be another issue. Make sure the file is not open in a different application or change the output file name."
        )


# Data manipulation


def axis_from_extent(nx: int, lims: tuple[float, float]) -> np.ndarray:
    """
    Create a numerical axis from the number of cells and extent limits. The axis values are centered with respect to each cell.

    Parameters
    ----------
    nx : int
        The number of cells in the axis.
    lims : tuple of float
        The extent limits (min, max).

    Returns
    -------
    ax : numpy.ndarray
        The numerical axis.

    Raises
    ------
    ZeroDivisionError
        If the number of cells is zero.
    TypeError
        If the second element of `lims` is not larger than the first element.

    Examples
    --------

    ???+ example "Simple axis"

        ```python
        import ozzy as oz
        axis = oz.utils.axis_from_extent(10, (0,1))
        axis
        # array([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95])
        ```
        Note how the axis values correspond to the center of each cell.

    """
    if nx == 0:
        raise ZeroDivisionError("Number of cells in axis cannot be zero.")
    if lims[1] <= lims[0]:
        raise TypeError("Second elements of 'lims' must be larger than first element.")
    dx = (lims[1] - lims[0]) / nx
    ax = np.linspace(lims[0], lims[1] - dx, num=nx) + 0.5 * dx
    return ax


def bins_from_axis(axis: np.ndarray) -> np.ndarray:
    """
    Create bin edges from a numerical axis. This is useful for binning operations that require the bin edges.

    Parameters
    ----------
    axis : numpy.ndarray
        The numerical axis.

    Returns
    -------
    binaxis : numpy.ndarray
        The bin edges.

    Examples
    --------

    ???+ example "Bin edges from simple axis"

        First we create a simple axis with the [axis_from_extent()][ozzy.utils.axis_from_extent] function:

        ```python
        import ozzy as oz
        axis = oz.utils.axis_from_extent(10, (0,1))
        print(axis)
        # [0.05 0.15 0.25 0.35 0.45 0.55 0.65 0.75 0.85 0.95]
        ```
        Now we get the bin edges:

        ```python
        bedges = oz.utils.bins_from_axis(axis)
        bedges
        # array([-6.9388939e-18,  1.0000000e-01,  2.0000000e-01,  3.0000000e-01, 4.0000000e-01,  5.0000000e-01,  6.0000000e-01,  7.0000000e-01, 8.0000000e-01,  9.0000000e-01,  1.0000000e+00])
        ```

        (In this example there is some rounding error for the zero edge.)
    """
    vmin = axis[0] - 0.5 * (axis[1] - axis[0])
    binaxis = axis + 0.5 * (axis[1] - axis[0])
    binaxis = np.insert(binaxis, 0, vmin)
    return binaxis
