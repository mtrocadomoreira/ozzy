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

# HACK: add function to get histogram (counts or otherwise) as function of axes_ds object
# e.g. example for counts:
# def get_histogram(da, ax_da, tvar = 't'):
#     bin_edges = ax_da.ozzy.get_bin_edges(tvar)
#     data = [da.to_numpy()]
#     dist, edges = np.histogramdd(data, bins=bin_edges, weights=np.ones(data[0].shape))
#     return dist


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
    r"""
    Check if the `xi_var` is provided when `n0` is provided.

    Parameters
    ----------
    n0 : float | None
        Reference density value.
    xi_var : str | None
        Name of the variable representing the $\xi$ axis.

    Raises
    ------
    ValueError
        If `n0` is provided but `xi_var` is not.

    Notes
    -----
    If `n0` and `xi_var` are both provided, a warning is printed assuming the $\xi$ axis is in normalized units.
    """
    if (n0 is not None) & (xi_var is None):
        raise ValueError("Name of xi variable must be provided when n0 is provided")
    elif (n0 is not None) & (xi_var is not None):
        print("WARNING: Assuming the xi axis is in normalized units.")


# TODO: may need to update this based on tests of LCODE charge definitions
def _define_q_units(n0, xi_var, dens_ds):
    """
    Define the units for the charge density based on the data origin and input parameters.

    Parameters
    ----------
    n0 : float | None
        Reference density value.
    xi_var : str | None
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


def _define_q_units_general(raw_sdims, rvar_attrs: dict | None):
    if all("units" in raw_sdims[each].attrs for each in raw_sdims.data_vars):
        ustrings = [
            raw_sdims[each].attrs["units"].strip("$") for each in raw_sdims.data_vars
        ]
        extra = ""
        for ustr in ustrings:
            extra += rf"/ {ustr}"
        if rvar_attrs is not None:
            extra += rf"/ {rvar_attrs["units"].strip("$")}"
        units_str = rf"$Q_w {extra}$"
    else:
        units_str = "a.u."
    return units_str


# TODO: add example (perhaps using sample data?)
# TODO: remove use of n0 and charge unit conversion
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
    n0 : float | None, optional
        Reference plasma density value, in $\mathrm{cm}^{-3}$. If provided, the charge is converted to physical units. Default is None.
    xi_var : str | None, optional
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
    parts = raw_ds.ozzy.bin_into_grid(axes_ds, time_dim, weight_var, r_var=None)

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


# TODO: add example (perhaps using sample data?)
def field_space(raw_ds, fields_ds, spatial_dims=["x1", "x2"]):
    """
    Get values of fields in the cell where each particle is located (no interpolation is done).

    Parameters
    ----------
    raw_ds : xarray.Dataset
        Dataset containing particle data.
    fields_ds : xarray.Dataset
        Dataset containing field data.
    spatial_dims : list[str], optional
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

    # HACK: assumes that second element of spatial_dims is the vertical dimension, maybe could generalize

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
