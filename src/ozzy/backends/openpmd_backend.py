# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import os

import xarray as xr
from openpmd_viewer import OpenPMDTimeSeries

from ..new_dataobj import new_dataset
from ..utils import force_str_to_list, stopwatch

general_regex_pattern: str = r"\w+?(\d{6,8}).h5"
general_file_endings: str | list[str] = ["h5", "bp"]
quants_ignore: None | list[str] | str = None


# def _find_all_records_openpmd(files):

#     # Get path names to field and particle data

#     with h5py.File(files[0], "r") as f:

#         fld_path = unpack_attr(f.attrs["meshesPath"])
#         part_path = unpack_attr(f.attrs["particlesPath"])

#         pass

#     # Retrieve all the record names

#     all_recs_fields = []
#     all_specs = []
#     for file in files:
#         with h5py.File(file, "r") as f:
#             all_iters = list(f["data"].keys())
#             for it in all_iters:
#                 fld_quants = list(f[f"data/{it}/{fld_path}"].keys())
#                 all_recs_fields = all_recs_fields + fld_quants
#                 specs = list(f[f"data/{it}/{part_path}"].keys())
#                 all_specs = all_specs + specs

#     fld_recs_unique = list(set(all_recs_fields))
#     specs_unique = list(set(all_specs))
#     return (fld_recs_unique, specs_unique)


# ****General attributes:***** (get through h5py/adios2)

# - the ones under "/":

# date	"2025-04-29 19:39:41 +0200"
# iterationEncoding	"fileBased"
# iterationFormat	"openpmd_%06T"
# openPMD	"1.1.0"
# openPMDextension	0
# software	"openPMD-api"
# softwareVersion	"0.16.1"
# -> add ozzy's general attributes (code, grid/particle)
# -> translate "software" to "pic_code"

# - the ones under "/data/%06T":

# dt
# -> multiply time by /data/%06T["timeUnitSI"]

# - the ones under "/data/%06T/[field path]":

# chargeCorrection	"spectral"
# chargeCorrectionParameters	"period=1"
# currentSmoothing	"Binomial"
# currentSmoothingParameters	"period=1;numPasses=1;compensator=false"
# fieldBoundary	["reflecting","reflecting","reflecting","reflecting"]
# fieldSolver	"PSATD"
# particleBoundary	["absorbing","absorbing","absorbing","absorbing"]

# *****Field variable attributes:*****

# - the ones under each var:

# geometry
# geometryParameters (if exists)
# fieldSmoothing (if exists)
# -> use "dataOrder" to orient array
# -> use "UnitSI"
# -> use "UnitDimension"
# -> use "gridGlobalOffset", "gridSpacing", "position", shape, "gridUnitSI" and "axisLabels" to make axes/coords
#       (careful, can't trust shape if geometry is thetaMode) --> nevermind, get axes from get_field (see docstring of metadata object)

# *****Species attributes:******

# - the ones under each species:

# -> use "HiPACE++_use_reference_unitSI"?
# -> whether pid's are unique
# -> pid from "id" if it exists, otherwise generate
# -> set species name

# ******Species var attributes:*******

# -> get variables from avail_record_components and get_particle
# -> get units etc. from unitSI + unitDimension + HiPACE++_reference_unitSI for each var


# function to preprocess files should go here
def config_openpmd(ds):

    # read fields or particles
    # define units
    # define quantity label
    # pass all relevant attributes
    # make sure orientation of axes is correct
    # define axes with quantities and units

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

    # sort out what will be read and pass configuration to a open_mfdataset function call

    try:
        if len(files) > 0:

            # Parse records keyword

            # - map out all available records

            op_obj = OpenPMDTimeSeries(os.path.commonpath(files), check_all_files=False)

            fld_records = op_obj.avail_fields
            part_species = op_obj.avail_species

            # fld_records, part_species = _find_all_records_openpmd(files)
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
                    case _:
                        if rec in fld_records:
                            # proceed, read field data
                            pass
                        elif rec in part_species:
                            # proceed, read particle species data
                            pass
                        else:
                            raise ValueError(
                                f"Can't find record '{rec}' in OpenPMD file(s)."
                            )

            else:

                if all([rec in fld_records for rec in records]):
                    # proceed, read only subset of records
                    pass
                elif all([rec in part_species for rec in records]):
                    raise ValueError(
                        f"""Please choose one particle species to read at a time. For example:

                        ds_{records[0]} = ozzy.open("openpmd", filename, records='{records[0]}')
                        ds_{records[1]} = ozzy.open("openpmd", filename, records='{records[1]}')
                        """
                    )
                else:
                    raise ValueError(
                        f"""
                        Provided 'records' list is invalid. The reason might be because records are a mix of field and particle records, they are non-existent, or they have ambiguous names (such as the component 'r').

                        Accepted options are:\n
                        \t- 'fields' | 'grid' | 'mesh' | 'meshes': read all grid-based variables\n
                        \t- [name of grid-based variable] | [list of several grid-based variable names]: read a subset of the grid-based variables
                        \t  Available variables: {string_fld_records}\n
                        \t- [name of particle species]: particle data for one species
                        \t  Available species: {string_part_species}
                        """
                    )

        else:
            raise OSError
        # code to read list of files

        # call xr.open_mfdataset, pass configuration: whether fields or particles, pass list of variables

    except OSError:
        ds = new_dataset()

    return ds


# Defines specific methods for data from this code
class Methods:
    """_There are currently no OpenPMD-specific methods._"""

    ...
