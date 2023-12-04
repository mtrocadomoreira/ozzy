
import numpy as np
import pandas as pd
import xarray as xr
import h5py
import os
from pathlib import PurePath
import glob
import dask
import seaborn as sns

# Plot styling

import matplotlib.font_manager as fm
font_dirs = ['/Users/Mariana/Documents/Work-local/i-do-sciens/mymods/ozzy/fonts']
font_files = fm.findSystemFonts(fontpaths=font_dirs)
for font_file in font_files:
    fm.fontManager.addfont(font_file)

ozparams = {
    'mathtext.fontset': 'cm',
    'font.serif': ['Noto Serif', 'serif'],
    'font.sans-serif': ['Arial', 'Helvetica', 'sans'],
    'text.usetex': False,
    'axes.grid': True,
    'grid.color': '.9',
    'axes.linewidth': '0.75',
    'xtick.major.width': '0.75',
    'ytick.major.width': '0.75',
    'lines.linewidth': '0.5',
    'figure.figsize': ('8.0','4.8'),
    'figure.dpi': '300',
    'image.cmap': 'magma',
    'savefig.format': 'pdf',
    'savefig.transparent': True,
}

sns.set_theme(style='ticks', palette='husl', font='serif', font_scale=1.1, rc=ozparams)

# Data processing

def how_many_runs(path, runs_pattern):

    currpath = os.getcwd()
    os.chdir(path)

    if isinstance(runs_pattern, str):
        runs_pattern = [runs_pattern]
    
    dirs = []
    for run in runs_pattern:
        filesindir = sorted(glob.glob(run))
        dirs = dirs + [folder for folder in filesindir if os.path.isdir(folder)]
        
    nruns = len(dirs)
    os.chdir(currpath)
    return (dirs, nruns)


def how_many_quants(parent_paths, quants_pattern):

    if isinstance(quants_pattern, str):
        quants_pattern = [quants_pattern]

    quant_info = {}
    itermax = 0

    for dir in parent_paths:

        quants = []
        for quant in quants_pattern:

            query = sorted(glob.glob('**/'+quant, recursive=True, root_dir=dir))
            filessplit = [os.path.split(item) for item in query]
            head, tail = zip(*filessplit)
            tail_unique = list(set(tail))
            quants = quants + [os.path.commonprefix(tail_unique).replace('.h5','')]

            for q in quants:
                qfiles = sorted([it for it in tail_unique \
                                if (q in it and '.h5' in it)])
                niters = len(qfiles)

                if q in list(quant_info.keys()):
                    if niters > itermax:
                        itermax = niters
                        quant_info[q] = qfiles
                else:
                    quant_info[q] = qfiles
                    itermax = niters

    return (quant_info, itermax)


def how_many_units(path_pattern):
    if isinstance(path_pattern, str):
            path_pattern = [path_pattern]

    units = []
    for path in path_pattern:
        filesindir = sorted(glob.glob(path))
        units = units + [file for file in filesindir if '.h5' in file]
    nunits = len(units)

    return(units, nunits)

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

def get_run_name(path):
    
    if 'MS' in path:
        pathloop = path
        tail = ''
        while tail != 'MS':
            head, tail = os.path.split(pathloop)
            pathloop = head
        runname = os.path.basename(head)
    else:
        try: 
            if len(filestoberead) == 1:
                absfolder = PurePath(path).parent
                runname = absfolder.parts[-1]
            else:
                commonpath = PurePath(os.path.commonpath(filestoberead))
                abspath = PurePath(path)
                relpath = abspath.relative_to(commonpath)
                runname = relpath.parts[0]
        except ValueError:
            runname = path

    return runname

def ds_config_osiris(ds):

    # Read some properties with HDF5 interface
    ax_labels = []
    ax_units = []
    ax_type = []
    xmax = []
    xmin = []    
    fname = ds.encoding['source']
    with h5py.File(fname, 'r') as f:
        move_c = f['/SIMULATION'].attrs['MOVE C']
        # ndims = f['/SIMULATION'].attrs['NDIMS']
        # nx = f['/SIMULATION'].attrs['NX']
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
    run_name = get_run_name(fname)

    ds = ds.assign_coords({'time': ds.attrs['TIME'], 'iter': ds.attrs['ITER'], 'move_offset': xmin[0], 'run': run_name})
    ds = ds.expand_dims(dim={'time':1}, axis=ndims).expand_dims(dim={'run':1}, axis=ndims+1)
    ds.time.attrs['units'] = tex_format(ds.attrs['TIME UNITS'])
    ds.time.attrs['long_name'] = 'Time'
    ds.attrs['length_x1'] = length_x1
    ds.attrs['dx'] = dx
    ds.attrs['nx'] = nx
    ds.attrs['source'] = fname

    ds = ds.fillna(0.0)

    return ds    


def open_many_osiris(files):

    with dask.config.set({"array.slicing.split_large_chunks": True}):

        ds = xr.open_mfdataset(files, chunks='auto', engine='h5netcdf', phony_dims='access', preprocess=ds_config_osiris, combine='by_coords',
        join='exact')

    ds.attrs['source'] = os.path.commonpath(files)

    return ds



def open_osiris(path, runs=None, quants=None):
    """Opens OSIRIS data in HDF5 format

    Args:
        file (string): location of file to be opened
    """

    # Sort out the input

    if (runs is None) and (quants is None):

        dirs_units, nunits = how_many_units(path)
        is_agg = False

    else:

        assert quants is not None, "'quants' keyword must be specified along with 'runs' keyword"

        assert isinstance(path, str), "'path' keyword must be a string when 'quants' keyword is specified"

        if runs is not None:
            dirs_runs, nruns = how_many_runs(path, runs)
            subdirs = [os.path.join(path, fldr) for fldr in dirs_runs]
            print('Found ' + str(nruns) + ' run(s):')
            [print('    ' + item) for item in dirs_runs]
        else: 
            dirs_runs = ['']
            nruns = 0
            subdirs = [path]

        quants_info, ndumps = how_many_quants(subdirs, quants)
        nquants = len(list(quants_info.keys()))

        print('Found ' + str(nquants) + ' quantities with ' + str(ndumps) + ' dumps at most:')
        [print('    ' + item) for item in list(quants_info.keys())]

        is_agg = True

    # Read files
    global filestoberead
    filestoberead = []

    if is_agg:

        allquants = []

        for quant, files in quants_info.items():

            filepaths = []

            for run in dirs_runs:
                for file in files:
                    # print('Reading ' + file + '...')
                    loc = sorted(glob.glob('**/'+file, recursive=True, root_dir=os.path.join(path,run)))
                    fullloc = [os.path.join(path,run,lc) for lc in loc]
                    filepaths = filepaths + fullloc

            filestoberead = filestoberead + filepaths
            ds = open_many_osiris(filepaths)
            allquants.append(ds)
        
        dataset = allquants[0]
        for i in np.arange(1,len(allquants)):
            dataset = dataset.assign(allquants[i].data_vars)

        # Check whether any data was silently dropped

        if len(dataset['run']) < nruns:
            print('\n--- WARNING ---\nDataset(s) of one or more runs may have been silently dropped\n')
        if len(dataset['time']) < ndumps:
            print('\n--- WARNING ---\nDataset(s) for one or more dumps may have been silently dropped\n')
        if len(dataset.data_vars.keys()) < nquants:
            print('\n--- WARNING ---\nOne or more quantity(-ies) may have been silently dropped\n')

    else:

        dataset = []
        print('Reading the following files:')
        filestoberead = dirs_units

        for item in filestoberead:
            print('    ' + item)
            ds = open_many_osiris(item)
            dataset.append(ds)


    print('Done!')

    return dataset