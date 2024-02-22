import os
import numpy as np
import xarray as xr
from . import ozzy as oz
from flox.xarray import xarray_reduce
import time

# --- Helper functions ---

def bins_from_axis(axis):
    vmin = axis[0] - 0.5*(axis[1]-axis[0])
    binaxis = axis + 0.5*(axis[1]-axis[0])
    binaxis = np.insert(binaxis, 0, vmin)
    return binaxis


def mean_rms_grid(xda, dims, savepath=os.getcwd(), outfile=None):

    # new xr dataset: same dims as xda, except dims in keyword
    # name of quantity 'quant_rms'
    # same units

    # name of file: 'quant_rms_grid.pkl' or keyword
    return

def parts_into_grid(raw_ds, axes_ds, time_dim='t', weight_var='q', r_var=None):

    spatial_dims = list(set(list(axes_ds.coords)) - {time_dim})

    bin_edges = []
    for axis in spatial_dims:
        axis_arr = np.array(axes_ds[axis])
        bin_edges.append(bins_from_axis(axis_arr))

    q_binned = []

    # Multiply weight by radius, if r_var is specified

    if r_var == None:
        wvar = weight_var
    else:
        raw_ds['w'] = raw_ds[weight_var] / raw_ds[r_var]
        wvar = 'w'

    # Loop along time

    for i in np.arange(0, len(raw_ds[time_dim])):

        ds_i = raw_ds.isel({time_dim: i})

        part_coords = [ds_i[var] for var in spatial_dims]
        dist, edges = np.histogramdd(
            part_coords, 
            bins = bin_edges, 
            weights = ds_i[wvar]
        )

        newcoords = {var: axes_ds[var] for var in spatial_dims}
        newcoords[time_dim] = ds_i[time_dim]
        qds_i = xr.Dataset(
            data_vars={
                'nb': (spatial_dims, dist)
            }, 
            coords=newcoords
        )
        q_binned.append(qds_i)

    parts = xr.concat(q_binned, time_dim)

    return parts


def get_phase_space(raw_ds, vars, extents=None, nbins=200):

    # Define extent and nbins depending on input

    if extents == None:
        extents = {}
        for v in vars:
            maxval = float(raw_ds[v].max().compute().to_numpy())
            minval = float(raw_ds[v].min().compute().to_numpy())
            if (minval < 0) & (maxval > 0):
                extr = max([abs(minval),maxval])
                lims = (-extr, extr)
            else:
                lims = (minval, maxval)
            extents[v] = lims
    else:
        assert type(extents) == dict

    if type(nbins) == int:
        bins = {}
        for v in vars:
            bins[v] = nbins
    else:
        assert type(nbins) == dict
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

    ps = ps.rename_vars({'nb': 'Q'})
    ps['Q'].attrs['units'] = r"$\Delta\xi m c^2 / (2 e)$"
    ps['Q'].attrs['long_name'] = r"$Q$"

    return ps

def mean_std_raw(xds, dim, binned_axis, savepath=os.getcwd(), outfile=None, expand_time=True, axisym=False):

    print('\nPreparing...')

    if isinstance(dim, list):
        if len(dim) == 1:
            dim = dim[0]
        else:
            raise Exception('Keyword "dim" must be one single dimension')

    # Check if dimension(s) exists in dataset
    if dim not in xds.data_vars:
        print('Error: dimension "' + dim + '" not found in dataset.')
        raise Exception('Could not find dimension to perform operation along.')
    
    # Check if dimension(s) in input "binned_axis" = xarray.DataArray exist in input dataset "xds" = xarray.Dataset

    if isinstance(binned_axis, xr.DataArray):
        binned_axis = binned_axis.to_dataset()

    problem = 0
    for out_dim in binned_axis.data_vars:
        if out_dim not in xds.data_vars:
            print('Error: output dimension "' + out_dim + '" could not be found in input dataset.')
            problem = problem + 1
    if problem > 0:
        raise Exception('Problem matching output dim(s) with input dim(s).')

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
        print('Error: Was expecting the keyword "binned_axis" to be either an xarray.DataArray or an xarray.Dataset.')
        raise

    # Prepare dataset for calculation

    ds = xds[bin_vars + [dim, 'q']]
    ds[dim+'_sqw'] = (ds[dim]**2) * ds['q']
    if axisym == False:
        ds[dim+'_w'] = ds[dim]*ds['q']
    ds = ds.drop_vars(['q', dim])

    # Determine bin index for each particle (and for each binning variable)

    for i, bvar in enumerate(bin_vars):
        group_id = np.digitize(ds[bvar].isel(t=0),bin_arr[i])
        group_labels = [bin_axes[i][j] for j in group_id]
        ds = ds.assign_coords({ bvar+'_bin': ('pid',group_labels) })

    # Perform mean along the dataset and get final variables

    print('\nCalculating mean and standard deviation...')

    by_dims = [ds[key] for key in ds.coords if '_bin' in key]

    result = ds
    for dim_da in by_dims:
        try: 
            result = xarray_reduce(result, dim_da, func='mean', sort=True, dim='pid', keep_attrs=True, fill_value=np.nan)
        except:
            print('This is probably a problem with the multiple binning axes. Have to look over this.')
            raise

    if axisym == False:
        result[dim+'_std'] = np.sqrt(result[dim+'_sqw'] - result[dim+'_w']**2)
        result = result.rename({dim+'_w': dim+'_mean'})

        result[dim+'_mean'].attrs['long_name'] = 'mean(' + xds[dim].attrs['long_name'] + ')'
        result[dim+'_mean'].attrs['units'] = xds[dim].attrs['units']
    else:
        result[dim+'_std'] = np.sqrt(result[dim+'_sqw'])

    result[dim+'_std'].attrs['long_name'] = 'std(' + xds[dim].attrs['long_name'] + ')'
    result[dim+'_std'].attrs['units'] = xds[dim].attrs['units']
    result = result.drop_vars(dim+'_sqw')

    # Save data

    if outfile is None:
        outfile = dim + '_mean_std_raw.nc'

    filepath = os.path.join(savepath,outfile)
    print('\nSaving file ' + filepath)

    oz.save(result, filepath)

    print('\nDone!')

    return
    

def charge_in_fields(raw_ds, fields_ds, time_dim ='t', savepath=os.getcwd(), outfile=None, weight_var = 'q', r_var = None):

    t0 = time.process_time()

    fields = fields_ds.data_vars
    axes_ds = xr.Dataset(fields_ds.coords)

    # Bin particles

    print('\nBinning particles into a grid...')
    t0_1 = time.process_time()

    parts = parts_into_grid(raw_ds, axes_ds, time_dim, weight_var, r_var)

    print(' -> Took ' + str(time.process_time()-t0_1) + ' s'  )

    # Select subsets of the fields

    print('\nMatching particle distribution with sign of fields:')

    spatial_dims = list(set(list(axes_ds.coords)) - {time_dim})
    summed = []

    for f in fields:

        print('     - ' + f)
        t0_1 = time.process_time()

        f_pos = fields_ds[f].where((fields_ds[f]>=0.0).compute(), drop=True)
        f_neg = fields_ds[f].where((fields_ds[f]<0.0).compute(), drop=True)

        f_pos = abs(f_pos * parts['nb'])
        f_neg = abs(f_neg * parts['nb'])

        q_pos = f_pos.sum(dim=spatial_dims, skipna=True)
        q_neg = f_neg.sum(dim=spatial_dims, skipna=True)

        # Set metadata

        q_pos.name = 'q_' + f + '_pos'
        q_neg.name = 'q_' + f + '_neg'

        if 'long_name' in fields_ds[f].attrs:
            flabel = fields_ds[f].attrs['long_name'].strip('$') 
        else:
            flabel = f.capitalize()

        q_pos.attrs['long_name'] = '$Q(' + f + ' \\geq 0)$'
        q_neg.attrs['long_name'] = '$Q(' + f + ' < 0)$'

        if 'units' in raw_ds['q'].attrs:
            unt = raw_ds['q'].attrs['units']
        else:
            unt = ''
        q_pos.attrs['units'] = unt
        q_pos.attrs['units'] = unt

        # Add to list

        summed = summed + [q_pos, q_neg]

        print('      -> Took ' + str(time.process_time()-t0_1) + ' s'  )
        
    data_vars = { da.name: da for da in summed }
    charge_ds = xr.Dataset(data_vars)

    # Save data

    print('\nSaving data...')

    t0_1 = time.process_time()

    if outfile is None:
        outfile = 'charge_in_fields.nc'

    filepath = os.path.join(savepath,outfile)
    print('\nSaving file ' + filepath)

    oz.save(charge_ds, filepath)

    print(' -> Took ' + str(time.process_time()-t0_1) + ' s'  )

    print('\nDone!')
    print('...in ' + str(time.process_time()-t0) + ' s'  )

    return
    


    