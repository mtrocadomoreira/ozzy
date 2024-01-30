import numpy as np
import pandas as pd
import xarray as xr
import h5py
import dask
import dask.dataframe as dd
import dask.array as da
import os
import re
import time

# --- Helper functions ---

def get_regex_tail(file_type):

    file_format = file_type.split('.')[-1]

    match file_type:
        case 'osiris.h5':
            expr = r"0\d+.*\." + file_format
        case 'lcode.swp':
            expr = r"\d+.*\." + file_format
        case 'lcode.dat':
            expr = r"\." + file_format
        # case 'lcode.*':
        #     expr = r".*\.(swp|dat|det|pls)"
        case 'ozzy.h5' | 'ozzy.nc':
            expr = r".*\." + file_format
        case _:
            raise Exception('Error: invalid input for "file_type" keyword')

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

def lcode_get_rqm(ds):

    ds['q_sign'] = xr.apply_ufunc(np.sign, ds['q'], dask='allowed')
    ds['rqm'] = ds['q_sign'] * ds['abs_rqm']
    ds = ds.drop_vars('q_sign')

    return ds


# --- Functions to pass to xarray.open_mfdataset for each file type ---

def config_lcode_raw(file):

    cols = ['x1', 'x2', 'p1', 'p2', 'L', 'abs_rqm', 'q', 'pid']
    label = ['$\\xi$', '$r$', '$p_z$', '$p_r$', '$L$', '$|\mathrm{rqm}|$', '$q$', 'pid']
    units = ['$k_p^{-1}$', '$k_p^{-1}$', '$m_e c$', '$m_e c$', '$m_e c^2 / \\omega_p$', '', '$\\Delta \\xi m_e c^2 / (2 e)$', '']

    arr = np.fromfile(file).reshape(-1,8)
    dda = da.from_array(arr[0:-1,:])

    data_vars = {}
    for i, var in enumerate(cols[0:-1]):
        data_vars[var] = ('pid', dda[:,i], {
            'long_name': label[i],
            'units': units[i]
        })  

    xds = xr.Dataset(data_vars).expand_dims(dim={'t':1}, axis=1)\
        .assign_coords({'pid': dda[:,-1]})
    xds.coords['pid'].attrs['long_name'] = label[-1]
    xds.coords['pid'].attrs['units'] = units[-1]

    return xds

def config_lcode_grid(file, quant):

    ddf = dd.read_table(file, sep='\s+', header=None)\
        .to_dask_array(lengths=True)

    ndims = ddf.ndim
    match ndims:
        case 1:
            dims = ['x1']
            ddf = np.flip(ddf, axis=0)
        case 2:
            dims = ['x2', 'x1']
            ddf = ddf.transpose()
            ddf = np.flip(ddf, axis=1)
        case _:
            raise Exception('Invalid number of dimensions in file ' + file)

    xds = xr.Dataset(data_vars={quant: (dims, ddf)})\
        .expand_dims(dim={'t':1}, axis=ndims)

    xds[quant].attrs['long_name'] = quant
    xds.attrs['ndims'] = ndims

    # add units and label to coordinates

    return xds


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


def read_lcode_1Dtime(files, quant):

    assert len(files) == 1

    ddf = dd.read_table(files[0], sep='\s+', header=None)\
        .to_dask_array(lengths=True)
    ddf = ddf.transpose()

    xds = xr.Dataset(
        data_vars={
            quant: ('t', ddf[1]),
            quant.replace('max','min'): ('t', ddf[3]),
            'ximax': ('t', ddf[2]),
            'ximin': ('t', ddf[4])
        }
    )

    xds = xds.assign_coords({'t': ddf[0]})
    xds.coords['t'].attrs['long_name'] = '$t$'
    xds.coords['t'].attrs['units'] = '$\omega_p^{-1}$'
    xds.attrs['source'] = os.path.commonpath(files)
    xds.attrs['files_prefix'] = os.path.commonprefix( [os.path.basename(f) for f in files] ) 

    return xds


def read_lcode_dumps(files, quant):

    print('\nFiles are being read one by one:\n')

    if quant is None:
        quant = 'quant'

    ds_t = []

    with dask.config.set({"array.slicing.split_large_chunks": True}):
        for file in files:

            print('  - '+ file)

            if quant == 'tb':
                xds = config_lcode_raw(file)
            else:
                xds = config_lcode_grid(file, quant)

            thistime = float(re.search(r'\d+', os.path.basename(file)).group(0))
            xds = xds.assign_coords({'t': [thistime]})

            ds_t.append(xds)

    print('\nConcatenating along time... (this may take a while for raw files)')
    t0 = time.process_time()
    ds = xr.concat(ds_t, 't', fill_value={'q': 0.0})
    print(' -> Took ' + str(time.process_time()-t0) + ' s'  )

    ds.coords['t'].attrs['long_name'] = '$t$'
    ds.coords['t'].attrs['units'] = '$\omega_p^{-1}$'
    ds = ds.sortby('t')
    ds.attrs['source'] = os.path.commonpath(files)
    ds.attrs['files_prefix'] = os.path.commonprefix( [os.path.basename(f) for f in files] )

    return ds


# --- Main functions ---

def read_ozzy(files):

    ds = xr.open_mfdataset(files, engine='h5netcdf').load()

    return ds


def read_lcode(files, quant):

    match files[0][-4:]:
        case '.swp':
            ds = read_lcode_dumps(files, quant)
        case '.dat':
            if files[0][-5] == 'f':
                ds = read_lcode_1Dtime(files, quant)
            else:
                print('\nERROR: backend for these files not implemented yet. Ignoring.\n')
                ds = None
        case '.det' | '.pls':
            print('\nERROR: backend for these files not implemented yet. Ignoring.\n')
            ds = None
        case _:
            raise Exception('Error: LCODE file format not recognized.')

    return ds


def read_osiris(files):

    print('\nChunk of files being read and concatenated in a single xarray operation (xarray.open_mfdataset):')
    for f in files:
        print('  - ' + f)

    t0 = time.process_time()
    with dask.config.set({"array.slicing.split_large_chunks": True}):

        ds = xr.open_mfdataset(files, chunks='auto', engine='h5netcdf', phony_dims='access', preprocess=config_osiris, combine='by_coords', join='exact')

    ds.attrs['source'] = os.path.commonpath(files)
    ds.attrs['files_prefix'] = os.path.commonprefix( [os.path.basename(f) for f in files] )

    print(' -> Took ' + str(time.process_time()-t0) + ' s'  )

    return ds

def read(filepaths, file_type, quant=None):

    match file_type:
        case 'osiris.h5':
            ds = read_osiris(filepaths)
        case 'lcode.swp' | 'lcode.dat' | 'lcode.*':
            ds = read_lcode(filepaths, quant)
        case 'ozzy.h5' | 'ozzy.nc':
            ds = read_ozzy(filepaths)
        case _:
            raise Exception('Error: invalid input for "file_type" keyword')

    return ds
