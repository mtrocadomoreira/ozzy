import numpy as np
import pandas as pd
import xarray as xr
import h5py
import dask
import dask.dataframe as dd
import dask.array as da
import os
import re
from .ozzy import coords_from_extent
from .utils import stopwatch
import glob

# --- Load backend info ---

from importlib.resources import files

lcode_data_file = files("ozzy").joinpath("lcode_file_key.csv")
lcode_regex = pd.read_csv(lcode_data_file, sep=";", header=0)


# --- Helper functions ---


def get_regex_snippet(pattern, string):
    return re.search(pattern, string).group(0)


def tex_format(str):
    if str == "":
        newstr = str
    else:
        newstr = "$" + str + "$"
    return newstr


def unpack_str(attr):
    if isinstance(attr, np.ndarray):
        result = attr[0]
    else:
        result = attr
    return result


def lcode_get_rqm(ds):
    ds["q_sign"] = xr.apply_ufunc(np.sign, ds["q"], dask="allowed")
    ds["rqm"] = ds["q_sign"] * ds["abs_rqm"]
    ds["rqm"] = 1.0 / ds["rqm"]
    ds = ds.drop_vars("q_sign")

    return ds


def lcode_identify_data_type(file_string):
    for row in lcode_regex.itertuples(index=False):
        pattern = row.regex
        match = re.fullmatch(pattern, os.path.basename(file_string))
        if match is not None:
            break

    return (row, match)


def lcode_append_time(ds, file_string):
    thistime = float(get_regex_snippet(r"\d{5}", os.path.basename(file_string)))
    ds_out = ds.assign_coords({"t": [thistime]})
    ds_out.coords["t"].attrs["long_name"] = "$t$"
    ds_out.coords["t"].attrs["units"] = r"$\omega_p^{-1}$"

    return ds_out


def lcode_convert_q(ds, dxi, q_var="q", n0=None):
    # expects n0 in 1/cm^3

    print("\nConverting charge...")

    re = 2.8179403227e-13  # in cm
    if n0 is None:
        print("     - assuming dxi is in units of cm")
        factor = dxi / (2 * re)
    else:
        print("     - assuming dxi is in normalized units")
        distcm = 531760.37819 / np.sqrt(n0)
        factor = dxi * distcm / (2 * re)

    ds[q_var] = ds[q_var] * factor
    ds[q_var].attrs["units"] = "$e$"

    return ds


def dd_read_table(file, sep=r"\s+", header=None):
    ddf = dd.read_table(file, sep=sep, header=header).to_dask_array(lengths=True)
    return ddf.squeeze()


# --- Functions to pass to xarray.open_mfdataset for each file type ---


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


def config_ozzy(ds):
    if ("t" in ds.coords) & ("t" not in ds.dims):
        assert ds["t"].size == 1
        ds = ds.expand_dims(dim={"t": 1}, axis=ds[list(ds)[0]].ndim)

    return ds


def lcode_parse_parts(file, pattern_info):
    cols = ["x1", "x2", "p1", "p2", "L", "abs_rqm", "q", "pid"]
    label = [
        "$\\xi$",
        "$r$",
        "$p_z$",
        "$p_r$",
        "$L$",
        r"$|\mathrm{rqm}|$",
        "$q$",
        "pid",
    ]
    units = [
        "$k_p^{-1}$",
        "$k_p^{-1}$",
        "$m_e c$",
        "$m_e c$",
        "$m_e c^2 / \\omega_p$",
        "",
        "$e \\frac{\\Delta \\xi}{2 \\: r_e}$",
        "",
    ]

    if pattern_info.subcat == "lost":
        cols = ["t"] + cols
        units = [r"$\omega_p^{-1}$"] + units
        label = ["$t$"] + label

    arr = np.fromfile(file).reshape(-1, len(cols))
    dda = da.from_array(arr[0:-1, :])

    data_vars = {}
    for i, var in enumerate(cols[0:-1]):
        data_vars[var] = ("pid", dda[:, i], {"long_name": label[i], "units": units[i]})

    ds = xr.Dataset(data_vars).assign_coords({"pid": dda[:, -1]})
    ds.coords["pid"].attrs["long_name"] = label[-1]
    ds.coords["pid"].attrs["units"] = units[-1]
    if pattern_info.subcat != "lost":
        ds = ds.expand_dims(dim={"t": 1}, axis=1)

    return ds


def lcode_parse_grid(file, pattern_info, match):
    with dask.config.set({"array.slicing.split_large_chunks": True}):
        ddf = dd_read_table(file)
        # ddf = dd.read_table(file, sep=r'\s+', header=None)\
        #     .to_dask_array(lengths=True)
        # ddf = ddf.squeeze()

    if pattern_info.subcat == "alongz":
        quant = match.group(1)

        label = {"e": "$E_z$", "g": r"$\phi$"}
        units = {"e": "$E_0$", "g": "$m c^2 / e$"}
        prefix = ""
        quant1 = quant + "_max"
        quant2 = quant1.replace("max", "min")

        if match.group(2) == "loc":
            quant1 = quant1 + "_loc"
            prefix = "local "

        xds = xr.Dataset(
            data_vars={
                quant1: ("t", ddf[:, 1]),
                quant2: ("t", ddf[:, 3]),
                "ximax": ("t", ddf[:, 2]),
                "ximin": ("t", ddf[:, 4]),
            },
            coords={"t": ddf[:, 0]},
        )

        xds[quant1] = xds[quant1].assign_attrs(
            long_name=prefix + "max. " + label[quant], units=units[quant]
        )
        xds[quant2] = xds[quant2].assign_attrs(
            long_name=prefix + "min. " + label[quant], units=units[quant]
        )
        xds["t"] = xds["t"].assign_attrs(long_name=r"$t$", units=r"$\omega_p^{-1}$")

    elif pattern_info.subcat == "plzshape":
        xds = xr.Dataset(data_vars={"np": ("t", ddf[:, 1])}, coords={"t": ddf[:, 0]})

        xds["np"] = xds["np"].assign_attrs(long_name=r"$n_p$", units=r"$n_0$")
        xds["t"] = xds["t"].assign_attrs(long_name=r"$t$", units=r"$\omega_p^{-1}$")

    else:
        quant = match.group(1)

        ndims = ddf.ndim
        match ndims:
            case 1:
                dims = ["x1"]
                ddf = np.flip(ddf, axis=0)

                timestr = get_regex_snippet(r"\d{5}", os.path.basename(file))
                xifile = glob.glob(
                    os.path.join(os.path.dirname(file), "xi_" + timestr + ".swp")
                )
                xiddf = dd_read_table(xifile)

                # look for xi axis file and add it
                # check whether on axis or off axis
            case 2:
                dims = ["x2", "x1"]
                ddf = ddf.transpose()
                ddf = np.flip(ddf, axis=1)
            case _:
                raise Exception("Invalid number of dimensions in file " + file)

        xds = xr.Dataset(data_vars={quant: (dims, ddf)}).expand_dims(
            dim={"t": 1}, axis=ndims
        )

        xds[quant].attrs["long_name"] = quant
        xds.attrs["ndims"] = ndims

        # add units and label to coordinates

    return xds


@stopwatch
def lcode_concat_time(ds, files):
    ds = xr.concat(ds, "t", fill_value={"q": 0.0})
    ds.coords["t"].attrs["long_name"] = "$t$"
    ds.coords["t"].attrs["units"] = r"$\omega_p^{-1}$"
    ds = ds.sortby("t")
    ds.attrs["source"] = os.path.commonpath(files)
    ds.attrs["files_prefix"] = os.path.commonprefix(
        [os.path.basename(f) for f in files]
    )

    return ds


def read_lcode_parts(files, pattern_info, as_series=True):
    print("Reading files...")

    ds_t = []
    for file in files:
        print("  - " + file)

        ds_tmp = lcode_parse_parts(file, pattern_info)

        if pattern_info.subcat == "beamfile":
            bfbit_path = os.path.join(os.path.dirname(file), "beamfile.bit")
            if os.path.exists(bfbit_path):
                with open(bfbit_path, "r") as f:
                    thistime = float(f.read())
                ds_tmp = ds_tmp.assign_coords({"t": [thistime]})

        elif pattern_info.subcat != "lost":
            ds_tmp = lcode_append_time(ds_tmp, file)

        ds_t.append(ds_tmp)

    # Get file type of all files so as to allow mix between
    # beamfile and tb*.swp
    subcat_all = [lcode_identify_data_type(f)[0].subcat for f in files]

    if any([(sc == "parts") | (sc == "species") for sc in subcat_all]) & (
        as_series is True
    ):
        print(
            "\nConcatenating along time... \
            (this may take a while for particle data)"
        )
        # t0 = time.process_time()
        ds = lcode_concat_time(ds_t, files)
        # print(" -> Took " + str(time.process_time() - t0) + " s")
    else:
        assert len(ds_t) == 1
        ds = ds_t[0]

    return ds


def read_lcode_grid(files, as_series, pattern_info, match, axes_lims):
    print("Reading files...")

    ds_t = []
    for file in files:
        print("  - " + file)
        ds_tmp = lcode_parse_grid(file, pattern_info, match)

        if pattern_info.time == "single":
            ds_tmp = lcode_append_time(ds_tmp, file)

        ds_t.append(ds_tmp)

    if (not as_series) | (pattern_info.time == "full"):
        assert len(ds_t) == 1
        ds = ds_t[0]

    else:
        print("\nConcatenating along time...")
        # t0 = time.process_time()
        ds = lcode_concat_time(ds_t, files)
        # print(" -> Took " + str(time.process_time() - t0) + " s")

    if axes_lims is not None:
        ds = coords_from_extent(ds, axes_lims)

    return ds


# --- Main functions ---


def read_ozzy(files, as_series):
    if len(files) != 0:
        print("Reading files...")

        try:
            with dask.config.set({"array.slicing.split_large_chunks": True}):
                ds = xr.open_mfdataset(files, chunks="auto", engine="h5netcdf")
            for file in files:
                print("  - " + file)

        except Exception:
            ds_t = []
            for file in files:
                print("  - " + file)
                with dask.config.set({"array.slicing.split_large_chunks": True}):
                    ds_tmp = xr.open_dataset(file, engine="h5netcdf", chunks="auto")
                ds_t.append(config_ozzy(ds_tmp))
            print("\nConcatenating along time... (this may take a while)")
            ds = xr.concat(ds_t, "t", fill_value={"q": 0.0})

        ds.attrs["source"] = os.path.commonpath(files)
        ds.attrs["files_prefix"] = os.path.commonprefix(
            [os.path.basename(f) for f in files]
        )

    else:
        ds = xr.Dataset()

    return ds


def read_lcode(files, as_series, axes_lims):
    # assuming files is already sorted into a single type
    # of data (no different kinds of files)

    pattern_info, match = lcode_identify_data_type(files[0])

    if match is None:
        raise Exception("Error: could not identify the type of LCODE data file.")

    match pattern_info.cat:
        case "grid":
            if axes_lims is None:
                print(
                    "\nWARNING: axis extents were not specified. \
                        Dataset object(s) will not have coordinates.\n"
                )
            ds = read_lcode_grid(files, as_series, pattern_info, match, axes_lims)

        case "parts":
            ds = read_lcode_parts(files, pattern_info, as_series)

        case "info":
            print(
                "Error: Backend for this type of file has not been \
                    implemented yet. Exiting."
            )
            return

        case "uncat":
            print(
                "Error: Backend for this type of file has not been \
                    implemented yet. Exiting."
            )
            return

    return ds


@stopwatch
def read_osiris(files, as_series):
    print("\nReading and concatenating the following files:")
    for f in files:
        print("  - " + f)

    # t0 = time.process_time()

    if as_series is False:
        assert len(files) == 1

    try:
        with dask.config.set({"array.slicing.split_large_chunks": True}):
            ds = xr.open_mfdataset(
                files,
                chunks="auto",
                engine="h5netcdf",
                phony_dims="access",
                preprocess=config_osiris,
                combine="by_coords",
                join="exact",
            )

        ds.attrs["source"] = os.path.commonpath(files)
        ds.attrs["files_prefix"] = os.path.commonprefix(
            [os.path.basename(f) for f in files]
        )

    except OSError:
        ds = xr.Dataset()

    # print(" -> Took " + str(time.process_time() - t0) + " s")

    return ds


def get_file_pattern(file_type):
    match file_type:
        case "osiris":
            fend = ["h5"]
            re_pat = r"([\w-]+)-(\d{6})\.(h5|hdf)"
        case "lcode":
            fend = ["swp", "dat", "det", "bin", "bit", "pls"]
            re_pat = r"([\w-]*?)(\d{5}|\d{6}\.\d{3})?[m|w]?\.([a-z]{3})"
        case "ozzy":
            fend = ["h5", "nc"]
            re_pat = r"([\w-]*?)(\d{5}|\d{6})\.(h5|nc)"
        case "openpmd" | "hipace":
            fend = ["json"]
            re_pat = r"([\w]*)_(\d{6})\.(json)"
        case _:
            raise Exception('Error: invalid input for "file_type" keyword')

    return (fend, re_pat)


def read(filepaths, file_type, as_series=True, axes_lims=None):
    match file_type:
        case "osiris":
            ds = read_osiris(filepaths, as_series)
        case "lcode":
            ds = read_lcode(filepaths, as_series, axes_lims)
        case "ozzy":
            ds = read_ozzy(filepaths, as_series)
        case _:
            raise Exception('Error: invalid input for "file_type" keyword')

    return ds
