# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import h5py
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


def _find_all_records_openpmd(files):

    all_recs_fields = []
    all_specs = []
    for file in files:
        with h5py.File(file, "r") as f:
            all_iters = list(f["data"].keys())
            for it in all_iters:
                fld_quants = list(f[f"data/{it}/fields"].keys())
                all_recs_fields = all_recs_fields + fld_quants
                specs = list(f[f"data/{it}/particles"].keys())
                all_specs = all_specs + specs

    fld_recs_unique = list(set(all_recs_fields))
    specs_unique = list(set(all_specs))
    return (fld_recs_unique, specs_unique)


# function to preprocess files should go here
def config_openpmd(ds):

    return ds


@stopwatch
def read(
    files: list[str], records: str | list[str] | None = None, **kwargs
) -> xr.Dataset:
    """
    Read a list of files and return a [Dataset][xarray.Dataset].
    If an `OSError` occurs during the reading process, a new empty Dataset should be created and returned.
    """
    # TODO: update docstring

    # HACK: maybe return two separate objects if no records are specified, or if fields+particles (return different particle species separately too)

    # sort out what will be read and pass configuration to a open_mfdataset function call

    try:
        if len(files) > 0:

            # Parse records keyword

            # - map out all available records

            fld_records, part_species = _find_all_records_openpmd(files)
            string_fld_records = ", ".join([f"'{item}'" for item in fld_records])
            string_part_species = ", ".join([f"'{item}'" for item in part_species])

            # - raise informative error if records is None

            if records is None:

                raise ValueError(
                    f"""
                    Please choose which variables to read from the OpenPMD file(s) using the 'records' keyword argument.

                    Accepted options are:\n
                    \t- 'fields' | 'grid' | 'mesh' | 'meshes': read all grid-based variables\n
                    \t- [name of grid-based variable] | [list of several grid-based variable names]: read a subset of the grid-based variables
                    \t  Available variables: {string_fld_records}\n
                    \t- [name of particle species]: particle data for one species
                    \t  Available species: {string_part_species}
                    """
                )

            # - otherwise, parse records keyword

            records = force_str_to_list(records)

            if len(records) == 1:

                rec = records[0]
                match rec:
                    case "fields" | "mesh" | "meshes" | "grid":
                        # proceed, instruct to read all fields quants
                        pass
                    case "particles" | "part":

                        if len(part_species) > 1:
                            raise ValueError(
                                f"ozzy only reads particle data for one particle species at a time.\nPlease select one of the following species to read: {string_part_species}"
                            )
                        elif len(part_species) == 0:
                            print(
                                "WARNING: OpenPMD file does not seem to contain any particle data. Returning an empty dataset."
                            )
                            ds = new_dataset()
                        elif len(part_species) == 1:
                            # proceed, instruct to read particle data for the one species: part_species[0]
                            pass
                        # check how many particle species exist, raise error if more than 1
                        # else choose single species that exists and pass it along
                        pass
                    case _:
                        if rec in fld_records:
                            # proceed
                            pass
                        elif rec in part_species:
                            # proceed
                            pass
                        else:
                            raise ValueError(
                                f"Can't find record '{rec}' in OpenPMD file(s)."
                            )

            else:

                pass

            for rec in records:

                match rec:
                    case "all":
                        pass
                    case "fields" | "mesh" | "meshes" | "grid":
                        pass
                    case "particles" | "particle" | "part":
                        pass
                    case _:

                        # Try to find record in file

                        matches_rec = find_item_in_h5(files[-1], rec)

                        if len(matches_rec) == 0:
                            raise ValueError(
                                f"Could not find '{rec}' in OpenPMD file. Please specify a valid argument for the 'records' keyword."
                            )
                        elif len(matches_rec) > 1:
                            raise ValueError(
                                f"Found more than one matches for '{rec}' in OpenPMD files:\n- "
                                + "\n- ".join(matches_rec)
                                + "\nPlease provide a non-ambiguous argument for the 'records' keyword."
                            )
                        elif len(matches_rec) == 1:
                            pass

                            # check whether field or particle?
                            # and then pass quantity to config function

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
