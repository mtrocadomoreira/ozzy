from .utils import stopwatch
from .backend import Backend
import os
import glob


def _prep_file_input(files):
    if isinstance(files, str):
        filelist = sorted(glob.glob(os.path.expanduser(files)))
    else:
        filelist = [os.path.expanduser(f) for f in files]
    return filelist


@stopwatch
def open(path, file_type, axes_lims=None):
    filelist = _prep_file_input(path)

    # initialize the backend object (it deals with the error handling)
    bknd = Backend(file_type, axes_lims, as_series=False)

    ods = bknd.parse_data(filelist)

    return ods


@stopwatch
def open_series(files, file_type, axes_lims=None, nfiles=None):
    filelist = _prep_file_input(files)

    bknd = Backend(file_type, axes_lims, as_series=True)

    ods = bknd.parse_data(filelist[:nfiles])

    return ods
