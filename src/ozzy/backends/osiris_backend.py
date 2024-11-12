# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import dask
import h5py
import numpy as np
import xarray as xr

from ..new_dataobj import new_dataset
from ..utils import print_file_item, stopwatch, tex_format, unpack_attr

general_regex_pattern = r"([\w-]+)-(\d{6})\.(h5|hdf)"
general_file_endings = ["h5"]
quants_ignore = None

# TODO: make compatible with particle track data

special_vars = {
    "ene": [r"$E_{\mathrm{kin}}$", r"$m_\mathrm{sp} c^2$"],
    "p1": [r"$p_1$", r"$m_\mathrm{sp} c$"],
    "p2": [r"$p_2$", r"$m_\mathrm{sp} c$"],
    "p3": [r"$p_3$", r"$m_\mathrm{sp} c$"],
}

type_mapping = {"particles": "part", "grid": "grid", "tracks-2": "track"}


def config_osiris(ds):
    # Convert all attributes to lower case
    original_keys = list(ds.attrs.keys())
    for item in original_keys:
        ds.attrs[item.lower()] = ds.attrs.pop(item)

    # Read attributes in SIMULATION group with HDF5 interface

    fname = ds.encoding["source"]

    try:
        f = h5py.File(fname, "r")
        for sim_attr in list(f["/SIMULATION"].attrs):
            ds.attrs[sim_attr.lower()] = unpack_attr(f["/SIMULATION"].attrs[sim_attr])

        # Read axis metadata if grid
        if ds.attrs["type"] == "grid":
            ax_labels = []
            ax_units = []
            ax_type = []
            xmin = []
            xmax = []
            for axis in list(f["AXIS"]):
                loc = "/AXIS/" + axis
                ax_labels.append(unpack_attr(f[loc].attrs["LONG_NAME"]))
                ax_units.append(unpack_attr(f[loc].attrs["UNITS"]))
                ax_type.append(unpack_attr(f[loc].attrs["TYPE"]))
                xmin.append(f[loc][0])
                xmax.append(f[loc][1])

    except KeyError:
        raise
    finally:
        f.close()

    xmax_box = np.array(ds.attrs["xmax"])
    xmin_box = np.array(ds.attrs["xmin"])
    nx = np.array(ds.attrs["nx"])

    dx = (xmax_box - xmin_box) / nx

    # Specific metadata depending on type of data

    ndims = ds.attrs["ndims"]

    # BUG: still have a problem when x1box doesn't match exactly in each time step

    match ds.attrs["type"]:
        case "grid":
            # Get variable metadata

            var = list(ds.data_vars)[0]
            ds[var] = ds[var].assign_attrs(
                long_name=tex_format(ds.attrs["label"]),
                units=tex_format(ds.attrs["units"]),
            )
            if var in special_vars:
                if special_vars[var][0] is not None:
                    ds[var].attrs["long_name"] = special_vars[var][0]
                if special_vars[var][1] is not None:
                    ds[var].attrs["units"] = special_vars[var][1]
            del ds.attrs["label"], ds.attrs["units"]

            # Rename dims

            dims = []
            for i in np.arange(ndims):
                dim_suffix = "_box" if ds.attrs["move c"][i] == 1 else ""
                dims.append("x" + str(i + 1) + dim_suffix)

            dim_suffix = [
                "_box" if ifmove == 1 else "" for ifmove in ds.attrs["move c"]
            ]
            match ndims:
                case 1:
                    ds = ds.rename_dims({"phony_dim_0": "x1" + dim_suffix[0]})

                case 2:
                    ds = ds.rename_dims(
                        {
                            "phony_dim_0": "x2" + dim_suffix[1],
                            "phony_dim_1": "x1" + dim_suffix[0],
                        }
                    )
                case 3:
                    ds = ds.rename_dims(
                        {
                            "phony_dim_0": "x3" + dim_suffix[2],
                            "phony_dim_1": "x2" + dim_suffix[1],
                            "phony_dim_2": "x1" + dim_suffix[0],
                        }
                    )

            # Read axis metadata

            for i in np.arange(0, ndims):
                coord = "x" + str(i + 1)
                ax = np.arange(xmin[i], xmax[i], dx[i]) + 0.5 * dx[i]

                if len(ax) == (ds.sizes[dims[i]] + 1):
                    ax = ax[0:-1]

                ds = ds.assign_coords({coord: (dims[i], ax)})
                ds[coord] = ds[coord].assign_attrs(
                    long_name=tex_format(ax_labels[i]),
                    units=tex_format(ax_units[i]),
                    type=ax_type[i],
                )

            # Create co-moving coordinate(s)

            for i, ifmove in enumerate(ds.attrs["move c"]):
                if ifmove:
                    coord = "x" + str(i + 1) + "_box"
                    ax = np.arange(xmin_box[i], xmax_box[i], dx[i]) + 0.5 * dx[i]
                    ds = ds.assign_coords({coord: (dims[i], ax)})

                    if i == 0:
                        new_lab = tex_format(ax_labels[i] + "- t")
                    else:
                        new_lab = tex_format(ax_labels[i]) + " (fixed)"

                    ds[coord] = ds[coord].assign_attrs(
                        long_name=new_lab,
                        units=tex_format(ax_units[i]),
                        type=ax_type[i],
                    )

        case "particles":
            # Get variable metadata

            quants_zip = zip(
                ds.attrs["quants"],
                ds.attrs["labels"],
                ds.attrs["units"],
            )

            for var, label, units in quants_zip:
                ds[var] = ds[var].assign_attrs(
                    long_name=tex_format(label), units=tex_format(units)
                )
                if var in special_vars:
                    if special_vars[var][0] is not None:
                        ds[var].attrs["long_name"] = special_vars[var][0]
                    if special_vars[var][1] is not None:
                        ds[var].attrs["units"] = special_vars[var][1]

            del ds.attrs["quants"], ds.attrs["labels"], ds.attrs["units"]

            # Rename dims
            ds = ds.rename_dims({"phony_dim_0": "pid"})

            # Check whether particles have unique pid's
            if "tag" in ds:
                # Convert two columns to single pid
                tags = ds["tag"].astype(int).to_numpy()
                dgts_right = len(str(np.max(tags[:, 1])))

                new_tags = tags[:, 1] + tags[:, 0] * 10**dgts_right

                ds = ds.assign_coords({"pid": ("pid", new_tags)})
                ds = ds.sortby("pid")
                ds.attrs["unique_pids"] = True
                ds = ds.drop_vars("tag")
            else:
                ds = ds.assign_coords({"pid": ("pid", np.arange(ds.sizes["pid"]))})
                ds.attrs["unique_pids"] = False

            # Create co-moving coordinate(s)

            for i, ifmove in enumerate(ds.attrs["move c"]):
                if ifmove:
                    og_var = "x" + str(i + 1)
                    new_var = og_var + "_box"

                    ds[new_var] = ds[og_var] - ds.attrs["time"]

                    var_symbol = ds[og_var].attrs["long_name"].strip("$")
                    if i == 0:
                        new_lab = tex_format(var_symbol + "- t")
                    else:
                        new_lab = tex_format(var_symbol) + " (fixed)"

                    ds[new_var] = ds[new_var].assign_attrs(
                        long_name=new_lab,
                        units=ds[og_var].attrs["units"],
                    )

        case "tracks-2":
            raise NotImplementedError(
                "Tracks have not been implemented in the OSIRIS backend yet"
            )
        case _:
            type_str = ds.attrs["type"]
            raise ValueError(f"Unrecognized OSIRIS data type: {type_str}")

    # Save general metadata
    ds = ds.expand_dims(dim={"t": 1}, axis=len(ds.dims))
    ds = ds.assign_coords({"t": [ds.attrs["time"]], "iter": ("t", [ds.attrs["iter"]])})
    ds["t"] = ds["t"].assign_attrs(
        long_name=r"$t$", units=tex_format(ds.attrs["time units"])
    )
    del ds.attrs["iter"], ds.attrs["time"], ds.attrs["time units"]
    ds.attrs["dx"] = dx

    return ds


@stopwatch
def read(files):
    """Read OSIRIS HDF5 data files and return a Dataset.

    Parameters
    ----------
    files : list[str]
        List of paths to OSIRIS HDF5 data files

    Returns
    -------
    xarray.Dataset
        Dataset containing the OSIRIS simulation data with appropriate coordinates and attributes

    Raises
    ------
    NotImplementedError
        If data type is `'tracks-2'` which is not yet implemented
    ValueError
        If OSIRIS data type is unrecognized
    OSError
        If no valid files are provided or files cannot be opened


    Examples
    --------

    !!! warning

        Note that you would not usually call this function directly, except in advanced use cases such as debugging. The examples below are included for completeness.

        In general, please use [ozzy's file-reading functions][reading-files] along with the backend specification instead, for example:
        ```python
        data = oz.open('osiris', 'path/to/file.h5')
        ```

    ??? example "Reading grid data files"
        ```python
        from ozzy.backends.osiris_backend import read
        files = ['charge-electrons-000000.h5', 'charge-electrons-000001.h5']
        dataset = read(files)
        # Returns Dataset with grid data
        ```

    ??? example "Reading particle data files"
        ```python
        from ozzy.backends.osiris_backend import read
        particle_files = ['RAW-electrons-000010.h5']
        dataset = read(particle_files)
        # Returns Dataset with particle data
        ```
    """

    [print_file_item(file) for file in files]

    try:
        # Check type of data
        if len(files) > 0:
            with h5py.File(files[0]) as f:
                match f.attrs["TYPE"]:
                    case b"grid":
                        join_opt = {"join": "exact"}
                    case b"particles":
                        join_opt = {"join": "outer"}
                    case b"tracks-2":
                        raise NotImplementedError(
                            "Track files have not been implemented yet, sorry."
                        )
                    case _:
                        type_str = f.attrs["TYPE"]
                        raise ValueError(f"Unrecognized OSIRIS data type: {type_str}")

            with dask.config.set({"array.slicing.split_large_chunks": True}):
                ds = xr.open_mfdataset(
                    files,
                    chunks="auto",
                    engine="h5netcdf",
                    phony_dims="access",
                    preprocess=config_osiris,
                    combine="by_coords",
                    **join_opt,
                )

            ds.attrs["pic_data_type"] = type_mapping[ds.attrs["type"]]

        else:
            raise OSError
    except OSError:
        ds = new_dataset()

    return ds


# Defines specific methods for data from this code
class Methods:
    """The methods in this class are accessible to a data object when `<data_obj>.attrs['data_origin'] == 'osiris'`.

    This class is currently empty.
    """

    ...
