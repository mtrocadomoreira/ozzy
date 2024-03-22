import dask
import h5py
import numpy as np

from .. import core as oz
from ..ozdataset import OzzyDatasetBase
from ..utils import print_file_item, stopwatch, tex_format, unpack_str

# These three variables must be defined in each backend module

general_regex_pattern = r"([\w-]+)-(\d{6})\.(h5|hdf)"
general_file_endings = ["h5"]
quants_ignore = None

# The function read() and the Methods class must also be defined in each backend module


# TODO: make compatible with part data (and different data types in general)


def config_osiris(ds):
    # Read some properties with HDF5 interface

    ax_labels = []
    ax_units = []
    ax_type = []
    xmax = []
    xmin = []
    fname = ds.encoding["source"]

    f = h5py.File(fname, "r")
    try:
        move_c = f["/SIMULATION"].attrs["MOVE C"]
    except KeyError:
        raise
    else:
        axgroups = list(f["AXIS"])
        for subgrp in axgroups:
            loc = "/AXIS/" + subgrp
            ax_labels.append(unpack_str(f[loc].attrs["LONG_NAME"]))
            ax_units.append(f[loc].attrs["UNITS"][0])
            ax_type.append(f[loc].attrs["TYPE"][0])
            xmax.append(f[loc][1])
            xmin.append(f[loc][0])
    finally:
        f.close()

    xmax = np.array(xmax)
    xmin = np.array(xmin)
    length_x1 = round((xmax[0] - xmin[0]) * 1e3) * 1e-3

    # Save data label, units and dimension info

    varname = list(ds.keys())[0]
    ds[varname] = ds[varname].assign_attrs(
        long_name=tex_format(ds.attrs["LABEL"]), units=tex_format(ds.attrs["UNITS"])
    )
    del ds.attrs["LABEL"], ds.attrs["UNITS"]

    nx = np.array(ds[varname].shape)
    ndims = len(nx)
    if ndims >= 2:
        nx[1], nx[0] = nx[0], nx[1]
    if ndims == 3:
        nx = np.roll(nx, 1)

    # Rename dimensions

    match ndims:
        case 1:
            ds = ds.rename_dims({"phony_dim_0": "x1"})
        case 2:
            ds = ds.rename_dims({"phony_dim_0": "x2", "phony_dim_1": "x1"})
        case 3:
            ds = ds.rename_dims(
                {"phony_dim_0": "x3", "phony_dim_1": "x2", "phony_dim_2": "x1"}
            )

    # Save axis values and metadata

    dx = (xmax - xmin) / nx
    dx[0] = length_x1 / nx[0]

    ax = np.arange(dx[0], length_x1 + dx[0], dx[0]) - 0.5 * dx[0]
    ds = ds.assign_coords({"x1": ax})

    for i in np.arange(1, ndims):
        coord = "x" + str(i + 1)
        ax = np.arange(xmin[i] + dx[i], xmax[i] + dx[i], dx[i]) - 0.5 * dx[i]
        ds = ds.assign_coords({coord: ax})

    for i in np.arange(0, ndims):
        coord = "x" + str(i + 1)
        ds.coords[coord].attrs["long_name"] = tex_format(ax_labels[i].decode("UTF-8"))
        ds.coords[coord].attrs["units"] = tex_format(ax_units[i].decode("UTF-8"))
        ds.coords[coord].attrs["TYPE"] = ax_type[i].decode("UTF-8")

    # Save other metadata

    ds = ds.assign_coords(
        {"t": ds.attrs["TIME"], "iter": ds.attrs["ITER"], "move_offset": xmin[0]}
    )
    ds = ds.expand_dims(dim={"t": 1}, axis=ndims)
    ds.time.attrs["units"] = tex_format(ds.attrs["TIME UNITS"])
    ds.time.attrs["long_name"] = "Time"
    ds.attrs["length_x1"] = length_x1
    ds.attrs["dx"] = dx
    ds.attrs["nx"] = nx
    ds.attrs["move_c"] = move_c

    return ds


@stopwatch
def read(files):
    for f in files:
        print_file_item(f)

    try:
        with dask.config.set({"array.slicing.split_large_chunks": True}):
            ds = oz.open_mfdataset(
                files,
                chunks="auto",
                engine="h5netcdf",
                phony_dims="access",
                preprocess=config_osiris,
                combine="by_coords",
                join="exact",
            )

    except OSError:
        ds = OzzyDatasetBase(data_origin="osiris")

    return OzzyDatasetBase(ds, data_type=ds.attrs["TYPE"])


# Defines specific methods for data from this code
class Methods: ...
