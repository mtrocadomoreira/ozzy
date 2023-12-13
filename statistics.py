import os
import numpy as np
from flox.xarray import xarray_reduce

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

def mean_rms_raw(xds, dim, binned_axis, savepath=os.getcwd(), outfile=None, expand_time=True, axisym=False):

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
    
    # Check if dimension(s) in output "target_xda" = xarray.DataArray exist in input dataset "xds" = xarray.Dataset
    problem = 0
    for out_dim in target_xda.dims:
        if out_dim not in xds.data_vars:
            print('Error: output dimension "' + out_dim + '" could not be found in input dataset.')
            problem = problem + 1
    if problem > 0:
        raise Exception('Problem matching output dim(s) with input dim(s).')

    # Prepare binning array

    bin_arr = []
    bin_vars = []
    bin_axes = []
    if isinstance(binned_axis, xr.DataArray):
        axis = np.array(binned_axis)
        bin_axes.append(axis)
        bin_arr.append(bins_from_axis(axis))
        bin_var.append(binned_axis.name)
    elif isinstance(binned_axis, xr.Dataset):
        for var in binned_axis.data_vars:
            axis = np.array(binned_axis[var])
            bin_axes.append(axis)
            bin_arr.append(bins_from_axis(axis))
            bin_var.append(var)
    else:
       raise Exception('Error: Was expecting the keyword "binned_axis" to be either an xarray.DataArray or an xarray.Dataset.')

    # Prepare dataset for calculation
    
    ds = xds[bin_var + [dim, 'q']]
    ds[dim+'_sqw'] = (ds[dim]**2) * ds['q']
    if axisym == False:
        ds[dim+'_w'] = ds[dim]*ds['q']
    ds = ds.drop_vars(['q', dim])

    # Determine bin index for each particle (and for each binning variable)

    for i, bvar in enumerate(bin_var):
        group_id = np.digitize(ds[bvar].isel(t=0),bin_arr[i])
        group_labels = [bin_axes[i][j] for j in group_id]
        ds = ds.assign_coords({ bvar+'_bin': ('pid',group_labels) })

    # Perform mean along the dataset and get final variables

    print('\nCalculating mean and rms...')

    by_dims = [ds[key] for key in ds.coords if '_bin' in key]

    result = xarray_reduce(ds, by_dims, func='mean', sort=True, dim='pid', keep_attrs=True, fill_value=np.nan)

    if axisym == False:
        result[dim+'_rms'] = np.sqrt(result[dim+'_sqw'] - result[dim+'_w']**2)
        result = result.rename({dim+'_w': dim+'_mean'}).drop_vars(dim+'_sqw')
        result[dim+'_mean'].attrs['long_name'] = 'mean(' + result[dim+'_mean'].attrs['long_name'] + ')'
    else:
        result[dim+'_rms'] = np.sqrt(result[dim+'_sqw'])
        result = result.drop_vars(dim+'_sqw')

    result[dim+'_std'].attrs['long_name'] = 'std(' + result[dim+'_std'].attrs['long_name'] + ')'

    # Save data

    if outfile is None:
        outfile = dim + '_mean_rms_raw.nc'

    filepath = os.path.join(savepath,outfile)
    print('\nSaving file ' + filepath)

    result.to_netcdf(filepath, engine-'h5netcdf', compute=True, invalid_netcdf=True)

    print('\nDone!')

    return
    

    # name of file: 'quant_rms_grid.pkl' or keyword

    
    


    