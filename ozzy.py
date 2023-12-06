
import numpy as np
import pandas as pd
import os
from pathlib import PurePath
import glob
import re
import collections

from . import backends
from . import plotting

# Data processing

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


def find_quants(path, dirs_runs, quants, file_format):

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

    tail_pattern = r"0\d+.*\." + file_format
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


def open(path=os.getcwd(), runs=None, quants=None, file_type='osiris.h5'):

    # os.chdir(path)

    # Get run information

    dirs_runs, nruns = find_runs(path, runs)

    # Get quantity information

    file_format = file_type.split('.')[-1]
    try:
        assert len(file_type.split('.')) == 2
    except AssertionError:
        print('Error: invalid input for "file_type" keyword')
        raise 

    files_quants, nquants, ndumps = find_quants(path, dirs_runs, quants, file_format)

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

    currpath = os.getcwd()
    os.chdir(path)
    for run, run_dir in dirs_runs.items():
        for quant, quant_files in files_quants.items():

            filepaths_to_read = []
            for file in quant_files:
                fileloc = glob.glob('**/'+file, recursive=True, root_dir=run_dir)
                fullloc = [os.path.join(run_dir,loc) for loc in fileloc]
                filepaths_to_read = filepaths_to_read + fullloc

            dataset = backends.read(filepaths_to_read, file_type)
            dataset.attrs['run'] = run
            df.at[run,quant] = dataset
    os.chdir(currpath)

    return df