# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import xarray as xr

from ..new_dataobj import new_dataset
from ..utils import stopwatch

general_regex_pattern: str = r""
"""
A regular expression pattern used for matching file names or contents.
The pattern is an empty string by default.
"""
general_file_endings: str | list[str] = []
"""
A list of file extensions to consider when reading files.
These extensions are used to identify and filter out certain types of files when trying to find the data.
"""
quants_ignore: None | list[str] | str = None
"""
A list of variable names to ignore when reading data.
If None, no variables are ignored.
"""


@stopwatch
def read(files: list[str], **kwargs) -> xr.Dataset:
    """
    Read a list of files and return a [Dataset][xarray.Dataset].
    If an OSError occurs during the reading process, a new empty Dataset should be created and returned.
    """
    try:
        # code to read list of files
        pass

    except OSError:
        ds = new_dataset()

    return ds


# Defines specific methods for data from this code
class Methods:
    """Mixin class containing the definition of format-specific methods."""

    ...
