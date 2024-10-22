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
from collections.abc import Callable, Iterable
from datetime import timedelta
from pathlib import PurePath

import h5py
import numpy as np
import xarray as xr

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


def unpack_attr(attr):
    """
    Unpack a NumPy array attribute, typically from HDF5 files.

    This function handles different shapes and data types of NumPy arrays,
    particularly focusing on string (byte string) attributes. It's useful
    for unpacking attributes read from HDF5 files using [h5py](https://www.h5py.org/).

    Parameters
    ----------
    attr : numpy.ndarray
        The input NumPy array to unpack.

    Returns
    -------
    object
        The unpacked attribute. For string attributes, it returns a UTF-8
        decoded string. For other types, it returns either a single element
        (if the array has only one element) or the entire array.

    Raises
    ------
    AssertionError
        If the input is not a NumPy array.

    Notes
    -----
    - For string attributes (`dtype.kind == 'S'`):
        - 0D arrays: returns the decoded string
        - 1D arrays: returns the first element decoded
        - 2D arrays: returns the first element if size is 1, otherwise the entire array
    - For non-string attributes:
        - If the array has only one element, returns that element
        - Otherwise, returns the entire array

    Examples
    --------
    ???+ example "Unpacking a string attribute"
        ```python
        import numpy as np
        import ozzy.utils as utils

        # Create a NumPy array with a byte string
        attr = np.array(b'Hello, World!')
        result = utils.unpack_attr(attr)
        print(result)
        # Output: Hello, World!
        ```

    ???+ example "Unpacking a numeric attribute"
        ```python
        import numpy as np
        import ozzy.utils as utils

        # Create a NumPy array with a single number
        attr = np.array([42])
        result = utils.unpack_attr(attr)
        print(result)
        # Output: 42
        ```
    """
    assert isinstance(attr, np.ndarray)

    if attr.dtype.kind == "S":
        match len(attr.shape):
            case 0:
                content = attr
            case 1:
                content = attr[0]
            case 2:
                if attr.size == 1:
                    content = attr[0, 0]
        out = content.decode("UTF-8")

    else:
        if len(attr) == 1:
            out = attr[0]
        else:
            out = attr

    return out


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
    Extract a regex pattern from a string using [`re.search`](https://docs.python.org/3/library/re.html#re.search).

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
    methods : list[str]
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
        and (not func.startswith("__"))
    ]


# I/O


def prep_file_input(files: str | list[str]) -> list[str]:
    """
    Prepare path input argument by expanding user paths and converting to absolute paths.

    Parameters
    ----------
    files : str | list of str
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
        globlist = glob.glob(os.path.expanduser(files), recursive=True)
        filelist = [os.path.abspath(f) for f in globlist]
    else:
        expandlist = [os.path.expanduser(f) for f in files]
        globlist = []
        for f in expandlist:
            globlist.append(glob.glob(f, recursive=True))

        filelist = []
        for f in globlist:
            try:
                os.path.abspath(f)
            except TypeError:
                pass
            else:
                filelist.append(os.path.abspath(f))

    if len(filelist) == 0:
        raise FileNotFoundError("No files were found")

    return filelist


def force_str_to_list(var):
    """
    Convert a string to a list containing the string.

    Parameters
    ----------
    var : str | object
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


def recursive_search_for_file(fname: str, path: str = os.getcwd()) -> list[str]:
    """
    Recursively search for files with a given name or pattern in a specified directory and its subdirectories.

    Parameters
    ----------
    fname : str
        The name or name pattern of the file to search for.
    path : str, optional
        The path to the directory where the search should start. If not specified, uses the current directory via [`os.getcwd`](https://docs.python.org/3/library/os.html#os.getcwd).

    Returns
    -------
    list[str]
        A list of paths to the files found, relative to `path`.

    Examples
    --------
    ???+ example "Search for a file in the current directory"
        ```python
        from ozzy.utils import recursive_search_for_file
        files = recursive_search_for_file('example.txt')
        # files = ['/path/to/current/dir/example.txt']
        ```

    ???+ example "Search for many files in a subdirectory"
        ```python
        from ozzy.utils import recursive_search_for_file
        files = recursive_search_for_file('data-*.h5', '/path/to/project')
        # files = ['data/data-000.h5', 'data/data-001.h5', 'analysis/data-modified.h5']
        ```
    """
    query = sorted(glob.glob("**/" + fname, recursive=True, root_dir=path))
    return query


def path_list_to_pars(pathlist: list[str]) -> tuple[str, dict[str, str], list[str]]:
    """
    Split a list of file paths into common directory, run directories, and quantities.

    Parameters
    ----------
    pathlist : list[str]
        A list of file paths.

    Returns
    -------
    common_dir : str
        The common directory shared by all file paths.
    dirs_runs : dict[str, str]
        A dictionary mapping run folder names to their absolute paths.
    quants : list[str]
        A list of unique quantities (file names) present in the input paths.

    Examples
    --------
    ???+ example "Simple example"
        ```python
        import os
        from ozzy.utils import path_list_to_pars

        pathlist = ['/path/to/run1/quantity1.txt',
                    '/path/to/run1/quantity2.txt',
                    '/path/to/run2/quantity1.txt']

        common_dir, dirs_runs, quants = path_list_to_pars(pathlist)

        print(f"Common directory: {common_dir}")
        # Common directory: /path/to
        print(f"Run directories: {dirs_runs}")
        # Run directories: {'run1': '/path/to/run1', 'run2': '/path/to/run2'}
        print(f"Quantities: {quants}")
        # Quantities: ['quantity2.txt', 'quantity1.txt']
        ```

    ???+ example "Single file path"
        ```python
        import os
        from ozzy.utils import path_list_to_pars

        pathlist = ['/path/to/run1/quantity.txt']

        common_dir, dirs_runs, quants = path_list_to_pars(pathlist)

        print(f"Common directory: {common_dir}")
        # Common directory: /path/to/run1
        print(f"Run directories: {dirs_runs}")
        # Run directories: {'.': '/path/to/run1'}
        print(f"Quantities: {quants}")
        # Quantities: ['quantity.txt']
        ```
    """
    filedirs = [os.path.dirname(file) for file in pathlist]
    quants = [os.path.basename(file) for file in pathlist]
    quants = list(set(quants))

    common_dir = os.path.commonpath(filedirs)
    dirs_runs = {os.path.relpath(filedir, common_dir): filedir for filedir in filedirs}
    return common_dir, dirs_runs, quants


def find_runs(path: str, runs_pattern: str | list[str]) -> dict[str, str]:
    """
    Find run directories matching a [glob](https://en.wikipedia.org/wiki/Glob_(programming)) pattern.

    Parameters
    ----------
    path : str
        The base path.
    runs_pattern : str | list[str]
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

    run_names = [os.path.relpath(rdir, os.path.commonpath(dirs)) for rdir in dirs]
    # run_names = [PurePath(rdir).parts[-1] for rdir in dirs]

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
    lims : tuple[float, float]
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

        First we create a simple axis with the [`axis_from_extent`][ozzy.utils.axis_from_extent] function:

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


# TODO: check examples in docstring
def set_attr_if_exists(
    da: xr.DataArray,
    attr: str,
    str_exists: str | Iterable[str] | Callable | None,
    str_doesnt: str | None = None,
):
    """
    Set or modify an attribute of a [DataArray][ozzy.core.DataArray] if it exists, or modify if it doesn't exist or is `None`.

    Parameters
    ----------
    da : xarray.DataArray
        The input DataArray.
    attr : str
        The name of the attribute to set or modify.
    str_exists : str | Iterable[str] | Callable | None, optional
        The value or function to use if the attribute exists.
        If `str`: replace the attribute with this string.
        If [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable): concatenate the first element, existing value, and second element.
        If [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable): apply this function to the existing attribute value.
        If `None`: do not change the attribute.
    str_doesnt : str | None, optional
        The value to set if the attribute doesn't exist. If `None`, no action is taken.

    Returns
    -------
    xarray.DataArray
        The modified DataArray with updated attributes.

    Notes
    -----
    If `str_exists` is an `Iterable` with more than two elements, only the first two are used,
    and a warning is printed.

    Examples
    --------
    ???+ example "Set an existing attribute"
        ```python
        import ozzy as oz
        import numpy as np

        # Create a sample DataArray
        da = oz.DataArray(np.random.rand(3, 3), attrs={'units': 'meters'})

        # Set an existing attribute
        da = set_attr_if_exists(da, 'units', 'kilometers')
        print(da.attrs['units'])
        # Output: kilometers
        ```

    ???+ example "Modify an existing attribute with a function"
        ```python
        import ozzy as oz
        import numpy as np

        # Create a sample DataArray
        da = oz.DataArray(np.random.rand(3, 3), attrs={'description': 'Random data'})

        # Modify an existing attribute with a function
        da = set_attr_if_exists(da, 'description', lambda x: x.upper())
        print(da.attrs['description'])
        # Output: RANDOM DATA
        ```

    ???+ example "Set a non-existing attribute"
        ```python
        import ozzy as oz
        import numpy as np

        # Create a sample DataArray
        da = oz.DataArray(np.random.rand(3, 3))

        # Set a non-existing attribute
        da = set_attr_if_exists(da, 'units', 'meters', str_doesnt='unknown')
        print(da.attrs['units'])
        # Output: unknown
        ```
    """
    if (attr in da.attrs) and (da.attrs[attr] is not None):
        if isinstance(str_exists, str):
            da.attrs[attr] = str_exists
        elif isinstance(str_exists, Iterable):
            if len(str_exists) > 2:
                print(
                    "     WARNING: str_exists argument in set_attr_if_exists has more than two elements. The original attribute is inserted between element 0 and element 1 of str_exists, other elements will be ignored."
                )
            da.attrs[attr] = str_exists[0] + da.attrs[attr] + str_exists[1]
        elif isinstance(str_exists, Callable):
            da.attrs[attr] = str_exists(da.attrs[attr])
        elif str_exists is None:
            return da
    else:
        if str_doesnt is not None:
            da.attrs[attr] = str_doesnt
    return da


# TODO: check examples in docstring
def get_attr_if_exists(
    da: xr.DataArray,
    attr: str,
    str_exists: str | Iterable[str] | Callable | None = None,
    str_doesnt: str | None = None,
):
    """
    Retrieve an attribute from a xarray DataArray if it exists, or return a specified value otherwise.

    Parameters
    ----------
    da : xarray.DataArray
        The xarray DataArray object to check for the attribute.
    attr : str
        The name of the attribute to retrieve.
    str_exists : str | Iterable[str] | Callable | None, optional
        The value or function to use if the attribute exists.
        If `str`: return as-is.
        If [`Iterable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterable): concatenate the first element, existing value, and second element.
        If [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable): apply this function to the existing attribute value.
        If `None`: return attribute if it exists, otherwise return `None`.
    str_doesnt : str | None, optional
        The value to return if the attribute doesn't exist. If `None`, returns `None`.

    Returns
    -------
    str | None
        The processed attribute value if it exists, `str_doesnt` if it doesn't exist, or `None` if
        `str_doesnt` is `None` and the attribute doesn't exist.

    Notes
    -----
    If `str_exists` is an `Iterable` with more than two elements, only the first two are used,
    and a warning is printed.

    Examples
    --------
    ???+ example "Basic usage with string"
        ```python
        import ozzy as oz
        import numpy as np

        # Create a sample DataArray with an attribute
        da = oz.DataArray(np.random.rand(3, 3), attrs={'units': 'meters'})

        result = get_attr_if_exists(da, 'missing_attr', 'Exists', 'Does not exist')
        print(result)
        # Output: Does not exist
        ```

    ???+ example "Using an Iterable and a Callable"
        ```python
        import ozzy as oz
        import numpy as np

        da = oz.DataArray(np.random.rand(3, 3), attrs={'units': 'meters'})

        # Using an Iterable
        result = get_attr_if_exists(da, 'units', ['Unit: ', ' (SI)'], 'No unit')
        print(result)
        # Output: Unit: meters (SI)

        result = get_attr_if_exists(da, 'units', lambda x: f'The unit is: {x}', 'No unit found')
        print(result)
        # Output: The unit is: meters

        # Using a Callable
        result = get_attr_if_exists(da, 'units', lambda x: x.upper(), 'No unit')
        print(result)
        # Output: METERS
        ```
    """
    if attr in da.attrs:
        if isinstance(str_exists, str):
            return str_exists
        elif isinstance(str_exists, Iterable):
            if len(str_exists) > 2:
                print(
                    "     WARNING: str_exists argument in set_attr_if_exists has more than two elements. The original attribute is inserted between element 0 and element 1 of str_exists, other elements will be ignored."
                )
            return str_exists[0] + da.attrs[attr] + str_exists[1]
        elif isinstance(str_exists, Callable):
            return str_exists(da.attrs[attr])
        elif str_exists is None:
            return da.attrs[attr]
    else:
        if str_doesnt is not None:
            return str_doesnt
        else:
            return None
