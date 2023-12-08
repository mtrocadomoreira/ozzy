import numpy as np
import pandas as pd
import xarray as xr
import h5py
import dask
import os

# --- Helper functions ---

def get_regex_tail(file_type):

    file_format = file_type.split('.')[-1]

    match file_type:
        case 'osiris.h5':
            expr = r"0\d+.*\." + file_format
        case 'lcode.swp':
            expr = r"\d+.*\." + file_format

    return expr

def tex_format(str):
    if str == '':
        newstr = str
    else:
        newstr = '$' + str + '$'
    return newstr

def unpack_str(attr):
    if isinstance(attr, np.ndarray):
        result = attr[0]
    else:
        result = attr
    return result

# --- Functions to pass to xarray.open_mfdataset for each file type ---

def config_osiris(ds):

    # Read some properties with HDF5 interface

    ax_labels = []
    ax_units = []
    ax_type = []
    xmax = []
    xmin = []    
    fname = ds.encoding['source']
    with h5py.File(fname, 'r') as f:
        move_c = f['/SIMULATION'].attrs['MOVE C']
        axgroups = list(f['AXIS'])
        for subgrp in axgroups:
            loc = '/AXIS/' + subgrp
            ax_labels.append(unpack_str(f[loc].attrs['LONG_NAME']))
            ax_units.append(f[loc].attrs['UNITS'][0])
            ax_type.append(f[loc].attrs['TYPE'][0])
            xmax.append(f[loc][1])
            xmin.append(f[loc][0])
    xmax = np.array(xmax)
    xmin = np.array(xmin)
    length_x1 = round((xmax[0]-xmin[0])*1e3)*1e-3

    # Save data label, units and dimension info

    varname = list(ds.keys())[0]
    ds[varname] = ds[varname].assign_attrs(
        long_name = tex_format(ds.attrs['LABEL']), 
        units = tex_format(ds.attrs['UNITS'])
        )
    del ds.attrs['LABEL'], ds.attrs['UNITS']

    nx = np.array(ds[varname].shape)
    ndims = len(nx)
    if ndims >= 2:
        nx[1], nx[0] = nx[0], nx[1]

    # Rename dimensions

    match ndims:
        case 1:
            ds = ds.rename_dims({'phony_dim_0':'x1'})
        case 2:
            ds = ds.rename_dims({'phony_dim_0':'x2', 'phony_dim_1': 'x1'})
        case 3:
            ds = ds.rename_dims({'phony_dim_0':'x2', 'phony_dim_1': 'x3', 'phony_dim_2': 'x1'})
            
    # Save axis values and metadata

    dx = (xmax-xmin) / nx
    dx[0] = length_x1 / nx[0]

    ax = np.arange(dx[0], length_x1+dx[0], dx[0]) - 0.5*dx[0]
    ds = ds.assign_coords({'x1': ax})

    for i in np.arange(1,ndims):
        coord = 'x' + str(i+1)
        ax = np.arange(xmin[i]+dx[i], xmax[i]+dx[i], dx[i]) - 0.5*dx[i]
        ds = ds.assign_coords({coord: ax})

    for i in np.arange(0,ndims):
        coord = 'x' + str(i+1)
        ds.coords[coord].attrs['long_name'] = tex_format(ax_labels[i].decode('UTF-8'))
        ds.coords[coord].attrs['units'] = tex_format(ax_units[i].decode('UTF-8'))
        ds.coords[coord].attrs['TYPE'] = ax_type[i].decode('UTF-8')

    # Save other metadata

    ds = ds.assign_coords({'time': ds.attrs['TIME'], 'iter': ds.attrs['ITER'], 'move_offset': xmin[0]})
    ds = ds.expand_dims(dim={'time':1}, axis=ndims)
    ds.time.attrs['units'] = tex_format(ds.attrs['TIME UNITS'])
    ds.time.attrs['long_name'] = 'Time'
    ds.attrs['length_x1'] = length_x1
    ds.attrs['dx'] = dx
    ds.attrs['nx'] = nx

    return ds


# --- Main functions ---

def read_osiris(files):

    with dask.config.set({"array.slicing.split_large_chunks": True}):

        ds = xr.open_mfdataset(files, chunks='auto', engine='h5netcdf', phony_dims='access', preprocess=config_osiris, combine='by_coords', join='exact')

    ds.attrs['source'] = os.path.commonpath(files)
    ds.attrs['files_prefix'] = os.path.commonprefix( [os.path.basename(f) for f in files] )

    return ds

def read(filepaths, file_type):

    match file_type:
        case 'osiris.h5':
            ds = read_osiris(filepaths)
        case _:
            raise Exception('Error: invalid input for "file_type" keyword')

    return ds
