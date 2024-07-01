# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

"""
The statistics submodule encompasses functions that process particle data or otherwise synthesize data into lower-dimensional measures. A classic example is getting the centroid (mean transverse position) of a particle distribution.

"""

import numpy as np
import xarray as xr

from .new_dataobj import new_dataset
from .utils import stopwatch


def _check_raw_and_grid(raw_ds, grid_ds):
    """
    Check if the input datasets contain particle and grid data, respectively.

    Parameters
    ----------
    raw_ds : xarray.Dataset
        Dataset containing particle data.
    grid_ds : xarray.Dataset
        Dataset containing grid data.

    Raises
    ------
    ValueError
        If the input datasets do not contain particle and grid data, respectively.
    """
    if ("part" not in raw_ds.attrs["pic_data_type"]) | (
        "grid" not in grid_ds.attrs["pic_data_type"]
    ):
        raise ValueError(
            "First argument must be a dataset containing particle data and second argument must be a dataset containing grid data"
        )


def _check_n0_input(n0, xi_var):
    """
    Check if the `xi_var` is provided when `n0` is provided.

    Parameters
    ----------
    n0 : float or None
        Reference density value.
    xi_var : str or None
        Name of the variable representing the xi axis.

    Raises
    ------
    ValueError
        If `n0` is provided but `xi_var` is not.

    Notes
    -----
    If `n0` and `xi_var` are both provided, a warning is printed assuming the xi axis is in normalized units.
    """
    if (n0 is not None) & (xi_var is None):
        raise ValueError("Name of xi variable must be provided when n0 is provided")
    elif (n0 is not None) & (xi_var is not None):
        print("WARNING: Assuming the xi axis is in normalized units.")


def _define_q_units(n0, xi_var, dens_ds):
    """
    Define the units for the charge density based on the data origin and input parameters.

    Parameters
    ----------
    n0 : float or None
        Reference density value.
    xi_var : str or None
        Name of the variable representing the xi axis.
    dens_ds : xarray.Dataset
        Dataset containing density data.

    Returns
    -------
    units_str : str
        String representing the units for the charge density.
    """
    match dens_ds.attrs["data_origin"]:
        case "lcode":
            if n0 is None:
                units_str = r"$e \frac{\Delta \xi}{2 \: r_e} k_p^2$"
            else:
                dxi = dens_ds[xi_var].to_numpy()[1] - dens_ds[xi_var].to_numpy()[0]
                dens_ds.ozzy.convert_q(dxi, q_var="nb", n0=n0)
                units_str = r"$e \: k_p^2$"
        # TODO: add charge unit calculation for other codes
        case _:
            units_str = "a.u."
    return units_str


# TODO: add example (perhaps using sample data?)
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
    r"""
    Bin particle data into a grid (charge density distribution).

    Parameters
    ----------
    raw_ds : xarray.Dataset
        Dataset containing particle data.
    axes_ds : xarray.Dataset
        Dataset containing grid axes information.

        ??? tip
            The axis information can be easily obtained from a grid dataset (for example field data) with
            ```python
            axes_ds = fields_ds.coords
            ```

    time_dim : str, optional
        Name of the time dimension in the input datasets. Default is `'t'`.
    weight_var : str, optional
        Name of the variable representing particle weights or particle charge in `raw_ds`. Default is `'q'`.
    r_var : str or None, optional
        Name of the variable representing particle radial positions. If provided, the particle weights are divided by this variable. Default is None.
    n0 : float or None, optional
        Reference plasma density value, in $\mathrm{cm}^{-3}$. If provided, the charge density is converted to physical units. Default is None.
    xi_var : str or None, optional
        Name of the variable representing the longitudinal axis. Required if `n0` is provided.

    Returns
    -------
    parts : xarray.Dataset
        Dataset containing the charge density distribution on the grid.

    Raises
    ------
    KeyError
        If no spatial dimensions are found in the input `axes_ds`.
    ValueError
        If the input datasets do not contain particle and grid data, respectively, or if `n0` is provided but `xi_var` is not.
    """
    _check_raw_and_grid(raw_ds, axes_ds)

    _check_n0_input(n0, xi_var)

    # TODO: change this error message; dims might not be space dims (e.g. phase space)
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
        if var in axes_ds:
            parts.coords[var] = parts.coords[var].assign_attrs(axes_ds[var].attrs)

    return parts


# TODO: add example (perhaps using sample data?)
@stopwatch
def charge_in_field_quadrants(
    raw_ds,
    fields_ds,
    time_dim="t",
    weight_var="q",
    n0=None,
    xi_var=None,
):
    r"""
    Calculate the amount of charge in different quadrants of the "field space". By quadrants we mean the four possible combinations of positive/negative longitudinal fields and positive/negative transverse fields.


    Parameters
    ----------
    raw_ds : xarray.Dataset
        Dataset containing particle data.
    fields_ds : xarray.Dataset
        Dataset containing field data.
        !!! warning
            This function expects the `fields_ds` argument to be a dataset containing two variables, one of which corresponds to a longitudinal field/force and the other to a transverse field/force.
    time_dim : str, optional
        Name of the time dimension in the input datasets. Default is `'t'`.
    weight_var : str, optional
        Name of the variable representing particle weights or particle charge in `raw_ds`. Default is `'q'`.
    n0 : float or None, optional
        Reference plasma density value, in $\mathrm{cm}^{-3}$. If provided, the charge is converted to physical units. Default is None.
    xi_var : str or None, optional
        Name of the variable representing the longitudinal axis. Required if `n0` is provided.

    Returns
    -------
    charge_ds : xarray.Dataset
        Dataset containing the charge in different quadrants of the "field space".

    Raises
    ------
    ValueError
        If the input datasets do not contain particle and grid data, respectively, or if `n0` is provided but `xi_var` is not.

    """

    # Check type of input

    _check_raw_and_grid(raw_ds, fields_ds)

    axes_ds = new_dataset(fields_ds.coords, pic_data_type="grid")

    # Bin particles

    print("\nBinning particles into a grid...")

    # No rvar because we want absolute charge, not density
    parts = parts_into_grid(raw_ds, axes_ds, time_dim, weight_var, r_var=None)

    _check_n0_input(n0, xi_var)

    units_str = _define_q_units(n0, xi_var, parts)

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

        nb_sel = parts["nb"].where(cond.compute(), drop=True)
        q_quad = nb_sel.sum(dim=spatial_dims, skipna=True)

        # Set metadata

        ndims = q_quad.ndim
        q_quad = q_quad.expand_dims(dim=newdims[case], axis=[ndims, ndims + 1])
        q_quad.name = "Q"
        summed = summed + [q_quad]

    charge_ds = xr.merge(summed)

    charge_ds[q_quad.name].attrs["long_name"] = r"$Q$"
    charge_ds[q_quad.name].attrs["long_name"] = units_str

    charge_ds.attrs["pic_data_type"] = "grid"
    charge_ds.attrs["data_origin"] = "ozzy"

    return charge_ds


# TODO: rewrite docstring. warn about NO INTERPOLATION
# TODO: add example (perhaps using sample data?)
def field_space(raw_ds, fields_ds, spatial_dims=["x1", "x2"]):
    """
    Interpolate field values at particle positions.

    Parameters
    ----------
    raw_ds : xarray.Dataset
        Dataset containing particle data.
    fields_ds : xarray.Dataset
        Dataset containing field data.
    spatial_dims : list of str, optional
        List of spatial dimension names in the input datasets. Default is `['x1', 'x2']`.

    Returns
    -------
    raw_ds : xarray.Dataset
        Dataset containing particle data with interpolated field values.

    Raises
    ------
    ValueError
        If the input datasets contain a time dimension, or if the input datasets do not contain particle and grid data, respectively.

    Warning
    -------
    This function assumes that the second element of `spatial_dims` is the vertical dimension.

    """

    # BUG: (warning) assumes that second element of spatial_dims is the vertical dimension

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

    # Drop nans

    raw_ds = raw_ds.dropna(dim="pid", subset=[dim + "_i" for dim in spatial_dims])

    # Get flat indices

    arr_shape = fields_ds[list(fields_ds)[0]].to_numpy().shape
    inds_flat = np.ravel_multi_index(
        (
            raw_ds[spatial_dims[1] + "_i"].data.astype(int),
            raw_ds[spatial_dims[0] + "_i"].data.astype(int),
        ),
        arr_shape,
    )
    raw_ds = raw_ds.assign(x_ij=xr.DataArray(inds_flat, dims="pid"))
    raw_ds = raw_ds.drop_vars([dim + "_i" for dim in spatial_dims])

    # Read field values

    for fvar in fields_ds.data_vars:
        da_tmp = xr.DataArray(
            fields_ds[fvar].to_numpy().flat[raw_ds["x_ij"].to_numpy()],
            dims="pid",
            attrs=fields_ds[fvar].attrs,
        )
        raw_ds[fvar] = da_tmp

    raw_ds = raw_ds.drop_vars("x_ij")

    return raw_ds
