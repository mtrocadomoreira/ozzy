from .utils import stopwatch, print_file_item, get_regex_snippet
from .ozdataset import OzDataset
import os
import re
import numpy as np
import pandas as pd
import dask
import dask.dataframe as dd
import dask.array as da
import xarray as xr
from importlib.resources import files

# These three variables must be defined in each backend module

general_regex_pattern = r"([\w-]*?)(\d{5}|\d{6}\.\d{3})?[m|w]?\.([a-z]{3})"
general_file_endings = ["swp", "dat", "det", "bin", "bit", "pls"]
quants_ignore = ["xi"]

# The function read() must also be defined in each backend module

lcode_data_file = files("ozzy_refactor").joinpath("lcode_file_key.csv")
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
    r"$\delta n_i$"
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
    r"$n_0$"
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
    "pid"
]
units = [
    r"$k_p^{-1}$",
    r"$k_p^{-1}$",
    r"$m_e c$",
    r"$m_e c$",
    r"$m_e c^2 / \omega_p$",
    "",
    r"$e \frac{\Delta \xi}{2 \: r_e}$",
    ""
]
qinfo_parts = dict()
for i, pref in enumerate(prefix):
    qinfo_parts[pref] = (label[i], units[i])

# Field extrema
prefix = ['e', 'g']
label = [r"$E_z$", r"$\Phi$"]
units = [r"$E_0$", r"$m_e c^2 / e$"]
qinfo_extrema = dict()
for i, pref in enumerate(prefix):
    qinfo_extrema[pref] = (label[i], units[i])


quant_info['parts'] = qinfo_parts
quant_info['grid'] = qinfo_grid
quant_info['extrema'] = qinfo_extrema


# ------------------------
# - Function definitions -
# ------------------------

def set_default_coord_metadata(self, ods):
    for var in ods.coords:
        if var in default_coord_metadata:
            # Check which metadata should be set
            set_meta = {"long_name": False, "units": False}
            for k in set_meta.keys():
                if k not in ods.coords[var].attrs:
                    set_meta[k] = True
                else:
                    if len(ods.coords[var].attrs[k]) == 0:
                        set_meta[k] = True

            if any(set_meta.values()):
                for k, v in set_meta.items():
                    ods.coords[var].attrs[k] = (
                        default_coord_metadata[var][k] if v else None
                    )

    return ods

def get_file_type(file):
    for row in lcode_regex.itertuples(index=False):
        pattern = row.regex
        match = re.fullmatch(pattern, os.path.basename(file))
        if match is not None:
            break
    if match is None:
        row = None
    return row


def dd_read_table(file, sep=r"\s+", header=None):
    ddf = dd.read_table(file, sep=sep, header=header).to_dask_array(lengths=True)
    return ddf.squeeze()


def lcode_append_time(ds, file_string):
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


def read_parts_single(file):
    parts_cols = list(quant_info['parts'].keys())
    arr = np.fromfile(file).reshape(-1, len(parts_cols))
    dda = da.from_array(arr[0:-1, :]) # last row is excluded because it marks the eof

    data_vars = {}
    for i, var in enumerate(parts_cols[0:-1]):
        data_vars[var] = ("pid", dda[:, i])
    ds = xr.Dataset(data_vars).assign_coords({"pid": dda[:, -1]})
    ds.coords["pid"].attrs["long_name"] = quant_info['parts']['pid'][0]

    return ds


def read_lineout_single(file, **kwargs):
    with dask.config.set({"array.slicing.split_large_chunks": True}):
        ddf = dd_read_table(file)
    ddf = np.flip(ddf, axis=0)

    ndims = ddf.ndim
    assert ndims == 1

    ds = xr.Dataset(data_vars={quant_name: (["x1"], ddf)})\
        .expand_dims(dim={"t": 1}, axis=ndims)
    ds.attrs["ndims"] = ndims

    return ds

def read_lineout_post(ds, file_info, fpath):

    files = (os.path.join(fpath,file) for file in os.listdir(fpath) if os.path.isfile(os.path.join(fpath, file)))
    for file in files:
        match = re.fullmatch(file_info.suppl, os.path.basename(file))
        if match is not None:
            print(f"    -> found a file with xi axis data:\n        {file}")
            break
    
    if match is not None:
        axis_ds = read_lineout_single(file, quant_name='x1').isel(t=0)
        ds = ds.assign_coords({'x1': axis_ds['x1']})

    return ds


def read_grid_single(file, **kwargs):
    with dask.config.set({"array.slicing.split_large_chunks": True}):
        ddf = dd_read_table(file)
    ddf = np.flip(ddf.transpose(), axis=1)

    ndims = ddf.ndim
    assert ndims == 2

    ds = xr.Dataset(data_vars={quant_name: (["x2", "x1"], ddf)})\
        .expand_dims(dim={"t": 1}, axis=ndims)
    ds.attrs["ndims"] = ndims

    return ds


def set_quant_metadata(ds, file_info):
    quants_key = quant_info[file_info.type]
    for quant in ds.data_vars:
        q_in_quant = ((q in quant, q) for q in quants_key)
        found_q = False
        while found_q is False:
            found_q, q = next(q_in_quant)
        if found_q is True:
            ds[q] = ds[q].assign_attrs({
                    'long_name': quants_key[q][0],
                    'units': quants_key[q][1]
                })
        else:
            ds[q].attrs["long_name"] = q
    return ds


def read_agg(files, file_info, parser_func, post_func=None, **kwargs):
    print("     Reading files...")
    ds_t = []
    for file in files:
        print_file_item(file)
        ds_tmp = parser_func(file, **kwargs)
        ds_tmp = lcode_append_time(ds_tmp, file)
        ds_t.append(ds_tmp)
    print("\n   Concatenating along time...")
    ds = lcode_concat_time(ds_t, files)

    # Get name of quantity and define appropriate metadata
    ds = set_quant_metadata(ds, file_info)

    if post_func is not None:
        fpath = os.path.dirname(files[0])
        ds = post_func(ds, file_info, fpath)

    return ds


def read_extrema(files, file_info):

    match = re.fullmatch(file_info.regex, files[0])
    quant = match.group(1)

    prefix = ""
    quant1 = quant + "_max"
    quant2 = quant1.replace("max", "min")

    if match.group(2) == "loc":
        quant1 = quant1 + "_loc"
        prefix = "local "

    ds = xr.Dataset(
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
        units=quant_info[file_info.type][quant][1]
    )
    ds[quant2] = ds[quant2].assign_attrs(
        long_name=prefix + "min. " + quant_info[file_info.type][quant][0], 
        units=quant_info[file_info.type][quant][1]
    )
    ds["t"] = ds["t"].assign_attrs(long_name=r"$t$", units=r"$\omega_p^{-1}$")

    return ds


def read(files, axes_lims, **kwargs):
    file_info = get_file_type(files[0])

    if file_info is None:
        raise TypeError("Could not identify the type of LCODE data file.")

    data_type = None
    match file_info.type:
        case "grid":
            if axes_lims is None:
                print(
                    "\nWARNING: axis extents were not specified. Dataset object(s) will not have any coordinates.\n"
                )
            ds = read_agg(files, file_info, read_grid_single, **kwargs)
            data_type = 'grid'

        case "lineout":
            ds = read_agg(files, file_info, read_lineout_single, post_func = read_lineout_post, **kwargs)
            data_type = 'grid'

        case "parts":
            ds = read_agg(files, file_info, read_parts_single, **kwargs)
            data_type = 'part'

        case "extrema":
            ds = read_extrema(files, file_info)
            data_type = 'grid'

        case "info" | "plzshape" | "beamfile" | "notimplemented":
            raise NotImplementedError(
                "Backend for this type of file has not been implemented yet. Exiting."
            )
        case _:
            raise TypeError(
                "Data type identified via lcode_file_key.csv is not foreseen in backend code for LCODE. This is probably an important bug."
            )

        ods = OzDataset(ds, type=data_type)

        ods = set_default_coord_metadata(ods)

        if file_info.type == 'grid' & axes_lims is not None:
            ods = ods.coords_from_extent(axes_lims)

    return ods
