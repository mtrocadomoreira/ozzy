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
from ..utils import find_item_in_h5, force_str_to_list, stopwatch

general_regex_pattern: str = r""
"""
A regular expression pattern used for matching file names or contents.
The pattern is an empty string by default.

!!! tip
    Use [regex101.com](https://regex101.com/) to experiment with and debug regular expressions.

???+ example
    For OSIRIS files:
    ```python
    general_regex_pattern = r"([\w-]+)-(\d{6})\.(h5|hdf)"
    ```
"""
general_file_endings: str | list[str] = []
"""
A list of file extensions to consider when reading files.
These extensions are used to identify and filter out certain types of files when trying to find the data.
???+ example
    For LCODE files:
    ```python
    general_file_endings = ["swp", "dat", "det", "bin", "bit", "pls"]
    ```
"""
quants_ignore: None | list[str] | str = None
"""
A list of variable names to ignore when reading data. This is useful when the code saves a file containing axis data or other metadata only, and should therefore not be considered a quantity file.
If `None`, no variables are ignored.

???+ example
    For LCODE files:
    ```python
    quants_ignore = ["xi"]
    ```
"""


# function to preprocess files should go here
def config_openpmd(ds):

    return ds


@stopwatch
def read(files: list[str], records: str | list[str] = "all", **kwargs) -> xr.Dataset:
    """
    Read a list of files and return a [Dataset][xarray.Dataset].
    If an `OSError` occurs during the reading process, a new empty Dataset should be created and returned.
    """
    # TODO: update docstring

    # HACK: maybe return two separate objects if no records are specified, or if fields+particles

    # sort out what will be read and pass configuration to a open_mfdataset function call

    try:
        if len(files) > 0:

            # Parse records keyword

            records = force_str_to_list(records)

            for rec in records:

                match rec:
                    case "all":
                        pass
                    case "fields" | "mesh" | "meshes" | "grid":
                        pass
                    case "particles" | "particle" | "part":
                        pass
                    case _:
                        # any other mesh record, or also a specific particle species
                        # need function to check whether record exists in file:
                        #   go into data/[any folder at this level]/
                        #       search in fields/
                        #       search in particles/
                        # return positive | negative | ambiguous (multiple matches)
                        # if negative:
                        #   throw ValueError
                        # if ambiguous:
                        #   throw ValueError
                        # if positive:
                        #   proceed

                        matches_rec = find_item_in_h5(files[-1], rec)
                        pass

                # define configuration for variables to be read
                # maybe parse and check vars keyword? or leave that for later?

            # pass variables to be read along to open_mfdataset
            pass
        else:
            raise OSError
        # code to read list of files
    except OSError:
        ds = new_dataset()

    return ds


# Defines specific methods for data from this code
class Methods:
    """_There are currently no OpenPMD-specific methods._"""

    ...
