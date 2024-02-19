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

# --- Load backend info ---

from importlib.resources import files
lcode_data_file = files('ozzy').joinpath('lcode_file_key.csv')
lcode_regex = pd.read_csv(lcode_data_file, sep=';',header=0).sort_values(by='regex')

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
            expr = r"\." + file_format
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
    ds['rqm'] = 1.0/ds['rqm']
    ds = ds.drop_vars('q_sign')

    return ds

def lcode_identify_data_type(file_string):

    for row in lcode_regex.itertuples(index=False):

        pattern = row.regex
        match = re.fullmatch(pattern,file_string)
        if match != None:
            break

    return (row, match)

def lcode_append_time(ds, file_string):

    thistime = float(re.search(r"\d{5}", file_string).group(0))
    ds_out = ds.assign_coords({'t': [thistime]})

    return ds_out


# --- Functions to pass to xarray.open_mfdataset for each file type ---


def config_osiris(ds):

    # Read some properties with HDF5 interface

    ax_labels = []
    ax_units = []
    ax_type = []
    xmax = []
    xmin = []    
    fname = ds.encoding['source']

    f = h5py.File(fname, 'r')
    try:
        move_c = f['/SIMULATION'].attrs['MOVE C']
    except KeyError:
        raise
    else:
        axgroups = list(f['AXIS'])
        for subgrp in axgroups:
            loc = '/AXIS/' + subgrp
            ax_labels.append(unpack_str(f[loc].attrs['LONG_NAME']))
            ax_units.append(f[loc].attrs['UNITS'][0])
            ax_type.append(f[loc].attrs['TYPE'][0])
            xmax.append(f[loc][1])
            xmin.append(f[loc][0])
    finally:
        f.close()

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
    if ndims == 3:
        nx = np.roll(nx,1)

    # Rename dimensions

    match ndims:
        case 1:
            ds = ds.rename_dims({'phony_dim_0':'x1'})
        case 2:
            ds = ds.rename_dims({'phony_dim_0':'x2', 'phony_dim_1': 'x1'})
        case 3:
            ds = ds.rename_dims({'phony_dim_0':'x3', 'phony_dim_1': 'x2', 'phony_dim_2': 'x1'})
            
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


def lcode_parse_parts(file, pattern_info):

    cols = ['x1', 'x2', 'p1', 'p2', 'L', 'abs_rqm', 'q', 'pid']
    label = ['$\\xi$', '$r$', '$p_z$', '$p_r$', '$L$', '$|\mathrm{rqm}|$', '$q$', 'pid']
    units = ['$k_p^{-1}$', '$k_p^{-1}$', '$m_e c$', '$m_e c$', '$m_e c^2 / \\omega_p$', '', '$\\Delta \\xi m_e c^2 / (2 e)$', '']

    if pattern_info.subcat == 'lost':
        cols = ['t'] + cols
        units = ['$\omega_p^{-1}$'] + units
        label = ['$t$'] + label

    arr = np.fromfile(file).reshape(-1,len(cols))
    dda = da.from_array(arr[0:-1,:])

    data_vars = {}
    for i, var in enumerate(cols[0:-1]):
        data_vars[var] = ('pid', dda[:,i], {
            'long_name': label[i],
            'units': units[i]
        })  

    ds = xr.Dataset(data_vars).assign_coords({'pid': dda[:,-1]})
    ds.coords['pid'].attrs['long_name'] = label[-1]
    ds.coords['pid'].attrs['units'] = units[-1]
    if pattern_info.subcat != 'lost':
        ds = ds.expand_dims(dim={'t':1}, axis=1)

    return ds


def lcode_parse_grid(file, pattern_info, match):

    with dask.config.set({"array.slicing.split_large_chunks": True}):
        ddf = dd.read_table(file, sep='\s+', header=None)\
            .to_dask_array(lengths=True)
        ddf = ddf.transpose()

    quant = match.group(1)

    if pattern_info.subcat == 'alongz':

        label = {'e': '$E_z$', 'g': '$\phi$'}
        prefix = ''
        quant1 = quant + '_max'

        if match.group(2) == 'loc':
            quant1 = quant1 + '_loc'
            prefix = 'local '

        xds = xr.Dataset(
            data_vars={
                quant1: ('t', ddf[1]),
                quant1.replace('max','min'): ('t', ddf[3]),
                'ximax': ('t', ddf[2]),
                'ximin': ('t', ddf[4])
            }
        )

        xds[quant1].attrs['long_name'] = prefix +  'max. ' + label[quant]
        xds[quant1.replace('max','min')].attrs['long_name'] = prefix + 'min. ' + label[quant]

    else:

        ndims = ddf.ndim
        match ndims:
            case 1:
                dims = ['x1']
                ddf = np.flip(ddf, axis=0)
                # look for xi axis file and add it
                # check whether on axis or off axis
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


def lcode_concat_time(ds, files):

    ds = xr.concat(ds, 't', fill_value={'q': 0.0})
    ds.coords['t'].attrs['long_name'] = '$t$'
    ds.coords['t'].attrs['units'] = '$\omega_p^{-1}$'
    ds = ds.sortby('t')
    ds.attrs['source'] = os.path.commonpath(files)
    ds.attrs['files_prefix'] = os.path.commonprefix( [os.path.basename(f) for f in files] )

    return ds


def read_lcode_parts(files, as_series, pattern_info):

    print('Reading files...')

    ds_t = []
    for file in files:
        print('  - '+ file)

        ds_tmp = lcode_parse_parts(file, pattern_info)

        if pattern_info.subcat == 'beamfile':
            bfbit_path = os.path.join(os.path.dirname(file),'beamfile.bit')
            if os.path.exists(bfbit_path):
                with open(bfbit_path,'r') as f:
                    thistime = float(f.read())
                ds_tmp = ds_tmp.assign_coords({'t': [thistime]})

        elif pattern_info.subcat != 'lost':
            ds_tmp = lcode_append_time(ds_tmp, file)

        ds_t.append(ds_tmp)

    if (pattern_info.subcat == 'parts') & (as_series == True):
        print('\nConcatenating along time... (this may take a while for particle data)')
        t0 = time.process_time()
        ds = lcode_concat_time(ds_t, files)
        print(' -> Took ' + str(time.process_time()-t0) + ' s')
    else:
        assert len(ds_t) == 1
        ds = ds_t[0]

    return ds


def read_lcode_grid(files, as_series, pattern_info, match):

    print('Reading files...')

    ds_t = []
    for file in files:
        print('  - '+ file)
        ds_tmp = lcode_parse_grid(file, pattern_info, match)

        if pattern_info.subcat != 'alongz':
            ds_tmp = lcode_append_time(ds_tmp, file)

        ds_t.append(ds_tmp)

    if (not as_series | pattern_info.time == 'full'):
        assert len(ds_t) == 1
        ds = ds_t[0]

    else:
        print('\nConcatenating along time...')
        t0 = time.process_time()
        ds = lcode_concat_time(ds_t, files)
        print(' -> Took ' + str(time.process_time()-t0) + ' s')

    return ds


# --- Main functions ---

def read_ozzy(files, as_series):

    ds = xr.open_mfdataset(files, engine='h5netcdf').load()

    return ds


def read_lcode(files, as_series):
    # assuming files is already sorted into a single type of data (no different kinds of files)

    pattern_info, match = lcode_identify_data_type(files[0])

    match pattern_info.cat:

        case 'grid':
            ds = read_lcode_grid(files, as_series, pattern_info, match)

        case 'parts':
            ds = read_lcode_parts(files, as_series, pattern_info)

        case 'info':
            print('Error: Backend for this type of file has not been implemented yet. Exiting.')
            return

        case 'uncat':
            print('Error: Backend for this type of file has not been implemented yet. Exiting.')
            return

    return ds


def read_osiris(files, as_series):

    print('\nReading and concatenating the following files:')
    for f in files:
        print('  - ' + f)

    t0 = time.process_time()

    if as_series == False:
        assert len(files) == 1

    try:

        with dask.config.set({"array.slicing.split_large_chunks": True}):

            ds = xr.open_mfdataset(files, chunks='auto', engine='h5netcdf', phony_dims='access', preprocess=config_osiris, combine='by_coords', join='exact')

        ds.attrs['source'] = os.path.commonpath(files)
        ds.attrs['files_prefix'] = os.path.commonprefix( [os.path.basename(f) for f in files] )

    except OSError:

        ds = xr.Dataset()

    print(' -> Took ' + str(time.process_time()-t0) + ' s'  )

    return ds

def read(filepaths, file_type, as_series=True):

    match file_type:
        case 'osiris':
            ds = read_osiris(filepaths, as_series)
        case 'lcode':
            ds = read_lcode(filepaths, as_series)
        case 'ozzy':
            ds = read_ozzy(filepaths, as_series)
        case _:
            raise Exception('Error: invalid input for "file_type" keyword')

    return ds
