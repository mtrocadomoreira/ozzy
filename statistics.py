import os
import numpy as np

def mean_rms_grid(xda, dims, savepath=os.getcwd(), outfile=None):

    # new xr dataset: same dims as xda, except dims in keyword
    # name of quantity 'quant_rms'
    # same units

    # name of file: 'quant_rms_grid.pkl' or keyword


def mean_rms_raw(xds, dims, binned_axes, savepath=os.getcwd(), outfile=None, expand_time=True):

    if not isinstance(dims, list):
        dims = [dims]

    # Check if dimension(s) exists in dataset
    problem = 0
    for dim in dims:
        if dim not in xds.data_vars:
            print('Error: dimension "' + dim + '" not found in dataset.')
            problem = problem + 1
    if problem > 0:
        raise Exception('Could not find dimension(s) to perform operation along.')
    
    # Check if dimension(s) in output "target_xda" = xarray.DataArray exist in input dataset "xds" = xarray.Dataset
    problem = 0
    for out_dim in target_xda.dims:
        if out_dim not in xds.data_vars:
            print('Error: output dimension "' + out_dim + '" could not be found in input dataset.')
            problem = problem + 1
    if problem > 0:
        raise Exception('Problem matching output dim(s) with input dim(s).')

    # Prepare binning array

    bin_lims = []
    bin_vars = []
    bin_axes = []
    if isinstance(binned_axes, xr.DataArray):
        axis = np.array(binned_axes)
        bin_axes[0] = axis

        axis = axis + 0.5*(axis[1]-axis[0])
        vmin = axis[0] - 0.5*(axis[1]-axis[0])
        axis = np.insert(axis, 0, vmin)
        
        bin_arr[0] = axis
        bin_var[0] = binned_axes.name
    elif isinstance(binned_axes, xr.Dataset):
        for var in binned_axes.data_vars:
            axis = np.array(binned_axes[var])
            bin_axes.append(axis)

            vmin = axis[0] - 0.5*(axis[1]-axis[0])
            axis = axis + 0.5*(axis[1]-axis[0])
            axis = np.insert(axis, 0, vmin)

            bin_arr.append(axis)
            bin_var.append(var)
    else:
       raise Exception('Error: Was expecting the keyword "binned_axes" to be either an xarray.DataArray or an xarray.Dataset.')

    # Prepare dataset for calculation

    for dim in dims:
        xds[dim+'_sqr'] = xds[dim]**2
        xds[dim+'_sqrw'] = xds[dim+'_sqr'].weighted(xds['q'])
    
    ds = xds[bin_var + [dim+'_sqrw' for dim in dims]]

    # Group into bins along each binnable dimension

    for bvar, bax in zip(bin_var, bin_arr):


    

    # name of file: 'quant_rms_grid.pkl' or keyword

    
    


    