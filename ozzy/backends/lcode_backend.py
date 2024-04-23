import os
import re
from importlib.resources import files

import dask
import dask.array as da
import dask.dataframe as dd
import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm

from ..new_dataobj import new_dataset
from ..utils import axis_from_extent, get_regex_snippet, print_file_item, stopwatch

# HACK: do this in a more pythonic way (blueprint for new backend)
# These three variables must be defined in each backend module
# The function read() must also be defined in each backend module
# TODO: write docstrings

general_regex_pattern = r"([\w-]*?)(\d{5}|\d{6}\.\d{3})?[m|w]?\.([a-z]{3})"
general_file_endings = ["swp", "dat", "det", "bin", "bit", "pls"]
quants_ignore = ["xi"]


lcode_data_file = files("ozzy").joinpath("backends/lcode_file_key.csv")
lcode_regex = pd.read_csv(lcode_data_file, sep=";", header=0)

# -------------------------------------------
# - Define metadata of different file types -
# -------------------------------------------

# Coordinates
default_coord_metadata = {
    "t": {"long_name": r"$t$", "units": r"$\omega_p^{-1}$"},
    "x1": {"long_name": r"$\xi$", "units": r"$k_p^{-1}$"},
    "x2": {"long_name": r"$r$", "units": r"$k_p^{-1}$"},
}

# Grid data
prefix = ["er", "ef", "ez", "bf", "wr", "fi", "nb", "ne", "ni"]
label = [
    r"$E_r$",
    r"$E_\theta$",
    r"$E_z$",
    r"$B_\theta$",
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
prefix = ["x1", "x2", "p1", "p2", "L", "abs_rqm", "q", "pid"]
label = [
    r"$\xi$",
    r"$r$",
    r"$p_z$",
    r"$p_r$",
    r"$L$",
    r"$|\mathrm{rqm}|$",
    r"$q$",
    "pid",
]
units = [
    r"$k_p^{-1}$",
    r"$k_p^{-1}$",
    r"$m_e c$",
    r"$m_e c$",
    r"$m_e c^2 / \omega_p$",
    "",
    r"$e \frac{\Delta \xi}{2 \: r_e}$",
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
    "grid": qinfo_grid,
    "extrema": qinfo_extrema,
    "lineout": qinfo_lineout,
}


# ------------------------
# - Function definitions -
# ------------------------


def set_default_coord_metadata(ods):
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
    for row in lcode_regex.itertuples(index=False):
        pattern = row.regex
        match = re.fullmatch(pattern, os.path.basename(file))
        if match is not None:
            break
    if match is None:
        row = None
    return row


def get_quant_name_from_regex(file_info, file):
    match = re.fullmatch(file_info.regex, os.path.basename(file))
    return match.group(1)


def dd_read_table(file: str, sep=r"\s+", header=None):
    ddf = dd.read_table(file, sep=sep, header=header).to_dask_array(lengths=True)
    return ddf.squeeze()


def lcode_append_time(ds, file_string: str):
    thistime = float(get_regex_snippet(r"\d{5}", os.path.basename(file_string)))
    ds_out = ds.assign_coords({"t": [thistime]})
    ds_out.coords["t"].attrs["long_name"] = r"$t$"
    ds_out.coords["t"].attrs["units"] = r"$\omega_p^{-1}$"
    return ds_out


@stopwatch
def lcode_concat_time(ds):
    ds = xr.concat(ds, "t", fill_value={"q": 0.0})
    ds = ds.sortby("t")
    return ds


def read_parts_single(file: str, **kwargs) -> xr.Dataset:
    parts_cols = list(quant_info["parts"].keys())
    arr = np.fromfile(file).reshape(-1, len(parts_cols))
    dda = da.from_array(arr[0:-1, :])  # last row is excluded because it marks the eof

    data_vars = {}
    for i, var in enumerate(parts_cols[0:-1]):
        data_vars[var] = ("pid", dda[:, i])
    ds = new_dataset(data_vars).assign_coords({"pid": dda[:, -1]})
    ds.coords["pid"].attrs["long_name"] = quant_info["parts"]["pid"][0]

    return ds


def read_lineout_single(file: str, quant_name: str) -> xr.Dataset:
    with dask.config.set({"array.slicing.split_large_chunks": True}):
        ddf = dd_read_table(file)
    ddf = np.flip(ddf, axis=0)

    ndims = ddf.ndim
    assert ndims == 1

    ds = new_dataset(data_vars={quant_name: (["x1"], ddf)}).expand_dims(
        dim={"t": 1}, axis=0
    )
    ds.attrs["ndims"] = ndims

    return ds


def read_lineout_post(ds: xr.Dataset, file_info, fpath: str) -> xr.Dataset:
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
        axis_ds = read_lineout_single(file, quant_name="x1")  # .isel(t=0)
        ds = ds.assign_coords({"x1": axis_ds["x1"]})

    return ds


def read_grid_single(
    file: str, quant_name: str, axes_lims: dict[str, tuple[float, float]] | None
) -> xr.Dataset:
    with dask.config.set({"array.slicing.split_large_chunks": True}):
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


def set_quant_metadata(ds, file_info):
    quants_key = quant_info[file_info.type]
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


def read_agg(files, file_info, parser_func, post_func=None, **kwargs):
    ds_t = []
    (print_file_item(file) for file in files)
    for file in tqdm(files):
        ds_tmp = parser_func(file, **kwargs)
        ds_tmp = lcode_append_time(ds_tmp, file)
        ds_t.append(ds_tmp)
    print("  Concatenating along time...")
    ds = lcode_concat_time(ds_t)

    # Get name of quantity and define appropriate metadata
    ds = set_quant_metadata(ds, file_info)

    if post_func is not None:
        fpath = os.path.dirname(files[0])
        ds = post_func(ds, file_info, fpath)

    return ds


def read_extrema(files: list[str] | str, file_info):
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


def read(
    files: list[str], axes_lims: dict[str, tuple[float, float]] | None = None, **kwargs
):
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
                ds = read_agg(files, file_info, read_parts_single, **kwargs)
                pic_data_type = "part"

            case "extrema":
                ds = read_extrema(files, file_info)
                pic_data_type = "grid"

            case "info" | "plzshape" | "beamfile" | "notimplemented":
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


# Defines specific methods for data from this code
class Methods:
    def convert_q(self, dxi, q_var="q", n0=None):
        # expects n0 in 1/cm^3
        # TODO: make this compatible with pint

        if self.pic_data_type != "part":
            raise ValueError("This method can only be used on particle data")

        print("\n   Converting charge...")

        re = 2.8179403227e-13  # in cm
        if n0 is None:
            print("         - assuming dxi is in units of cm")
            factor = dxi / (2 * re)
        else:
            print("         - assuming dxi is in normalized units")
            distcm = 531760.37819 / np.sqrt(n0)
            factor = dxi * distcm / (2 * re)

        self._obj[q_var] = self._obj[q_var] * factor
        self._obj[q_var].attrs["units"] = "$e$"

        return
