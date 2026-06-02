# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import os
import re

import dask.array as da
import xarray as xr
from openpmd_viewer import OpenPMDTimeSeries
from tqdm import tqdm

from ..new_dataobj import new_dataarray, new_dataset
from ..utils import force_str_to_list, stopwatch, tex_format

general_regex_pattern: str = r"\w+?(\d{6,8}).h5"
general_file_endings: str | list[str] = ["h5", "bp"]
quants_ignore: None | list[str] | str = None


# Replace some variable names with appropriate symbols

# - general OpenPMD
openpmd_symbols = {"rho": r"\rho"}

# - HiPACE++

hipace_vars = re.compile(r"([uwjEB])([xyz]{0,1})((?:\^2){0,1})_{0,1}([\w-]*)")


def hipace_vars_repl(matchobj):
    out = matchobj.group(1)
    comp = matchobj.group(2)
    spec = matchobj.group(4)
    sqr = matchobj.group(3)
    if (comp != "") & (spec == ""):
        out = out + f"_{comp}"
    elif (comp != "") & (spec != ""):
        out = out + "_{" + comp + r",\mathrm{" + spec + r"}}"
    elif (comp == "") & (spec != ""):
        out = out + r"_\mathrm{" + spec + "}"
    if sqr != "":
        out = out + r"^2"
    return out


hipace_symbols = {
    "ExmBy": "E_x - B_y",
    "EypBx": "E_y + B_x",
    "Psi": r"\Psi",
    "rhomjz": r"\rho - j_z / c ",
    "rho": r"\rho",
    hipace_vars: hipace_vars_repl,
    r"rho_(\w+)": lambda matchobj: r"\rho_\mathrm{" + matchobj.group(1) + "}",
    "chi": r"\chi",
    "laserChi": r"\chi_\mathrm{laser}",
    "|a^2|": r"|a^2|",
    "laserEnvelope": r"\text{laser envelope}",
}


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

# - the ones under "/data/%06T":

# dt
# -> multiply time by /data/%06T["timeUnitSI"]

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


def get_tex_label(rec, comp, m, include_mode):

    # First make any replacements foreseen at top of this module

    all_symbols = openpmd_symbols | hipace_symbols

    for k, v in all_symbols.items():
        if re.fullmatch(k, rec) is not None:
            out = re.sub(k, v, rec)
        else:
            out = rec

    # Then add component and mode subscript if applicable

    if comp is not None:
        if (include_mode) & (m != "all"):
            out = out + "_{" + comp + f",m={m}" + "}"
        else:
            out = out + f"_{comp}"
    else:
        if (include_mode) & (m != "all"):
            out = out + "_{" + f"m = {m}" + "}"

    return tex_format(out)


@stopwatch
def openpmd_concat_time(ds: xr.Dataset | list[xr.Dataset]) -> xr.Dataset:

    # Example from lcode backend:
    # ds = xr.concat(ds, "t", fill_value={"q": 0.0}, join="outer")
    # ds = ds.sortby("t")
    # ds = ds.astype(float).chunk("auto")

    # TODO: how to deal with non-unique particle IDs

    # Simplest implementation:
    ds = xr.concat(ds, "t", fill_value={"q": 0.0}, join="outer")
    ds = ds.sortby("t")

    return ds


def read_fields(op_obj, fields, separate_theta_modes):

    if fields == "all":
        fields = op_obj.avail_fields

    field_metadata = op_obj.fields_metadata
    iters_all = op_obj.iterations
    time_all = op_obj.t

    # create empty dataset to add to

    ds_fields = new_dataset(pic_data_type="grid")

    for rec in fields:

        # Loop through components

        if len(field_metadata[rec]["avail_components"]) == 0:
            field_metadata[rec]["avail_components"] = [None]

        for comp in field_metadata[rec]["avail_components"]:

            # Deal with mode-decomposed cylindrical geomtry

            if field_metadata[rec]["geometry"] == "thetaMode":

                all_modes = set(field_metadata[rec]["avail_circ_modes"]) - {"all"}
                all_modes = [int(item) for item in all_modes]

                if separate_theta_modes:
                    modes = all_modes
                    rec_names = [rec + comp + f"_m{im}" for im in all_modes]
                else:
                    modes = ["all"]
                    allmstring = "".join([str(item) for item in all_modes])
                    rec_names = [rec + comp + f"_m{allmstring}"]

                include_mode_in_label = True

            else:

                modes = ["all"]
                rec_names = [rec + comp]
                include_mode_in_label = False

            print(f"Reading all '{rec + comp}' data:")

            # Loop through all "modes"

            for m, rec_name in zip(modes, rec_names):

                # Iterate along time

                da_rec_t = []
                for it, tval in zip(tqdm(iters_all), time_all):

                    data, metadata = op_obj.get_field(
                        rec, coord=comp, iteration=it, m=m
                    )
                    if metadata.component_attrs["unitSI"] != 1.0:
                        data = data * metadata.component_attrs["unitSI"]
                    if metadata.field_attrs["timeOffset"] != 0.0:
                        tval = tval + metadata.field_attrs["timeOffset"]

                    ndims = len(metadata.axes)
                    ax_vars = [metadata.axes[0], metadata.axes[1]]

                    dda = da.from_array(data, chunks="auto")

                    da_tmp = new_dataarray(
                        name=rec_name, data=dda, dims=ax_vars, attrs={"ndims": ndims}
                    ).expand_dims(
                        dim={"t": [tval]},
                        axis=ndims,
                    )

                    # Assign values for axes

                    for idim, ax_var in enumerate(ax_vars):
                        axis = metadata.__getattribute__(ax_var)

                        if "gridUnitSI" in metadata.field_attrs:
                            if metadata.field_attrs["gridUnitSI"] != 1.0:
                                axis = axis * metadata.field_attrs["gridUnitSI"]
                        elif "gridUnitSIPerDimension" in metadata.field_attrs:
                            if (
                                metadata.field_attrs["gridUnitSIPerDimension"][idim]
                                != 1.0
                            ):
                                axis = (
                                    axis
                                    * metadata.field_attrs["gridUnitSIPerDimension"][
                                        idim
                                    ]
                                )

                        da_tmp = da_tmp.assign_coords({ax_var: (ax_var, axis)})

                    # Append to list with all times for this record

                    da_rec_t.append(da_tmp)

                # Concatenate all datasets along time

                da_rec = openpmd_concat_time(da_rec_t)

                # Assign labels and metadata

                rec_label = get_tex_label(rec, comp, m, include_mode_in_label)

                # rec_units = get_units(metadata.field_attrs["unitDimension"])

                da_rec.attrs["long_name"] = rec_label
                da_rec.attrs["units"] = rec_units
                # if |unit_exp^2| == 1, then it's one of the base units

                # Add complete DataArray of quantity to overall Dataset

                ds_fields[rec_name] = da_rec

            # what about axis units and time units?

            # Set metadata
            # Process axes and general metadata (with last metadata obj)

        pass

    return


def read_fields_t(op_obj, it, fields, separate_theta_modes):

    if fields == "all":
        fields = op_obj.avail_fields

    field_metadata = op_obj.fields_metadata

    for rec in fields:

        # Loop through components

        if len(field_metadata[rec]["avail_components"]) == 0:
            field_metadata[rec]["avail_components"] = [None]

        for comp in field_metadata[rec]["avail_components"]:

            if field_metadata[rec]["geometry"] == "thetaMode":

                # Deal with mode-decomposed cylindrical geomtry

                if separate_theta_modes:
                    modes = set(field_metadata[rec]["avail_circ_modes"]) - {"all"}
                    modes = [int(item) for item in modes]
                else:
                    modes = ["all"]

                for m in modes:

                    data, metadata = op_obj.get_field(
                        rec, coord=comp, iteration=it, m=m
                    )

                    # make dask data array

                    dda = da.from_array(data, chunks="auto")

                    ndims = len(metadata.axes)

                    ds = new_dataset(
                        data_vars={rec: ([metadata.axes[0], metadata.axes[1]], dda)},
                    ).expand_dims(dim={"t": 1}, axis=ndims)
                    ds.attrs["ndims"] = ndims

                    # process physical units

                    # set variable name
                    # add to dataset with metadata

                    get_tex_label(rec, comp, m)

            else:  # No theta modes

                data, metadata = op_obj.get_field(rec, coord=comp, iteration=it)

                get_tex_label(rec, comp)

                # add to dataset with metadata
                pass

            # Set metadata
            # Process axes and general metadata (with last metadata obj)

        pass

    # get array
    # make dask array from array

    return


def read_species_t(op_obj, it):

    # get array
    # make dask array from array

    return


def read_agg(
    files: list[str],
    fields: list[str] | None = None,
    species: str | None = None,
    separate_theta_modes: bool | None = None,
    *args,
    **kwargs,
) -> xr.Dataset:

    # Create openPMD object again, checking consistency

    op_obj = OpenPMDTimeSeries(os.path.commonpath(files), check_all_files=True)
    t_all = op_obj.t
    iters_all = op_obj.iterations

    # Loop along all times

    ds_t = []
    for it in tqdm(iters_all):

        if fields is not None:
            ds_tmp = read_fields_t(op_obj, it, fields, separate_theta_modes)
            pass

        elif species is not None:
            ds_tmp = read_species_t(op_obj, it)
            pass

        ds_t.append(ds_tmp)

    print("  Concatenating along time...")
    ds = openpmd_concat_time(ds_t)

    # Set general metadata

    # ****General attributes:***** (get through h5py/adios2)

    # - the ones under "/":

    # iterationEncoding	"fileBased"
    # iterationFormat	"openpmd_%06T"
    # openPMD	"1.1.0"
    # openPMDextension	0
    # software	"openPMD-api"
    # softwareVersion	"0.16.1"
    # -> add ozzy's general attributes (code, grid/particle)
    # -> translate "software" to "pic_code"

    # IF FIELDS:
    # - the ones under "/data/%06T/[field path]":

    # chargeCorrection	"spectral"
    # chargeCorrectionParameters	"period=1"
    # currentSmoothing	"Binomial"
    # currentSmoothingParameters	"period=1;numPasses=1;compensator=false"
    # fieldBoundary	["reflecting","reflecting","reflecting","reflecting"]
    # fieldSolver	"PSATD"
    # particleBoundary	["absorbing","absorbing","absorbing","absorbing"]

    return ds


@stopwatch
def read(
    files: list[str],
    records: str | list[str] | None = None,
    separate_theta_modes: bool = False,
    **kwargs,
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
