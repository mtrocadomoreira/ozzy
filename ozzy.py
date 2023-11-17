
import numpy as np
import pandas as pd
import xarray as xr
import h5py
import os
import glob

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

            query = sorted(glob.glob(quant, recursive=True, root_dir=dir))
            filessplit = [os.path.split(item) for item in query]
            head, tail = zip(*filessplit)
            tail_unique = list(set(tail))
            quants = quants + [q for q in tail_unique if '.h5' not in q]
            
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



def find_path



def open_osiris(path, runs=None, quants=None, agg_along='sims'):
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
            subdirs = dirs_runs
        else: 
            nruns = 0
            subdirs = [path]

        quants_info, ndumps = how_many_quants(subdirs, quants)

        is_agg = True

    # Read files

    if is_agg:

        # loop along quant -> store into dict
            # loop along time -> store in +1 dimension of array
                # loop along runs -> store in +1 dimension of array

    else:






    try:
        for p in path:

    except TypeError:


    f = h5py.File(file, 'r')

    # Rea



    return 