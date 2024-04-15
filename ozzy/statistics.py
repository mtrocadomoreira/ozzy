import os

import numpy as np
import xarray as xr

from .new_dataobj import new_dataset
from .utils import stopwatch

# TODO: write docstrings


def _check_raw_and_grid(raw_ds, grid_ds):
    if (
        "part"
        not in raw_ds.attrs["pic_data_type"] | "grid"
        not in grid_ds.attrs["pic_data_type"]
    ):
        raise ValueError(
            "First argument must be a dataset containing particle data and second argument must be a dataset containing grid data"
        )


def _check_n0_input(n0, xi_var):
    if (n0 is not None) & (xi_var is None):
        raise ValueError("Name of xi variable must be provided when n0 is provided")
    elif (n0 is not None) & (xi_var is not None):
        raise Warning("Assuming the xi axis is in normalized units.")


def _define_q_units(n0, xi_var, dens_ds):
    match dens_ds.attrs["data_origin"]:
        case "lcode":
            if n0 is None:
                units_str = r"$e \frac{\Delta \xi}{2 \: r_e} k_p^2$"
            else:
                dxi = dens_ds[xi_var].to_numpy()[1] - dens_ds[xi_var].to_numpy()[0]
                dens_ds.ozzy.convert_q(dxi, q_var="nb", n0=n0)
                units_str = r"$e \: k_p^2$"
        case _:
            units_str = "a.u."
    return units_str


@stopwatch
def parts_into_grid(
    raw_ds,
    axes_ds,
    time_dim: str = "t",
    weight_var: str = "q",
    r_var: str | None = None,
    n0: float | None = None,
    xi_var: str | None = None,
):
    _check_raw_and_grid(raw_ds, axes_ds)

    _check_n0_input(n0, xi_var)

    spatial_dims = axes_ds.ozzy.get_space_dims(time_dim)
    if len(spatial_dims) == 0:
        raise KeyError("Did not find any spatial dimensions in input axes dataset")

    bin_edges = axes_ds.ozzy.get_bin_edges(time_dim)

    q_binned = []

    # Multiply weight by radius, if r_var is specified

    if r_var is None:
        wvar = weight_var
    else:
        raw_ds["w"] = raw_ds[weight_var] / raw_ds[r_var]
        wvar = "w"

    # Loop along time

    for i in np.arange(0, len(raw_ds[time_dim])):
        ds_i = raw_ds.isel({time_dim: i})

        part_coords = [ds_i[var] for var in spatial_dims]
        dist, edges = np.histogramdd(part_coords, bins=bin_edges, weights=ds_i[wvar])

        newcoords = {var: axes_ds[var] for var in spatial_dims}
        newcoords[time_dim] = ds_i[time_dim]
        qds_i = new_dataset(
            data_vars={"nb": (spatial_dims, dist)},
            coords=newcoords,
            pic_data_type="grid",
            data_origin=raw_ds.attrs["data_origin"],
        )
        q_binned.append(qds_i)

    parts = xr.concat(q_binned, time_dim)

    units_str = _define_q_units(n0, xi_var, parts)

    parts["nb"] = parts["nb"].assign_attrs({"long_name": r"$\rho$", "units": units_str})

    for var in parts.coords:
        parts.coords[var] = parts.coords[var].assign_attrs(axes_ds[var].attrs)

    return parts


@stopwatch
def charge_in_field_quadrants(
    raw_ds,
    fields_ds,
    time_dim="t",
    savepath=os.getcwd(),
    outfile="charge_in_field_quadrants.nc",
    weight_var="q",
    n0=None,
    xi_var=None,
):
    # Check type of input

    _check_raw_and_grid(raw_ds, fields_ds)

    axes_ds = new_dataset(fields_ds.coords)

    # Bin particles

    print("\nBinning particles into a grid...")

    # No rvar because we want absolute charge, not density
    parts = parts_into_grid(raw_ds, axes_ds, time_dim, weight_var, r_var=None)

    _check_n0_input(n0, xi_var)

    # units_str = _define_q_units(n0, xi_var, parts)

    # Select subsets of the fields

    print("\nMatching particle distribution with sign of fields:")

    spatial_dims = axes_ds.ozzy.get_space_dims(time_dim)
    fld_vars = list(fields_ds.data_vars)
    summed = []

    conditions = {
        "pospos": (fields_ds[fld_vars[0]] >= 0.0) & (fields_ds[fld_vars[1]] >= 0.0),
        "posneg": (fields_ds[fld_vars[0]] >= 0.0) & (fields_ds[fld_vars[1]] < 0.0),
        "negpos": (fields_ds[fld_vars[0]] < 0.0) & (fields_ds[fld_vars[1]] >= 0.0),
        "negneg": (fields_ds[fld_vars[0]] < 0.0) & (fields_ds[fld_vars[1]] < 0.0),
    }

    newdims = {
        "pospos": {fld_vars[0] + "_sign": [1.0], fld_vars[1] + "_sign": [1.0]},
        "posneg": {fld_vars[0] + "_sign": [1.0], fld_vars[1] + "_sign": [-1.0]},
        "negpos": {fld_vars[0] + "_sign": [-1.0], fld_vars[1] + "_sign": [1.0]},
        "negneg": {fld_vars[0] + "_sign": [-1.0], fld_vars[1] + "_sign": [-1.0]},
    }

    for case, cond in conditions.items():
        print("     - case: " + case)

        fld1_sel = fields_ds[fld_vars[0]].where(cond.compute(), drop=True)
        fld2_sel = fields_ds[fld_vars[1]].where(cond.compute(), drop=True)

        w_prll = abs(fld1_sel * parts["nb"]).sum(dim=spatial_dims, skipna=True)
        w_perp = abs(fld2_sel * parts["nb"]).sum(dim=spatial_dims, skipna=True)
        w_both = w_prll + w_perp

        # Set metadata

        ndims = w_prll.ndim

        w_prll = w_prll.expand_dims(dim=newdims[case], axis=[ndims, ndims + 1])
        w_perp = w_perp.expand_dims(dim=newdims[case], axis=[ndims, ndims + 1])
        w_both = w_both.expand_dims(dim=newdims[case], axis=[ndims, ndims + 1])

        w_prll.name = "W in " + fld_vars[0]
        w_perp.name = "W in " + fld_vars[1]
        w_both.name = "Wtot"

        summed = summed + [w_prll, w_perp, w_both]

    charge_ds = xr.merge(summed)

    charge_ds[w_prll.name].attrs["long_name"] = (
        r"$W$ in " + fields_ds[fld_vars[0].attrs["long_name"]]
    )
    charge_ds[w_perp.name].attrs["long_name"] = (
        r"$W$ in " + fields_ds[fld_vars[1].attrs["long_name"]]
    )
    charge_ds[w_both.name].attrs["long_name"] = r"$W_\mathrm{tot}$"

    for var in charge_ds.data_vars:
        charge_ds[var].attrs["units"] = "a.u."

    # Save data

    print("\nSaving data...")

    filepath = os.path.join(savepath, outfile)
    charge_ds.ozzy.save(filepath)

    print("\nDone!")

    return


def field_space(raw_ds, fields_ds, spatial_dims=["x1", "x2"]):
    # CAVEAT: assumes that second element of spatial_dims is the vertical dimension
    # Check that datasets do not have time dimension

    t_in_fields = "t" in fields_ds.dims
    t_in_parts = "t" in raw_ds.dims
    if t_in_fields | t_in_parts:
        raise ValueError(
            "This function does not allow a time dimension. Reduce dimension of dataset with sel() or isel() first."
        )

    _check_raw_and_grid(raw_ds, fields_ds)

    # Attribute grid cell index to each particle

    for dim in spatial_dims:
        axis = fields_ds.coords[dim].to_numpy()
        dx = axis[1] - axis[0]
        raw_ds[dim + "_i"] = np.floor(abs(raw_ds[dim]) / dx)

    arr_shape = fields_ds[list(fields_ds)[0]].to_numpy().shape
    raw_ds["x_ij"] = np.ravel_multi_index(
        (
            raw_ds[spatial_dims[1] + "_i"].astype(int),
            raw_ds[spatial_dims[0] + "_i"].astype(int),
        ),
        arr_shape,
    )

    raw_ds = raw_ds.drop_vars([dim + "_i" for dim in spatial_dims])

    # Read field values

    for fvar in fields_ds.data_vars:
        da_tmp = xr.DataArray(
            fields_ds[fvar].to_numpy().flat[raw_ds["x_ij"].to_numpy()],
            dims="pid",
            attrs=fields_ds[fvar].attrs,
        )
        raw_ds[fvar] = da_tmp

    return raw_ds
