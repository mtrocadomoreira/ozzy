# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import os
import re
from importlib.resources import files
from typing import Callable, NamedTuple

import dask
import dask.array as da
import dask.dataframe as dd
import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm

from ..new_dataobj import new_dataset
from ..utils import axis_from_extent, get_regex_snippet, print_file_item, stopwatch

# TODO: implement LCODE 3D

# HACK: do this in a more pythonic way (blueprint for new backend)

general_regex_pattern = r"([\w-]*?)(\d{5,6}|\d{5,6}\.\d{3})*?[m|w]?\.([a-z]{3})"
"""A regular expression pattern used to match file names in the LCODE data format.

The pattern matches file names that start with an optional word character sequence (letters, digits, or underscores),
followed by a sequence of 5 or 6 digits (or 5 or 6 digits followed by a decimal point and 3 more digits),
optionally followed by 'm' or 'w', and ending with a 3-letter extension.
"""

general_file_endings = ["swp", "dat", "det", "bin", "bit", "pls"]
"""A list of file extensions for LCODE data files. These extensions are used to identify and filter out certain types of files when trying to find LCODE data.
"""

quants_ignore = ["xi"]
"""A list of quantities to be ignored when reading LCODE data.
"""


lcode_data_file = files("ozzy").joinpath("backends/lcode_file_key.csv")
"""The path to the `lcode_file_key.csv` file, which contains information about LCODE file types and their associated regular expressions.

This file is used by the `get_file_type` function to identify the type of LCODE data file based on its file name.
"""

lcode_regex = pd.read_csv(lcode_data_file, sep=";", header=0)
"""A [DataFrame][pandas.DataFrame] containing information about LCODE file types and their associated regular expressions. This DataFrame is read from the `lcode_file_key.csv` file.
"""

# -------------------------------------------
# - Define metadata of different file types -
# -------------------------------------------

# Coordinates
default_coord_metadata = {
    "t": {"long_name": r"$t$", "units": r"$\omega_p^{-1}$"},
    "x1": {"long_name": r"$x_1$", "units": r"$k_p^{-1}$"},
    "x2": {"long_name": r"$x_2$", "units": r"$k_p^{-1}$"},
}

# Grid data
prefix = ["er", "ef", "ez", "bf", "wr", "fi", "nb", "ne", "ni"]
label = [
    r"$E_2$",
    r"$E_3$",
    r"$E_1$",
    r"$B_3$",
    r"$E_r - c B_\theta$",
    r"$\Phi$",
    r"$\rho_b$",
    r"$\delta n_e$",
    r"$\delta n_i$",
]
units = [
    r"$E_0$",
    r"$E_0$",
    r"$E_0$",
    r"$E_0$",
    r"$E_0$",
    r"$m_e c^2/e$",
    r"$e n_0$",
    r"$n_0$",
    r"$n_0$",
]
qinfo_grid = dict()
for i, pref in enumerate(prefix):
    qinfo_grid[pref] = (label[i], units[i])

# Particle data
prefix = ["x1", "x2", "p1", "p2", "p3", "L", "abs_rqm", "q", "pid"]
label = [
    r"$\xi$",
    r"$r$",
    r"$p_1$",
    r"$p_2$",
    r"$p_3$",
    r"$L$",
    r"$|\mathrm{rqm}|$",
    r"$q$",
    "pid",
]
units = [
    r"$k_p^{-1}$",
    r"$k_p^{-1}$",
    r"$m_\mathrm{sp} c$",
    r"$m_\mathrm{sp} c$",
    r"$m_\mathrm{sp} c$",
    r"$m_\mathrm{sp} c^2 / \omega_p$",
    "",
    r"$\frac{\Delta \hat{\xi}}{2} \frac{I_A}{\omega_p}$",
    "",
]
qinfo_parts = dict()
for i, pref in enumerate(prefix):
    qinfo_parts[pref] = (label[i], units[i])

# Field extrema
prefix = ["e", "g"]
label = [r"$E_z$", r"$\Phi$"]
units = [r"$E_0$", r"$m_e c^2 / e$"]
qinfo_extrema = dict()
for i, pref in enumerate(prefix):
    qinfo_extrema[pref] = (label[i], units[i])

# Lineouts
prefix = ["xi_Ez", "xi_Ez2", "xi_Er", "xi_Bf", "xi_Ef", "xi_ne", "xi_nb", "xi_nb2"]
label = [
    r"$E_z(r=0)$",
    r"$E_z(r=r_\mathrm{aux})$",
    r"$E_r(r=r_\mathrm{aux})$",
    r"$B_\theta(r=r_\mathrm{aux})$",
    r"$E_\theta(r=r_\mathrm{aux})$",
    r"$\delta n_e(r = 0)$",
    r"$\rho_b(r=0)$",
    r"$\rho_b(r=r_\mathrm{aux})$",
]
units = [
    r"$E_0$",
    r"$E_0$",
    r"$E_0$",
    r"$E_0$",
    r"$E_0$",
    r"$n_0$",
    r"$e n_0$",
    r"$e n_0$",
]
qinfo_lineout = dict()
for i, pref in enumerate(prefix):
    qinfo_lineout[pref] = (label[i], units[i])

quant_info = {
    "parts": qinfo_parts,
    "beamfile": qinfo_parts,
    "grid": qinfo_grid,
    "extrema": qinfo_extrema,
    "lineout": qinfo_lineout,
}
"""A dictionary containing information about different types of quantities in LCODE data.
"""


# ------------------------
# - Function definitions -
# ------------------------


def set_default_coord_metadata(ods):
    """Set default metadata for coordinate variables in an xarray.Dataset.

    Parameters
    ----------
    ods : xarray.Dataset
        The input Dataset for which the coordinate metadata should be set.

    Returns
    -------
    xarray.Dataset
        The input Dataset with default metadata set for coordinate variables.

    Notes
    -----
    This function sets the `'long_name'` and `'units'` attributes for coordinate variables (`'t'`, `'x1'`, and `'x2'`)
    based on the `default_coord_metadata` dictionary. If the attribute is already set or has a non-empty string value,
    it is not overwritten.

    """
    for var in ods.coords:
        if var in default_coord_metadata:
            # Check which metadata should be set
            set_meta = {"long_name": False, "units": False}
            for k in set_meta.keys():
                if k not in ods.coords[var].attrs:
                    set_meta[k] = True
                elif len(ods.coords[var].attrs[k]) == 0:
                    set_meta[k] = True

            if any(set_meta.values()):
                for k, v in set_meta.items():
                    ods.coords[var].attrs[k] = (
                        default_coord_metadata[var][k] if v else None
                    )

    return ods


def get_file_type(file: str):
    """Determine the type of an LCODE data file based on its file name.

    Parameters
    ----------
    file : str
        The path to the LCODE data file.

    Returns
    -------
    namedtuple or None
        A `namedtuple` containing information about the file type (regex pattern, type, and supplementary pattern), or `None` if the file type could not be determined.

    Notes
    -----
    This function uses the `lcode_regex` DataFrame to match the file name against the regular expressions for different LCODE file types.

    """
    for row in lcode_regex.itertuples(index=False):
        pattern = row.regex
        match = re.fullmatch(pattern, os.path.basename(file))
        if match is not None:
            break
    if match is None:
        row = None
    return row


def get_quant_name_from_regex(file_info: NamedTuple, file: str) -> str:
    """Extract the quantity name from an LCODE file name using a regular expression.

    Parameters
    ----------
    file_info : namedtuple
        A namedtuple containing information about the file type, including the regular expression pattern.
    file : str
        The path to the LCODE data file.

    Returns
    -------
    str
        The quantity name extracted from the file name using the regular expression pattern.
    """
    match = re.fullmatch(file_info.regex, os.path.basename(file))
    return match.group(1)


def dd_read_table(file: str, sep=r"\s+", header=None) -> dask.array.Array:
    """Read a tabular data file into a [Dask Array][dask.array.core.Array].

    Parameters
    ----------
    file : str
        The path to the tabular data file.
    sep : str, optional
        The string used to separate values in the file. Default is `r"\\s+"` (one or more whitespace characters).
    header : int, list of int, or None, optional
        The row number(s) to use as the column names, and the start of the data. Default is None, meaning no header row.

    Returns
    -------
    [Dask Array][dask.array.Array]
        A Dask Array containing the data from the file, squeezed to remove any dimensions of length 1.

    Notes
    -----
    This function uses [`dask.dataframe.read_table`][dask.dataframe.read_table] to read the tabular data file into a [Dask DataFrame][dask.dataframe.DataFrame], and then converts it to a Dask Array using [`to_dask_array`][dask.dataframe.DataFrame.to_dask_array]. The resulting Dask Array is squeezed to remove any dimensions
    of length 1.
    """
    ddf = dd.read_table(file, sep=sep, header=header).to_dask_array(lengths=True)
    return ddf.squeeze()


def lcode_append_time(
    ds: xr.Dataset | xr.DataArray, time: float
) -> xr.Dataset | xr.DataArray:
    """
    Append a time coordinate to an xarray.Dataset.

    Parameters
    ----------
    ds : xarray.Dataset
        The input xarray.Dataset to append the time coordinate to.
    time : float
        The time value to append as the time coordinate.

    Returns
    -------
    xarray.Dataset
        The input xarray.Dataset with the time coordinate appended.

    Examples
    --------
    ???+ example "Append time coordinate to Dataset"
        ```python
        import xarray as xr
        import ozzy as oz

        # Create a sample Dataset
        data = xr.DataArray(
            data=[[1, 2], [3, 4]],
            coords={"x": [0, 1], "y": [0, 1]},
            dims=("y", "x"),
        )
        ds = data.to_dataset(name="var")

        # Append time coordinate
        ds_with_time = oz.lcode_append_time(ds, 10.0)
        print(ds_with_time)
        # <xarray.Dataset>
        # Dimensions:  (y: 2, x: 2, t: 1)
        # Coordinates:
        #   * x        (x) int64 0 1
        #   * y        (y) int64 0 1
        #   * t        (t) float64 10.0
        # Data variables:
        #     var      (y, x) int64 1 2 3 4
        ```
    """
    ds_out = ds.assign_coords({"t": [time]})
    ds_out.coords["t"].attrs["long_name"] = r"$t$"
    ds_out.coords["t"].attrs["units"] = r"$\omega_p^{-1}$"
    return ds_out


def lcode_append_time_from_fname(
    ds: xr.DataArray | xr.Dataset, file_string: str
) -> xr.DataArray | xr.Dataset:
    """Append a time coordinate to an xarray.Dataset based on the file name.

    Parameters
    ----------
    ds : xarray.Dataset
        The input Dataset to which the time coordinate should be appended.
    file_string : str
        The file name from which the time value should be extracted.

    Returns
    -------
    xarray.Dataset
        The input Dataset with a new `'t'` coordinate appended, containing the time value extracted from the file name.

    Notes
    -----
    This function assumes that the file name contains a sequence of 5 or 6 digits representing the time value.
    It extracts this value using a regular expression and assigns it to a new `'t'` coordinate in the input Dataset.
    The `'long_name'` and `'units'` attributes for the `'t'` coordinate are also set.

    Examples
    --------
    >>> ds = xr.Dataset({'var': (['x1', 'x2'], np.random.rand(10, 20))},
    ...                  coords={'x1': np.linspace(0, 1, 10),
    ...                          'x2': np.linspace(0, 1, 20)})
    >>> ds = lcode_append_time_from_fname(ds, 'file_000005.dat')
    >>> ds.coords
    Coordinates:
      * x1        (x1) float64 0.0 0.1111 0.2222 0.3333 ... 0.7778 0.8889 1.0
      * x2        (x2) float64 0.0 0.05263 0.1053 0.1579 ... 0.8947 0.9474 1.0
      * t         (t) int64 5
    """
    thistime = float(get_regex_snippet(r"\d{5,6}", os.path.basename(file_string)))
    ds_out = lcode_append_time(ds, thistime)
    return ds_out


@stopwatch
def lcode_concat_time(ds: xr.Dataset | list[xr.Dataset]) -> xr.Dataset:
    """Concatenate an xarray.Dataset along the time dimension.

    Parameters
    ----------
    ds : xarray.Dataset or list[xarray.Dataset]
        The input Dataset(s) to be concatenated along the time dimension.

    Returns
    -------
    xarray.Dataset
        The concatenated Dataset, sorted along the time dimension.

    Notes
    -----
    This function uses `xarray.concat` to concatenate the input Dataset(s) along the `'t'` dimension. If the input is a
    list of Datasets, they are concatenated together. If the input is a single Dataset, it is assumed to be a collection of Datasets along the `'t'` dimension.

    Any missing values in the concatenated Dataset are filled with `0.0` for the `'q'` variable.

    The resulting concatenated Dataset is sorted along the `'t'` dimension.
    """
    ds = xr.concat(ds, "t", fill_value={"q": 0.0})
    ds = ds.sortby("t")
    ds = ds.chunk("auto")
    return ds


def read_parts_single(file: str, axisym: bool, abs_q: float) -> xr.Dataset:
    """Read particle data from a single LCODE file into an xarray.Dataset.

    Parameters
    ----------
    file : str
        The path to the LCODE particle data file.
    **kwargs
        Additional keyword arguments to be passed to the function.

    Returns
    -------
    xarray.Dataset
        An xarray.Dataset containing the particle data read from the file.

    Notes
    -----
    The particle data variables are read into the Dataset as data variables, with the `'pid'` variable used as a coordinate.

    Examples
    --------
    >>> ds = read_parts_single('tb02500.swp', axisym=True, abs_q = 1.0)
    >>> ds.data_vars
    Data variables:
        x1        (pid) float64 ...
        x2        (pid) float64 ...
        p1        (pid) float64 ...
        p2        (pid) float64 ...
        p3        (pid) float64 ...
        L         (pid) float64 ...
        abs_rqm   (pid) float64 ...
        q         (pid) float64 ...
    """
    parts_cols = ["x1", "x2", "p1", "p2", "p3", "abs_rqm", "q", "pid"]
    arr = np.fromfile(file).reshape(-1, len(parts_cols))
    with dask.config.set({"array.slicing.split_large_chunks": False}):
        dda = da.from_array(
            arr[0:-1, :],
            chunks=-1,
        )  # last row is excluded because it marks the EOF

    data_vars = {}
    for i, var in enumerate(parts_cols[0:-1]):
        data_vars[var] = ("pid", dda[:, i])
    ds = (
        new_dataset(data_vars)
        .assign_coords({"pid": dda[:, -1]})
        .expand_dims(dim={"t": 1}, axis=1)
    )
    ds.coords["pid"].attrs["long_name"] = quant_info["parts"]["pid"][0]

    # Convert units of momentum variables from m_e*c to m_sp*c

    meMb = ds["abs_rqm"] / abs_q
    for var in ["p1", "p2", "p3"]:
        ds[var] = ds[var] * meMb

    # Add p3 data variable

    if axisym:
        ds = ds.rename_vars({"p3": "L"})
        ds["p3"] = ds["L"] / ds["x2"]

    return ds


def read_lineout_single(file: str, quant_name: str) -> xr.Dataset:
    """Read lineout data from a single LCODE file into an xarray.Dataset.

    Parameters
    ----------
    file : str
        The path to the LCODE lineout data file.
    quant_name : str
        The name of the quantity to be read from the file.

    Returns
    -------
    xarray.Dataset
        An xarray.Dataset containing the lineout data read from the file.

    Notes
    -----
    The data is flipped along the first dimension (assuming the lineout data is stored in descending order) and expanded to include a `'t'` (time) dimension.
    """
    with dask.config.set({"array.slicing.split_large_chunks": False}):
        ddf = dd_read_table(file)
    ddf = np.flip(ddf, axis=0)

    ndims = ddf.ndim
    assert ndims == 1

    ds = new_dataset(data_vars={quant_name: (["x1"], ddf)}).expand_dims(
        dim={"t": 1}, axis=0
    )
    ds.attrs["ndims"] = ndims

    return ds


def read_lineout_post(ds: xr.Dataset, file_info: NamedTuple, fpath: str) -> xr.Dataset:
    """
    Read supplementary data for lineout files and assign it to the input Dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The input Dataset to which supplementary data will be assigned.
    file_info : FileInfo
        An object containing information about the file type and regex pattern.
    fpath : str
        The path to the directory containing the supplementary files.

    Returns
    -------
    xr.Dataset
        The input Dataset with supplementary data assigned as a new coordinate.

    """
    files = (
        os.path.join(fpath, file)
        for file in os.listdir(fpath)
        if os.path.isfile(os.path.join(fpath, file))
    )
    for file in files:
        match = re.fullmatch(file_info.suppl, os.path.basename(file))
        if match is not None:
            print(f"    -> found a file with xi axis data:\n        {file}")
            break

    if match is not None:
        axis_ds = read_lineout_single(file, quant_name="x1")
        ds = ds.assign_coords({"x1": axis_ds["x1"]})

    return ds


def read_grid_single(
    file: str, quant_name: str, axes_lims: dict[str, tuple[float, float]] | None
) -> xr.Dataset:
    """
    Read a single grid file and create a Dataset with the specified quantity.

    Parameters
    ----------
    file : str
        The path to the grid file.
    quant_name : str
        The name of the quantity to be read from the file.
    axes_lims : dict[str, tuple[float, float]] or None
        A dictionary containing the limits for each axis, or None if no limits are provided.

    Returns
    -------
    xr.Dataset
        A Dataset containing the specified quantity and coordinates (if provided).

    """
    with dask.config.set({"array.slicing.split_large_chunks": False}):
        ddf = dd_read_table(file)
    ddf = np.flip(ddf.transpose(), axis=1)

    ndims = ddf.ndim
    assert ndims == 2

    nx2, nx1 = ddf.shape

    ds = new_dataset(
        data_vars={quant_name: (["x2", "x1"], ddf)},
    ).expand_dims(dim={"t": 1}, axis=ndims)
    ds.attrs["ndims"] = ndims

    if axes_lims is not None:
        ds = ds.assign_coords(
            {
                "x1": ("x1", axis_from_extent(nx1, axes_lims["x1"])),
                "x2": ("x2", axis_from_extent(nx2, axes_lims["x2"])),
            }
        )

    return ds


def set_quant_metadata(ds: xr.Dataset, file_type: str) -> xr.Dataset:
    r"""
    Set the metadata (long name and units) for the quantities in the input `xarray.Dataset`.

    Parameters
    ----------
    ds : xarray.Dataset
        The input Dataset containing the quantities.
    file_type : str
        The type of file the data is from.

    Returns
    -------
    xarray.Dataset
        The input Dataset with metadata assigned to the quantities.

    Examples
    --------
    ???+ example "Set metadata for LCODE particle data"
        ```python
        import xarray as xr
        import ozzy.backends.lcode_backend as lcode

        # Load particle data from LCODE
        ds = xr.open_dataset('particles.h5')

        # Set metadata
        ds = lcode.set_quant_metadata(ds, 'part')
        ```

    ???+ example "Set metadata for LCODE field data"
        ```python
        import xarray as xr
        import ozzy.backends.lcode_backend as lcode

        # Load field data from LCODE
        ds = xr.open_dataset('fields.h5')

        # Set metadata
        ds = lcode.set_quant_metadata(ds, 'grid')
        ```
    """

    quants_key = quant_info[file_type]
    for quant in ds.data_vars:
        q_in_quant = ((q == quant, q) for q in quants_key)
        found_q = False
        while found_q is False:
            try:
                found_q, q = next(q_in_quant)
            except StopIteration:
                break
        if found_q is True:
            ds[q] = ds[q].assign_attrs(
                {"long_name": quants_key[q][0], "units": quants_key[q][1]}
            )
        else:
            ds[quant].attrs["long_name"] = quant
    return ds


def read_agg(
    files: list[str],
    file_info: NamedTuple,
    parser_func: Callable,
    post_func: Callable = None,
    *args,
    **kwargs,
) -> xr.Dataset:
    """
    Read and aggregate multiple files into a single Dataset.

    Parameters
    ----------
    files : list[str]
        A list of file paths to be read.
    file_info : NamedTuple
        An object (a Pandas DataFrame row returned by [`pandas.DataFrame.itertuples`][pandas.DataFrame.itertuples]) containing information about the file type and regex pattern.
    parser_func : callable
        A function to parse individual files and create a Dataset.
    post_func : callable or None, optional
        A function to perform post-processing on the aggregated Dataset (default is None).
    **kwargs
        Additional keyword arguments to be passed to the `parser_func`.

    Returns
    -------
    xr.Dataset
        The aggregated Dataset containing data from all input files.

    """
    ds_t = []
    [print_file_item(file) for file in files]
    for file in tqdm(files):
        ds_tmp = parser_func(file, *args, **kwargs)
        ds_tmp = lcode_append_time_from_fname(ds_tmp, file)
        ds_t.append(ds_tmp)
    print("  Concatenating along time...")
    ds = lcode_concat_time(ds_t)

    # Get name of quantity and define appropriate metadata
    ds = set_quant_metadata(ds, file_info.type)

    if post_func is not None:
        fpath = os.path.dirname(files[0])
        ds = post_func(ds, file_info, fpath)

    return ds


def read_beamfile(
    files: list[str], file_info: NamedTuple, axisym: bool, abs_q: float
) -> xr.Dataset:
    r"""
    Read particle data from a list of LCODE beam files and return an xarray.Dataset.

    Parameters
    ----------
    files : list[str]
        A list of file paths to the LCODE beam files.
    file_info : NamedTuple
        An object (a Pandas DataFrame row returned by [`pandas.DataFrame.itertuples`][pandas.DataFrame.itertuples]) containing information about the file type and regex pattern.

    Returns
    -------
    xr.Dataset
        An xarray.Dataset containing the particle data from the input files.

    """
    datasets = []
    for file in files:
        print_file_item(file)
        ds = read_parts_single(file, axisym=axisym, abs_q=abs_q)
        bitfile = file.replace(".bin", ".bit")
        try:
            thistime = np.loadtxt(bitfile)
        except FileNotFoundError:
            print(" - WARNING: Could not find 'beamfile.bit'. Assuming t = 0.0")
            thistime = 0.0
        ds = lcode_append_time(ds, thistime)
        datasets.append(ds)

    ds_out = xr.merge(datasets)
    ds_out = set_quant_metadata(ds_out, file_info.type)
    return ds_out


def read_extrema(files: list[str] | str, file_info: NamedTuple) -> xr.Dataset:
    """
    Read extrema data from one or more files.

    Parameters
    ----------
    files : list[str] or str
        A list of file paths or a single file path containing extrema data.
    file_info : NamedTuple
        An object (a Pandas DataFrame row returned by [`pandas.DataFrame.itertuples`][pandas.DataFrame.itertuples]) containing information about the file type and regex pattern.

    Returns
    -------
    xr.Dataset
        A Dataset containing the extrema data.
    """
    with dask.config.set({"array.slicing.split_large_chunks": True}):
        ddf = dd_read_table(files)

    match = re.fullmatch(file_info.regex, files[0])
    quant = match.group(1)

    prefix = ""
    quant1 = quant + "_max"
    quant2 = quant1.replace("max", "min")

    if match.group(2) == "loc":
        quant1 = quant1 + "_loc"
        prefix = "local "

    ds = new_dataset(
        data_vars={
            quant1: ("t", ddf[:, 1]),
            quant2: ("t", ddf[:, 3]),
            "ximax": ("t", ddf[:, 2]),
            "ximin": ("t", ddf[:, 4]),
        },
        coords={"t": ddf[:, 0]},
    )

    ds[quant1] = ds[quant1].assign_attrs(
        long_name=prefix + "max. " + quant_info[file_info.type][quant][0],
        units=quant_info[file_info.type][quant][1],
    )
    ds[quant2] = ds[quant2].assign_attrs(
        long_name=prefix + "min. " + quant_info[file_info.type][quant][0],
        units=quant_info[file_info.type][quant][1],
    )
    ds["t"] = ds["t"].assign_attrs(long_name=r"$t$", units=r"$\omega_p^{-1}$")

    return ds


def read_plzshape(files: list[str] | str, file_info: NamedTuple) -> xr.Dataset:
    """
    Read plasma shape data from one or more files.

    Parameters
    ----------
    files : list[str] or str
        A list of file paths or a single file path containing plasma shape data.
    file_info : NamedTuple
        An object (a Pandas DataFrame row returned by [`pandas.DataFrame.itertuples`][pandas.DataFrame.itertuples]) containing information about the file type and regex pattern.


    Returns
    -------
    xr.Dataset
        A Dataset containing the plasma shape data.
    """
    with dask.config.set({"array.slicing.split_large_chunks": True}):
        ddf = dd_read_table(files)

    ds = new_dataset(
        data_vars={
            "np": ("t", ddf[:, 1]),
        },
        coords={"t": ("t", ddf[:, 0])},
    )

    ds["np"] = ds["np"].assign_attrs(
        long_name="Longitudinal plasma density profile", units=r"$n_0$"
    )
    ds["t"] = ds["t"].assign_attrs(long_name=r"$t$", units=r"$\omega_p^{-1}$")

    return ds


# TODO: maybe print warning in case abs_q is not provided (momentum normalization may be wrong/units may be wrong)
def read(
    files: list[str],
    axes_lims: dict[str, tuple[float, float]] | None = None,
    axisym: bool = True,
    abs_q: float = 1.0,
) -> xr.Dataset:
    r"""
    Read one or more LCODE data files and create a Dataset.

    Parameters
    ----------
    files : list[str]
        A list of file paths to be read.
    axes_lims : dict[str, tuple[float, float]] | None, optional
        A dictionary specifying the limits for each axis in the data. Keys are axis names, and values are tuples of (min, max) values.
    axisym : bool, optional
        Whether the data is in 2D axisymmetric/cylindrical geometry.
    abs_q : float, optional
        Absolute value of the charge of the bunch particles, in units of the elementary charge $e$.

        This argument is used to normalize the particle momenta to $m_\mathrm{sp} c$ instead of LCODE's default of $m_e c$.

    Returns
    -------
    xr.Dataset
        A Dataset containing the data from the input files.

    Examples
    --------

    !!! warning

        Note that you would not usually call this function directly, except in advanced use cases such as debugging. The examples below are included for completeness.

        In general, please use [ozzy's file-reading functions][reading-files] along with the backend specification instead, for example:
        ```python
        data = oz.open('lcode', 'path/to/file.swp')
        ```

    ??? example "Reading grid files with axis limits"
        ```python
        from ozzy.backends.lcode_backend import read

        files = ['grid_file1.swp', 'grid_file2.swp']
        axes_lims = {'x1': (0, 10), 'x2': (-5, 5)}
        ds = read(files, axes_lims)
        # Returns Dataset with grid data and axis coordinates
        ```

    ??? example "Reading particle data with custom charge"

        The `abs_q` keyword argument is used to normalize the particle momenta to $m_\mathrm{sp} c$ (instead of LCODE's default of $m_e c$).

        ```python
        from ozzy.backends.lcode_backend import read
        files = ['tb00200.swp']
        ds = read(files, axisym=True, abs_q=2.0)
        # Returns Dataset with particle momenta normalized to the species mass times the speed of light
        ```
    """
    if len(files) == 0:
        ds = new_dataset()
    else:
        file_info = get_file_type(files[0])

        if file_info is None:
            raise TypeError("Could not identify the type of LCODE data file.")

        pic_data_type = None
        match file_info.type:
            case "grid":
                if axes_lims is None:
                    print(
                        "\nWARNING: axis extents were not specified. Dataset object(s) will not have any coordinates.\n"
                    )
                ds = read_agg(
                    files,
                    file_info,
                    read_grid_single,
                    quant_name=get_quant_name_from_regex(file_info, files[0]),
                    axes_lims=axes_lims,
                )
                pic_data_type = "grid"

            case "lineout":
                ds = read_agg(
                    files,
                    file_info,
                    read_lineout_single,
                    post_func=read_lineout_post,
                    quant_name=get_quant_name_from_regex(file_info, files[0]),
                )
                pic_data_type = "grid"

            case "parts":
                ds = read_agg(
                    files, file_info, read_parts_single, axisym=axisym, abs_q=abs_q
                )
                pic_data_type = "part"

            case "extrema":
                ds = read_extrema(files, file_info)
                pic_data_type = "grid"

            case "plzshape":
                ds = read_plzshape(files, file_info)
                pic_data_type = "grid"

            case "beamfile":
                ds = read_beamfile(files, file_info, axisym, abs_q)
                pic_data_type = "part"
                pass

            case "info" | "notimplemented":
                raise NotImplementedError(
                    "Backend for this type of file has not been implemented yet. Exiting."
                )
            case _:
                raise TypeError(
                    "Data type identified via lcode_file_key.csv is not foreseen in backend code for LCODE. This is probably an important bug."
                )

        ds.attrs["pic_data_type"] = pic_data_type
        ds = set_default_coord_metadata(ds)

        if (file_info.type == "grid") & (axes_lims is not None):
            ds = ds.ozzy.coords_from_extent(axes_lims)

    return ds


class Methods:
    """The methods in this class are accessible to a data object when `<data_obj>.attrs['data_origin'] == 'lcode'`."""

    def convert_q(self, dxi: float, n0: float, q_var: str = "q") -> None:
        r"""Convert the charge variable to physical units (in units of $e$).

        Parameters
        ----------
        dxi : float
            The grid spacing in the longitudinal direction in normalized units, i.e., in units of $k_p^{-1}$. or $\mathrm{cm}$.
        n0 : float
            The reference density, in $\mathrm{cm}^{-3}$.
        q_var : str, default 'q'
            Name of the charge density variable.

        Returns
        -------
        None
            The dataset is modified in place.

        Notes
        -----
        The charge in physical units ($\mathrm{C}$) is obtained by multiplying the normalized charge with the factor $\frac{\Delta \hat{\xi}}{2} \frac{I_A}{\omega_p}$, where $\Delta \hat{\xi} = k_p \Delta \xi$ is the normalized longitudinal cell size and $I_A$ is the Alfvén current, defined as:

        \[
        I_A = 4 \pi \varepsilon_0 \frac{m_e c^3}{e} \approx 17.045 \ \mathrm{kA}
        \]

        Note that the charge is given in units of the elementary charge $e$ after this method is applied.

        Examples
        --------

        ???+ example "Particle data"

            ```python
            import ozzy as oz
            ds = oz.open('lcode', [part example])
            ds.ozzy.convert_q(dxi=0.01, n0=2e14, q_var='q')
            print(ds)

            ```
        """
        # TODO: make this compatible with pint

        try:
            assert isinstance(n0, float)
        except AssertionError:
            raise ValueError("n0 argument must be a float")

        # Alfven current divided by elementary charge
        alfven_e = 1.0638708535128997e23  # 1/s
        # Plasma frequency
        omega_p = 56414.60231191864 * np.sqrt(n0)  # 1/s
        factor = dxi * 0.5 * alfven_e / omega_p
        self._obj[q_var] = self._obj[q_var] * factor
        self._obj[q_var].attrs["units"] = "$e$"

        return
