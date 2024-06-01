# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import functools
import glob
import os
import re
import time
from datetime import timedelta
from pathlib import PurePath

import h5py
import numpy as np

# TODO: edit docstrings

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
    >>> @stopwatch
    ... def my_function(a, b):
    ...     return a + b
    ...
    >>> my_function(2, 3)
    -> 'my_function' took: 0:00:00.000001
    5
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


def print_file_item(file):
    """
    Print a file name with a leading '  - '.

    Parameters
    ----------
    file : str
        The file name to be printed.

    Examples
    --------
    >>> print_file_item('example.txt')
    - example.txt
    """
    print("  - " + file)


# String manipulation


def unpack_str(attr):
    """
    Unpack a string from a NumPy ndarray or return the input as is.

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
    >>> unpack_str(np.array(['hello']))
    'hello'
    >>> unpack_str('world')
    'world'
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


def tex_format(str):
    """
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
    >>> tex_format('x^2')
    '$x^2$'
    >>> tex_format('')
    ''
    """
    if str == "":
        newstr = str
    else:
        newstr = "$" + str + "$"
    return newstr


def get_regex_snippet(pattern, string):
    """
    Extract a regex pattern from a string using re.search.

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
    >>> get_regex_snippet(r'\d+', 'hello123world')
    '123'
    """
    return re.search(pattern, string).group(0)


# Class manipulation


def get_user_methods(clss):
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
    >>> class MyClass:
    ...     def __init__(self):
    ...         pass
    ...
    ...     def my_method(self):
    ...         pass
    ...
    >>> get_user_methods(MyClass)
    ['my_method']
    """
    return [
        func
        for func in dir(clss)
        if callable(getattr(clss, func))
        and (func in clss.__dict__)
        and (~func.startswith("__"))
    ]


# I/O


def prep_file_input(files):
    """
    Prepare file input by expanding user paths and converting to absolute paths.

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
    >>> prep_file_input('~/example.txt')
    ['/home/user/example.txt']
    >>> prep_file_input(['~/file1.txt', '~/file2.txt'])
    ['/home/user/file1.txt', '/home/user/file2.txt']
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
    >>> force_str_to_list('hello')
    ['hello']
    >>> force_str_to_list([1, 2, 3])
    [1, 2, 3]
    """
    if isinstance(var, str):
        var = [var]
    return var


def get_abs_filepaths(path, run_dir, quant_files):
    """
    Get absolute file paths for quantification files in a run directory.

    Parameters
    ----------
    path : str
        The base path.
    run_dir : str
        The run directory name.
    quant_files : list of str
        The quantification file names.

    Returns
    -------
    filepaths_to_read : list of str
        A list of absolute file paths for the quantification files.

    Examples
    --------
    >>> get_abs_filepaths('/path/to/data', 'run1', ['quant1.txt', 'quant2.txt'])
    ['/path/to/data/run1/quant1.txt', '/path/to/data/run1/quant2.txt']
    """
    filepaths_to_read = []
    for file in quant_files:
        fileloc = glob.glob(
            "**/" + file, recursive=True, root_dir=os.path.join(path, run_dir)
        )
        fullloc = [os.path.join(path, run_dir, loc) for loc in fileloc]
        filepaths_to_read = filepaths_to_read + fullloc
    return filepaths_to_read


def find_runs(path, runs_pattern):
    """
    Find run directories matching a pattern.

    Parameters
    ----------
    path : str
        The base path.
    runs_pattern : str or list of str
        The run directory name pattern(s).

    Returns
    -------
    dirs_dict : dict
        A dictionary mapping run names to their corresponding directory paths.

    Examples
    --------
    >>> find_runs('/path/to/data', 'run*')
    {'run1': '/path/to/data/run1', 'run2': '/path/to/data/run2'}
    """
    dirs = []
    run_names = []

    runs_list = force_str_to_list(runs_pattern)

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


def check_h5_availability(path):
    """
    Check if an HDF5 file can be opened for writing.

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
    >>> check_h5_availability('/path/to/file.h5')  # doctest: +SKIP
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


def axis_from_extent(nx: int, lims: tuple[float, float]):
    """
    Create a numerical axis from the number of cells and extent limits.

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
    >>> axis_from_extent(10, (0, 1))
    array([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95])
    """
    if nx == 0:
        raise ZeroDivisionError("Number of cells in axis cannot be zero.")
    if lims[1] <= lims[0]:
        raise TypeError("Second elements of 'lims' must be larger than first element.")
    dx = (lims[1] - lims[0]) / nx
    ax = np.linspace(lims[0], lims[1] - dx, num=nx) + 0.5 * dx
    return ax


def bins_from_axis(axis):
    """
    Create bin edges from a numerical axis.

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
    >>> bins_from_axis(np.array([0.1, 0.3, 0.5, 0.7, 0.9]))
    array([0.05, 0.2 , 0.4 , 0.6 , 0.8 , 0.95])
    """
    vmin = axis[0] - 0.5 * (axis[1] - axis[0])
    binaxis = axis + 0.5 * (axis[1] - axis[0])
    binaxis = np.insert(binaxis, 0, vmin)
    return binaxis
