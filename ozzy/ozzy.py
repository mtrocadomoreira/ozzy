
import numpy as np
import pandas as pd
import os
from pathlib import PurePath
import glob
import re
import collections

from . import backends
from . import plotting

# Helper functions

def validate_file_type(file_type):
    try:
        assert len(file_type.split('.')) == 2
    except AssertionError:
        print('Error: invalid input for "file_type" keyword')
        raise 
    return

# Data processing

def coord_to_physical_distance(ds, coord, n0, units='m'):

    if not any([units==opt for opt in ['m', 'cm']]):
        raise Exception('Error: "units" keyword must be either "m" or "cm"')
    
    # assumes n0 is in cm^(-3), returns skin depth in meters
    skdepth = 3e8/5.64e4/np.sqrt(n0)
    if units == 'cm':
        skdepth = skdepth * 100.0

    if coord not in ds.coords:
        print('\nError: Could not find time coordinate to calculate the propagation distance coordinate.\nReturning the dataset unchanged.')
        newds = ds
    else:
        newcoord = coord + '_' + units
        newds = ds.assign_coords({newcoord: skdepth*ds.coords[coord] })
        newds[newcoord].attrs['units'] = '$\mathrm{' + units + '}$'

    return newds

def axis_from_extent(nx, lims):
    # Check format of value 
    try:
        assert isinstance(lims, tuple) and len(lims)==2
    except AssertionError:
        raise Exception('Extent "lims" should be given as a two-element tuple: (min, max)')
    
    dx = (lims[1]-lims[0]) / nx
    ax = np.arange(lims[0]+dx, lims[1]+dx, dx) - 0.5*dx

    return ax
    

def coords_from_extent(ds, mapping):
    newds = ds
    for k, v in mapping.items():
        # Construct axis array
        nx = ds.sizes[k]
        ax = axis_from_extent(nx, v)

        newds = newds.assign_coords({k: ax})
    
    return newds


def sample_particles(ds, n):
    surviving = ds.isel(t=-1).coords['pid'].notnull()
    pool = ds.coords['pid'][surviving]
    nparts = len(pool)
    if n > nparts:
        print('Warning: number of particles to be sampled is larger than total particles. Proceeding without any sampling.')
    else:
        rng = np.random.default_rng()
        downsamp = rng.choice(pool['pid'], size=n, replace=False, shuffle=False)
        ds = ds.sel(pid=np.sort(downsamp))
    return ds


# Reading/writing files

def find_runs(path, runs_pattern):

    dirs = []
    run_names = []

    if runs_pattern == None:

        runname = PurePath(path).parts[-1]
        dirs.append(runname)

    else:

        if isinstance(runs_pattern, str):
            runs_pattern = [runs_pattern]

        for run in runs_pattern:
            filesindir = sorted(glob.glob(run, root_dir=path))
            dirs = dirs + [folder for folder in filesindir if os.path.isdir(os.path.join(path,folder))]
        
    run_names = dirs    
    nruns = len(dirs)

    if nruns == 0:

        # Check whether already inside run folder
        folder = PurePath(path).parts[-1]
        try:
            assert any([folder == item for item in runs_pattern])
        except AssertionError:
            print('Could not find any run folder.\nProceeding without a run name.')
            run_names = ['undefined']
        else:
            run_names = [folder]
        finally:
            dirs.append('.')
            nruns = 1

    dirs_dict = {}
    for i, k in enumerate(run_names):
        dirs_dict[k] = dirs[i]

    return (dirs_dict, nruns)


def find_quants(path, dirs_runs, quants, file_type):

    validate_file_type(file_type)
    file_format = file_type.split('.')[-1]

    filenames = []

    for run, dir in dirs_runs.items():

        searchdir = os.path.join(path, dir)

        if quants == None:
            query = sorted(glob.glob('**/*.'+file_format, recursive=True, root_dir=searchdir))
        else:
            if isinstance(quants, str):
                quants = [quants]
            for q in quants:
                query = sorted(glob.glob('**/'+q+'*', recursive=True, root_dir=searchdir))
                filenames = filenames + [os.path.basename(f) for f in query]

    # Look for clusters of files matching pattern

    tail_pattern = backends.get_regex_tail(file_type)
    pattern = r".*" + tail_pattern

    matched = [f for f in filenames if re.match(pattern,f)]

    quants_dict = collections.defaultdict(list)
    for f in matched:
        pat = re.sub(tail_pattern, '', f).strip('-_ ')
        if f not in quants_dict[pat]:
            quants_dict[pat].append(f)

    # Discard quantities with suffixes if input specifies exact match

    found_quants = list(quants_dict.keys())
    for q in quants:
        if q[-1] == '.':
            for foundq in found_quants:
                if (q in foundq) and (q != foundq):
                    del quants_dict[foundq]

    # Summarise and return

    nquants = len(list(quants_dict.keys()))

    max_ndumps = 0
    for q, files in quants_dict.items():
        ndumps = len(files)
        if ndumps > max_ndumps:
                max_ndumps = ndumps        

    return (quants_dict, nquants, max_ndumps) 


def open(path, file_type):

    assert isinstance(path, str)
    ds = backends.read([path], file_type, as_series=False)

    return ds

def open_series(files, file_type):

    if isinstance(files, str):
        filelist = sorted(glob.glob(files))
    else:
        filelist = files

    ds = backends.read(filelist, file_type, as_series=True)

    return ds

def open_compare(file_type, path=os.getcwd(), runs='*', quants='*'):

    # Get run information

    dirs_runs, nruns = find_runs(path, runs)

    # Get quantity information

    files_quants, nquants, ndumps = find_quants(path, dirs_runs, quants, file_type)

    # Print info found so far

    print('\nFound ' + str(nruns) + ' run(s):')
    [print('    ' + item) for item in dirs_runs.keys()]

    print('\nFound ' + str(nquants) + ' quantities with ' + str(ndumps) + ' dumps at most:')
    [print('    ' + item) for item in list(files_quants.keys())]

    # Initialize dataframe

    df = pd.DataFrame(
            index=list(dirs_runs.keys()),
            columns=list(files_quants.keys())
        )

    # Loop along runs and along quants

    print('\nFile reading backend: ' + file_type)

    currpath = os.getcwd()
    os.chdir(path)
    for run, run_dir in dirs_runs.items():
        for quant, quant_files in files_quants.items():

            filepaths_to_read = []
            for file in quant_files:
                fileloc = glob.glob('**/'+file, recursive=True, root_dir=run_dir)
                fullloc = [os.path.join(run_dir,loc) for loc in fileloc]
                filepaths_to_read = filepaths_to_read + fullloc

            dataset = backends.read(filepaths_to_read, file_type, quant)
            dataset.attrs['run'] = run
            df.at[run,quant] = dataset
    os.chdir(currpath)

    print('\nDone!')

    return df


def save(obj, path):

    try:
        obj.to_netcdf(path, engine='h5netcdf', compute=True, invalid_netcdf=True)
    except AttributeError:
        if isinstance(obj, pd.DataFrame):
            if path[-3:] == '.nc':
                print('Warning: User specified the netCDF file format (".nc"), but file must be saved as HDF5 (".h5") since object is a pandas.DataFrame.')
            obj.to_hdf(path, 'dataframe')
        else:
            print('Error: Object to save does not seem to be an xarray.DataArray, xarray.Dataset or pandas.DataFrame. Aborting')
            raise

    print('[ saved file "' + path +'" ]')