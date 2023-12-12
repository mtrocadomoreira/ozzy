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

    # Search for time dimension in input array
    # - not sure if this is necessary

    # Prepare binning array
    # for data

    if isinstance(binned_axes, xr.DataArray)

    bin_arr = 

    newarr = np.empty
    

    # name of file: 'quant_rms_grid.pkl' or keyword

    
    


    