import os
import numpy as np
import xarray as xr
from . import ozzy as oz
from . import backends as ozbk
from flox.xarray import xarray_reduce
import time

# --- Helper functions ---


def get_space_dims(ds, time_dim="t"):
    return list(set(list(ds.coords)) - {time_dim})


def bins_from_axis(axis):
    vmin = axis[0] - 0.5 * (axis[1] - axis[0])
    binaxis = axis + 0.5 * (axis[1] - axis[0])
    binaxis = np.insert(binaxis, 0, vmin)
    return binaxis


def bin_edges_from_ds(axes_ds, time_dim="t"):
    bin_edges = []
    for axis in get_space_dims(axes_ds, time_dim):
        axis_arr = np.array(axes_ds[axis])
        bin_edges.append(bins_from_axis(axis_arr))
    return bin_edges


# --- Actual functions ---


def mean_rms_grid(xda, dims, savepath=os.getcwd(), outfile=None):
    # new xr dataset: same dims as xda, except dims in keyword
    # name of quantity 'quant_rms'
    # same units

    return


def parts_into_grid(
    raw_ds, axes_ds, time_dim="t", weight_var="q", r_var=None, n0=None, xi_var=None
):
    # assumes that axis is normalized when n0 and xi_var are provided

    if (n0 is not None) & (xi_var is None):
        raise Exception("Name of xi variable must be provided when n0 is provided.")

    spatial_dims = get_space_dims(axes_ds, time_dim)
    if len(spatial_dims) == 0:
        raise Exception("Did not find any spatial dimensions in input axes dataset")

    bin_edges = bin_edges_from_ds(axes_ds, time_dim)

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
        qds_i = xr.Dataset(data_vars={"nb": (spatial_dims, dist)}, coords=newcoords)
        q_binned.append(qds_i)

    parts = xr.concat(q_binned, time_dim)
    parts["nb"].attrs["long_name"] = r"$\rho$"

    if n0 is None:
        parts["nb"].attrs["units"] = r"$e \frac{\Delta \xi}{2 \: r_e} k_p^2$"
    else:
        dxi = axes_ds[xi_var].to_numpy()[1] - axes_ds[xi_var].to_numpy()[0]
        parts = ozbk.lcode_convert_q(parts, dxi, q_var="nb", n0=n0)
        parts["nb"].attrs["units"] = r"$e \: k_p^2$"

    for var in parts.coords:
        parts.coords[var].assign_attrs(axes_ds[var].attrs)

    return parts


def get_phase_space(raw_ds, vars, extents=None, nbins=200):
    # Define extent and nbins depending on input

    if extents is None:
        extents = {}
        for v in vars:
            maxval = float(raw_ds[v].max().compute().to_numpy())
            minval = float(raw_ds[v].min().compute().to_numpy())
            if (minval < 0) & (maxval > 0):
                extr = max([abs(minval), maxval])
                lims = (-extr, extr)
            else:
                lims = (minval, maxval)
            extents[v] = lims
    else:
        assert extents is dict

    if nbins is int:
        bins = {}
        for v in vars:
            bins[v] = nbins
    else:
        assert nbins is dict
        bins = nbins

    # Prepare axes dataset

    axes_ds = xr.Dataset()
    for v in vars:
        ax = oz.axis_from_extent(bins[v], extents[v])
        axes_ds = axes_ds.assign_coords({v: ax})
        axes_ds[v].attrs.update(raw_ds[v].attrs)

    # Deposit quantities on phase space grid

    ps = parts_into_grid(raw_ds, axes_ds)

    # Change metadata

    ps = ps.rename_vars({"nb": "Q"})
    ps["Q"].attrs["units"] = r"a.u."
    ps["Q"].attrs["long_name"] = r"$Q$"

    return ps


def mean_std_raw(
    xds,
    dim,
    binned_axis,
    savepath=os.getcwd(),
    outfile=None,
    expand_time=True,
    axisym=False,
):
    print("\nPreparing...")

    if isinstance(dim, list):
        if len(dim) == 1:
            dim = dim[0]
        else:
            raise Exception('Keyword "dim" must be one single dimension')

    # Check if dimension(s) exists in dataset
    if dim not in xds.data_vars:
        print('Error: dimension "' + dim + '" not found in dataset.')
        raise Exception("Could not find dimension to perform operation along.")

    # Check if dimension(s) in input "binned_axis" = xarray.DataArray exist
    # in input dataset "xds" = xarray.Dataset

    if isinstance(binned_axis, xr.DataArray):
        binned_axis = binned_axis.to_dataset()

    problem = 0
    for out_dim in binned_axis.data_vars:
        if out_dim not in xds.data_vars:
            print(
                'Error: output dimension "'
                + out_dim
                + '" could not be found in input dataset.'
            )
            problem = problem + 1
    if problem > 0:
        raise Exception("Problem matching output dim(s) with input dim(s).")

    # Prepare binning array

    bin_arr = []
    bin_vars = []
    bin_axes = []
    problem = 0

    try:
        for var in binned_axis.data_vars:
            axis = np.array(binned_axis[var])
            bin_axes.append(axis)
            bin_arr.append(bins_from_axis(axis))
            bin_vars.append(var)
    except AttributeError:
        print(
            'Error: Was expecting the keyword "binned_axis" \
            to be either an xarray.DataArray or an xarray.Dataset'
        )
        raise

    # Prepare dataset for calculation

    ds = xds[bin_vars + [dim, "q"]]
    ds[dim + "_sqw"] = (ds[dim] ** 2) * ds["q"]
    if axisym is False:
        ds[dim + "_w"] = ds[dim] * ds["q"]
    ds = ds.drop_vars(["q", dim])

    # Determine bin index for each particle (and for each binning variable)

    for i, bvar in enumerate(bin_vars):
        group_id = np.digitize(ds[bvar].isel(t=0), bin_arr[i])
        group_labels = [bin_axes[i][j] for j in group_id]
        ds = ds.assign_coords({bvar + "_bin": ("pid", group_labels)})

    # Perform mean along the dataset and get final variables

    print("\nCalculating mean and standard deviation...")

    by_dims = [ds[key] for key in ds.coords if "_bin" in key]

    result = ds
    for dim_da in by_dims:
        try:
            result = xarray_reduce(
                result,
                dim_da,
                func="mean",
                sort=True,
                dim="pid",
                keep_attrs=True,
                fill_value=np.nan,
            )
        except Exception:
            print(
                "This is probably a problem with the multiple binning axes. \
                    Have to look over this."
            )
            raise

    if axisym is False:
        result[dim + "_std"] = np.sqrt(result[dim + "_sqw"] - result[dim + "_w"] ** 2)
        result = result.rename({dim + "_w": dim + "_mean"})

        result[dim + "_mean"] = result[dim + "_mean"].assign_attrs(
            long_name="mean(" + xds[dim].attrs["long_name"] + ")",
            units=xds[dim].attrs["units"],
        )
    else:
        result[dim + "_std"] = np.sqrt(result[dim + "_sqw"])

    result[dim + "_std"] = result[dim + "_std"].assign_attrs(
        long_name="std(" + xds[dim].attrs["long_name"] + ")",
        units=xds[dim].attrs["units"],
    )
    result = result.drop_vars(dim + "_sqw")

    # Save data

    if outfile is None:
        outfile = dim + "_mean_std_raw.nc"

    filepath = os.path.join(savepath, outfile)
    print("\nSaving file " + filepath)

    oz.save(result, filepath)

    print("\nDone!")

    return


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
    t0 = time.process_time()

    axes_ds = xr.Dataset(fields_ds.coords)

    # Bin particles

    print("\nBinning particles into a grid...")
    t0_1 = time.process_time()

    # No rvar because we want absolute charge, not density
    parts = parts_into_grid(raw_ds, axes_ds, time_dim, weight_var, r_var=None)

    print(" -> Took " + str(time.process_time() - t0_1) + " s")

    if n0 is None:
        units = r"$e \frac{\Delta\xi}{2 r_e} E_0$"
    elif (n0 is not None) & (xi_var is None):
        raise Exception("Must provide name of xi variable when n0 is provided.")
    else:
        dxi = axes_ds[xi_var].to_numpy()[1] - axes_ds[xi_var].to_numpy()[0]
        parts = ozbk.lcode_convert_q(parts, dxi, q_var="nb", n0=n0)
        units = r"$e E_0$"

    # Select subsets of the fields

    print("\nMatching particle distribution with sign of fields:")

    spatial_dims = get_space_dims(axes_ds, time_dim)
    summed = []

    conditions = {
        "pospos": (fields_ds["ez"] >= 0.0) & (fields_ds["wr"] >= 0.0),
        "posneg": (fields_ds["ez"] >= 0.0) & (fields_ds["wr"] < 0.0),
        "negpos": (fields_ds["ez"] < 0.0) & (fields_ds["wr"] >= 0.0),
        "negneg": (fields_ds["ez"] < 0.0) & (fields_ds["wr"] < 0.0),
    }

    newdims = {
        "pospos": {"ez_sign": [1.0], "wr_sign": [1.0]},
        "posneg": {"ez_sign": [1.0], "wr_sign": [-1.0]},
        "negpos": {"ez_sign": [-1.0], "wr_sign": [1.0]},
        "negneg": {"ez_sign": [-1.0], "wr_sign": [-1.0]},
    }

    for case, cond in conditions.items():
        print("     - case: " + case)

        t0_1 = time.process_time()

        ez_sel = fields_ds["ez"].where(cond.compute(), drop=True)
        wr_sel = fields_ds["wr"].where(cond.compute(), drop=True)

        w_prll = abs(ez_sel * parts["nb"]).sum(dim=spatial_dims, skipna=True)
        w_perp = abs(wr_sel * parts["nb"]).sum(dim=spatial_dims, skipna=True)
        w_both = w_prll + w_perp

        # Set metadata

        ndims = w_prll.ndim

        w_prll = w_prll.expand_dims(dim=newdims[case], axis=[ndims, ndims + 1])
        w_perp = w_perp.expand_dims(dim=newdims[case], axis=[ndims, ndims + 1])
        w_both = w_both.expand_dims(dim=newdims[case], axis=[ndims, ndims + 1])

        w_prll.name = "Wpar"
        w_perp.name = "Wperp"
        w_both.name = "Wtot"

        summed = summed + [w_prll, w_perp, w_both]

        print("      -> Took " + str(time.process_time() - t0_1) + " s")

    # data_vars = { da.name: da for da in summed }
    charge_ds = xr.merge(summed)

    charge_ds["Wpar"].attrs["long_name"] = r"$W_\parallel$"
    charge_ds["Wperp"].attrs["long_name"] = r"$W_\perp$"
    charge_ds["Wtot"].attrs["long_name"] = r"$W_\mathrm{tot}$"

    for var in charge_ds.data_vars:
        charge_ds[var].attrs["units"] = units

    # Save data

    print("\nSaving data...")

    t0_1 = time.process_time()

    filepath = os.path.join(savepath, outfile)
    print("\nSaving file " + filepath)

    oz.save(charge_ds, filepath)

    print(" -> Took " + str(time.process_time() - t0_1) + " s")

    print("\nDone!")
    print("...in " + str(time.process_time() - t0) + " s")

    return


def field_space(raw_ds, fields_ds):
    # Check that datasets do not have time dimension

    t_in_fields = "t" in fields_ds.dims
    t_in_parts = "t" in raw_ds.dims

    if t_in_fields | t_in_parts:
        raise Exception(
            "Error: this function does not allow a time dimension. \
                Reduce dimension of dataset with sel() or isel() first."
        )

    # Attribute grid cell index to each particle

    spatial_dims = ["x1", "x2"]

    for dim in spatial_dims:
        axis = fields_ds.coords[dim].to_numpy()
        dx = axis[1] - axis[0]
        raw_ds[dim + "_i"] = np.floor(abs(raw_ds[dim]) / dx)

    arr_shape = fields_ds[list(fields_ds)[0]].to_numpy().shape
    raw_ds["x_ij"] = np.ravel_multi_index(
        (raw_ds["x2_i"].astype(int), raw_ds["x1_i"].astype(int)), arr_shape
    )

    raw_ds = raw_ds.drop_vars(["x1_i", "x2_i"])

    # Read field values

    for fvar in fields_ds.data_vars:
        da_tmp = xr.DataArray(
            fields_ds[fvar].to_numpy().flat[raw_ds["x_ij"].to_numpy()],
            dims="pid",
            attrs=fields_ds[fvar].attrs,
        )
        raw_ds[fvar] = da_tmp

    return raw_ds
