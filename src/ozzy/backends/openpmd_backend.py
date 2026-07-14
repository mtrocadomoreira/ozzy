# *********************************************************
# Copyright (C) 2026 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import os
import re

import dask.array as da
import h5py
import numpy as np
import xarray as xr
from openpmd_viewer import OpenPMDTimeSeries
from pint.errors import DimensionalityError
from tqdm import tqdm

from ..new_dataobj import new_dataarray, new_dataset
from ..physunits.units import ureg as u  # noqa
from ..utils import force_str_to_list, stopwatch, tex_format, unpack_attr

# TODO: include HiPACE++_reference_unitSI (under species var attributes)

# ---------------------------------------------------------------------------- #
#                    Define constants and utility functions                    #
# ---------------------------------------------------------------------------- #

# ------------------ Required constants for any ozzy backend ----------------- #

general_regex_pattern: str = r"(\w+?)(\d{6,8}).(h5|bp)"
general_file_endings: str | list[str] = ["h5", "bp"]
quants_ignore: None | list[str] | str = None

# ------------- Symbol replacement for labels of OpenPMD records ------------- #

# - general OpenPMD

_openpmd_symbols = {
    "rho": r"\\rho",
    r"[a-z]": lambda matchobj: matchobj.group(0),
    r"u([a-z])": lambda matchobj: f"p_{matchobj.group(1)}",
    "charge": "Q",
    "mass": r"m_\\mathrm{sp}",
}

# - HiPACE++

_hipace_vars = re.compile(r"([uwjEB])([xyz]{0,1})((?:\^2){0,1})_{0,1}([\w-]*)")


def _hipace_vars_repl(matchobj):
    out = matchobj.group(1)
    comp = matchobj.group(2)
    spec = matchobj.group(4)
    sqr = matchobj.group(3)
    if (comp != "") & (spec == ""):
        out = out + f"_{comp}"
    elif (comp != "") & (spec != ""):
        out = out + "_{" + comp + r",\\mathrm{" + spec + r"}}"
    elif (comp == "") & (spec != ""):
        out = out + r"_\\mathrm{" + spec + "}"
    if sqr != "":
        out = out + r"^2"
    return out


_hipace_symbols = {
    "ExmBy": "E_x - B_y",
    "EypBx": "E_y + B_x",
    "Psi": r"\\Psi",
    "rhomjz": r"\\rho - j_z / c ",
    _hipace_vars: _hipace_vars_repl,
    r"rho_(\w+)": lambda matchobj: r"\\rho_\\mathrm{" + matchobj.group(1) + "}",
    "chi": r"\\chi",
    "laserChi": r"\\chi_\\mathrm{laser}",
    "|a^2|": r"|a^2|",
    "laserEnvelope": r"\\text{laser~envelope}",
}

# ------------------------- Parsing of physical units ------------------------ #

_si_derived_units = {
    (0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0): "Hz",
    (1.0, 1.0, -2.0, 0.0, 0.0, 0.0, 0.0): "N",
    (-1.0, 1.0, -2.0, 0.0, 0.0, 0.0, 0.0): "Pa",
    (2.0, 1.0, -2.0, 0.0, 0.0, 0.0, 0.0): "J",
    (2.0, 1.0, -3.0, 0.0, 0.0, 0.0, 0.0): "W",
    (0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0): "C",
    (2.0, 1.0, -3.0, -1.0, 0.0, 0.0, 0.0): "V",
    (2.0, 1.0, -3.0, -2.0, 0.0, 0.0, 0.0): "ohm",
    (-2.0, -1.0, 3.0, 2.0, 0.0, 0.0, 0.0): "S",
    (-2.0, -1.0, 4.0, 2.0, 0.0, 0.0, 0.0): "F",
    (2.0, 1.0, -2.0, -2.0, 0.0, 0.0, 0.0): "H",
    (0.0, 1.0, -2.0, -1.0, 0.0, 0.0, 0.0): "T",
    (2.0, 1.0, -2.0, -1.0, 0.0, 0.0, 0.0): "Wb",
    (1.0, 1.0, -3.0, -1.0, 0.0, 0.0, 0.0): "V/m",
    (-3.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0): "C/m**3",
}
"""Look-up dictionary for unit conversion

Maps exponents of International System of Quantities to SI derived units. 
Exponents refer to the following quantities: 
[length, mass, time, electric current, temperature, amount of substance, 
luminous intensity]
"""


def _exponents_to_unit(isq_exp: list[float]):
    try:
        assert len(isq_exp) == 7
    except AssertionError:
        raise ValueError(
            "Error parsing physical units: expecting a list of seven exponents for each quantity of the International System of Quantities"
        )
    return (
        1
        * u.m ** isq_exp[0]
        * u.kg ** isq_exp[1]
        * u.s ** isq_exp[2]
        * u.A ** isq_exp[3]
        * u.K ** isq_exp[4]
        * u.mol ** isq_exp[5]
        * u.cd ** isq_exp[6]
    )


# ---------------------------------------------------------------------------- #
#                   Main code to read and parse OpenPMD files                  #
# ---------------------------------------------------------------------------- #

# HACK: re.sub is unpredictable, especially with special symbols; need to work on this


def get_tex_label(
    rec: str,
    comp: str | None = None,
    m: int | str | None = None,
    include_mode: bool = False,
) -> str:

    # First make any replacements foreseen at top of this module

    all_symbols = _openpmd_symbols | _hipace_symbols

    for k, v in all_symbols.items():
        if re.fullmatch(k, rec) is not None:
            out = re.sub(k, v, rec)
            break
        else:
            out = rec

    # Replace 't' when it is a component (FBPIC)

    if comp == "t":
        comp = r"\vartheta"

    # Then add component and mode subscript if applicable

    if (comp is None) | (comp == ""):
        if (include_mode) & (m != "all"):
            out = out + "_{" + f"m = {m}" + "}"
    else:
        if (include_mode) & (m != "all"):
            out = out + "_{" + comp + f",m={m}" + "}"
        else:
            out = out + f"_{comp}"

    # Eliminate whitespaces

    out = out.replace(" ", "")

    return tex_format(out)


def compactualize_units(quant, extremum: float) -> tuple[float, str]:

    quant_comp = extremum * quant
    quant_comp = quant_comp.to_compact()
    comp_factor = (1 * quant_comp.units / quant.units).to_base_units().magnitude
    units_latex_string = f"{quant_comp.units:~L}".replace(" ", "")

    # Workaround for pint printing µ
    units_latex_string = units_latex_string.replace("\xb5", "\\mu ")

    return (comp_factor, units_latex_string)


def get_tex_units(isq_exp: list[float], extremum: float) -> tuple[float, str]:

    quant = _exponents_to_unit(isq_exp)

    if tuple(isq_exp) in _si_derived_units:

        quant_str = _si_derived_units[tuple(isq_exp)]

        try:
            quant = quant.to(quant_str)
        except DimensionalityError:
            raise DimensionalityError(
                "Failed to convert OpenPMD unit dimensions to SI-derived units"
            )

    comp_factor, units_latex = compactualize_units(quant, extremum)

    return (comp_factor, tex_format(units_latex))


def set_sensible_units(
    da: xr.DataArray, isq_exp: list[float] | None = None, unit_init: str | None = None
) -> xr.DataArray:

    if (isq_exp is not None) | (unit_init is not None):

        data_max_value = abs(da).max(skipna=True).compute().data

        if isq_exp is not None:
            comp_factor, units_label = get_tex_units(isq_exp, data_max_value)
        elif unit_init is not None:
            quant_init = 1 * u(unit_init)
            comp_factor, units_str = compactualize_units(quant_init, data_max_value)
            units_label = tex_format(units_str)

        if comp_factor != 1:
            da = da / comp_factor

        da.attrs["units"] = units_label

        return da

    else:
        print(
            "Warning: Did not receive any unit information for sensible unit conversion. Returning DataArray as is."
        )
        return da


def openpmd_concat_time(ds: xr.Dataset | list[xr.Dataset]) -> xr.Dataset:

    ds = xr.concat(
        ds, "t", fill_value=np.nan, join="outer", combine_attrs="drop_conflicts"
    )
    ds = ds.sortby("t")

    return ds


def read_fields(
    op_obj: OpenPMDTimeSeries, fields: list[str], separate_theta_modes: bool
) -> xr.Dataset:

    if "all" in fields:
        fields = op_obj.avail_fields

    field_metadata = op_obj.fields_metadata
    iters_all = op_obj.iterations
    time_all = op_obj.t

    # Create empty dataset to add to

    ds_fields = new_dataset(pic_data_type="grid", data_origin="openpmd")
    all_ax_vars = []

    for rec in fields:

        # Loop through components

        if len(field_metadata[rec]["avail_components"]) == 0:
            field_metadata[rec]["avail_components"] = [None]

        for comp in field_metadata[rec]["avail_components"]:
            # Define comp when there are no components
            if comp is None:
                comp = ""

            # Deal with mode-decomposed cylindrical geometry

            if field_metadata[rec]["geometry"] == "thetaMode":

                all_modes = set(field_metadata[rec]["avail_circ_modes"]) - {"all"}
                all_modes = [int(item) for item in all_modes]

                if separate_theta_modes:
                    modes = all_modes
                    rec_names = [rec + comp + f"_m{im}" for im in all_modes]
                    include_mode_in_label = True
                else:
                    modes = ["all"]
                    rec_names = [rec + comp]
                    include_mode_in_label = False

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

                # Concatenate all DataArrays along time

                da_rec = openpmd_concat_time(da_rec_t)

                # Assign labels and metadata to this record/quantity

                rec_label = get_tex_label(rec, comp, m, include_mode_in_label)
                da_rec.attrs["long_name"] = rec_label

                da_rec = set_sensible_units(
                    da_rec, isq_exp=metadata.field_attrs["unitDimension"]
                )

                for meta_attr in [
                    "geometry",
                    "type",
                    "geometryParameters",
                    "fieldSmoothing",
                    "gridGlobalOffset",
                ]:
                    if meta_attr in field_metadata[rec]:
                        da_rec.attrs[meta_attr] = field_metadata[rec][meta_attr]

                # Add mode information

                if "geometry" in field_metadata[rec]:
                    if field_metadata[rec]["geometry"] == "thetaMode":
                        da_rec.attrs["theta_mode"] = m

                # Add complete DataArray of quantity to overall Dataset

                ds_fields[rec_name] = da_rec

        all_ax_vars = all_ax_vars + ax_vars

    # Set axis and time metadata

    ds_fields["t"].attrs["long_name"] = tex_format("t")
    ds_fields["t"] = set_sensible_units(ds_fields["t"], unit_init="s")

    # CAUTION: assumption here: that all spatial axes have units of m
    space_vars = set(all_ax_vars)
    for ax_var in space_vars:
        ds_fields[ax_var].attrs["long_name"] = tex_format(ax_var)
        ds_fields[ax_var] = set_sensible_units(ds_fields[ax_var], unit_init="m")

    # Add iteration coordinate

    ds_fields = ds_fields.assign_coords(coords={"iter": ("t", iters_all)})
    ds_fields["iter"].attrs["long_name"] = "Iteration"

    return ds_fields


def read_species(
    op_obj: OpenPMDTimeSeries, species: str, sp_var_attrs: dict
) -> xr.Dataset:

    iters_all = op_obj.iterations
    time_all = op_obj.t

    # Get available quantities
    all_quants = op_obj.avail_record_components[species]

    ds_t = []

    for it, tval in zip(tqdm(iters_all), time_all):
        pass

        all_data = op_obj.get_particle(all_quants, iteration=it, species=species)
        all_data_dict = {k: v for k, v in zip(all_quants, all_data)}

        if "w" in all_data_dict:
            weighting = all_data_dict["w"]
        else:
            weighting = None

        ds_tmp = new_dataset(pic_data_type="part", data_origin="openpmd")

        for iq, quant in enumerate(all_quants):

            data = da.from_array(all_data_dict[quant], chunks="auto")

            if quant in sp_var_attrs:
                quant_attrs = sp_var_attrs[quant]
                if quant[0] != "u":
                    if (quant_attrs["macroWeighted"] == 0) & (
                        quant_attrs["weightingPower"] != 0
                    ):
                        data = data * weighting ** quant_attrs["weightingPower"]
                if "unitSI" in quant_attrs:
                    if quant_attrs["unitSI"] != 1:
                        data = data * quant_attrs["unitSI"]

            if quant == "id":
                quant = "pid"
                sp_var_attrs[species]["unique_pids"] = True

            # Add variable to single time Dataset
            ds_tmp[quant] = xr.DataArray(data, dims="pid")

        # Assign pid coordinates if they don't exist
        if "id" not in all_quants:
            ds_tmp = ds_tmp.assign_coords(
                {"pid": ("pid", np.arange(ds_tmp.sizes["pid"]))}
            )
            sp_var_attrs[species]["unique_pids"] = False

        ds_tmp = ds_tmp.expand_dims(
            dim={"t": [tval]},
            axis=1,
        )
        ds_t.append(ds_tmp)

    # Concatenate along time

    ds = openpmd_concat_time(ds_t)

    # If shape of mass or charge is different than one of the other variables, drop them
    # (and do not use "id" as the other variable to compare)

    other_vars = list({*all_quants} - {"charge", "mass", "id"})
    for var in ["charge", "mass"]:
        if ds[var].shape != ds[other_vars[0]].shape:
            ds = ds.drop_vars(var)

    # Set quantity label and units

    for var in ds.data_vars:
        var_label = get_tex_label(var)
        if var_label != "":
            ds[var].attrs["long_name"] = var_label

        if (var[0] == "u") & (len(var) == 2):
            if sp_var_attrs["mass"]["value"] != 0:
                ds[var].attrs["units"] = r"$m_\mathrm{sp} c$"
            else:
                ds[var] = set_sensible_units(ds[var], unit_init="kg*m/s")
        else:
            ds[var] = set_sensible_units(
                ds[var], isq_exp=sp_var_attrs[var]["unitDimension"]
            )

    # Set general attributes

    ds = ds.assign_attrs(**sp_var_attrs[species])

    # Add iteration coordinate

    ds = ds.assign_coords(coords={"iter": ("t", iters_all)})
    ds["iter"].attrs["long_name"] = "Iteration"

    return ds


def read_sort(
    files: list[str],
    separate_theta_modes: bool,
    fields: list[str] | None = None,
    species: str | None = None,
    *args,
    **kwargs,
) -> xr.Dataset:

    # Read all general metadata
    # TODO: do same for ADIOS2 format

    with h5py.File(files[-1], "r") as f:

        # General attributes

        gen_attrs = {k: unpack_attr(v) for k, v in dict(f.attrs).items()}

        # Time factor

        time_paths = list(f["/data"].keys())
        time_attrs = f["/data"][time_paths[0]].attrs

        if "timeUnitSI" in time_attrs:
            time_factor = time_attrs["timeUnitSI"]
        else:
            time_factor = 1

        # Data-type-specific metadata

        fld_path = gen_attrs["meshesPath"]
        sp_path = gen_attrs["particlesPath"]

        if fields is not None:

            fld_attrs_obj = f[f"/data/{time_paths[0]}/{fld_path}"].attrs
            fld_attrs = {k: unpack_attr(v) for k, v in dict(fld_attrs_obj).items()}

        elif species is not None:

            sp_obj = f[f"/data/{time_paths[0]}/{sp_path}{species}"]
            sp_attrs_obj = sp_obj.attrs
            sp_attrs = {k: unpack_attr(v) for k, v in dict(sp_attrs_obj).items()}

            sp_position_attrs = dict(
                f[f"/data/{time_paths[0]}/{sp_path}{species}/position"].attrs
            )
            sp_momentum_attrs = dict(
                f[f"/data/{time_paths[0]}/{sp_path}{species}/momentum"].attrs
            )

            sp_var_attrs = {}

            def visit_part_quants(item, obj):
                if item[:-1] == "momentum/":
                    comp = item[-1]
                    sp_var_attrs["u" + comp] = dict(obj.attrs) | sp_momentum_attrs
                elif item[:-1] == "position/":
                    comp = item[-1]
                    sp_var_attrs[comp] = dict(obj.attrs) | sp_position_attrs
                elif (item == "position") | (item == "momentum"):
                    pass
                elif item == "weighting":
                    sp_var_attrs["w"] = dict(obj.attrs)
                else:
                    sp_var_attrs[item] = dict(obj.attrs)
                return None

            sp_obj.visititems(visit_part_quants)

            # Save charge and mass information as general attribute

            sp_var_attrs[species] = {}
            sp_var_attrs[species]["unique_pids"] = False
            sp_var_attrs[species]["species_name"] = species

            for var in ["charge", "mass"]:
                if sp_var_attrs[var]["macroWeighted"] == 1:
                    prefix = "macroparticle"
                else:
                    prefix = "species"
                value = sp_var_attrs[var]["value"]

                if sp_var_attrs[var]["unitSI"] != 1:
                    value = sp_var_attrs[var]["unitSI"] * value

                # Workaround for wrong unitDimension of mass variable
                if (var == "mass") & all(
                    sp_var_attrs[var]["unitDimension"] == [1, 0, 0, 0, 0, 0, 0]
                ):
                    sp_var_attrs[var]["unitDimension"] = np.array([0, 1, 0, 0, 0, 0, 0])

                var_unit = _exponents_to_unit(sp_var_attrs[var]["unitDimension"])
                unit_string = f"{var_unit.to_compact().units}"

                sp_var_attrs[species][f"{prefix}_{var}"] = value
                sp_var_attrs[species][f"{prefix}_{var}_units"] = unit_string

    # Create openPMD object again, checking consistency

    op_obj = OpenPMDTimeSeries(os.path.commonpath(files), check_all_files=True)

    if fields is not None:
        ds = read_fields(op_obj, fields, separate_theta_modes)
        ds = ds.assign_attrs(**fld_attrs)

    elif species is not None:

        ds = read_species(op_obj, species, sp_var_attrs)
        ds = ds.assign_attrs(**sp_attrs)

    # Set general metadata

    ds = ds.assign_attrs(**gen_attrs)

    # HACK: unclear whether it would be useful to have specific
    # methods for different simulation codes. But it's probably
    # a bad idea to put this information in the "data_origin"
    # attribute along with the value "openpmd"

    # # - Add simulation code information (without version number)

    # if "software" in gen_attrs:
    #     software_string = gen_attrs["software"]
    #     if len(software_string) > 0:
    #         sw_regex = r"(\w+)( [\d.]+)*"
    #         matchobj = re.match(sw_regex, software_string)
    #         sw_name = matchobj.group[1]

    # Multiply by time factor if necessary

    if time_factor != 1.0:
        ds["t"] = ds["t"] * time_factor

    # Set time metadata

    ds["t"].attrs["long_name"] = tex_format("t")
    ds["t"] = set_sensible_units(ds["t"], unit_init="s")

    return ds


@stopwatch
def read(
    files: list[str],
    records: str | list[str] | None = None,
    separate_theta_modes: bool = False,
    **kwargs,
) -> xr.Dataset:
    """
    Read selected records from openPMD files into a [Dataset][xarray.Dataset].

    Parameters
    ----------
    files : list[str]
        Paths to the openPMD files to read.
    records : str, list[str], or None, optional
        Records to read from the files. Accepted values are:

        - `'fields'`, `'grid'`, `'mesh'`, or `'meshes'` to read all grid-based variables
        - the name of one grid-based variable
        - a list of grid-based variable names
        - `'particles'` or `'part'` to read particle data when exactly one particle species is present
        - the name of one particle species

        If `None`, an error is raised listing the available records.
    separate_theta_modes : bool, default: False
        Whether to keep each azimuthal mode separate for each data variable when reading grid-based data in geometries with azimuthal mode decomposition. If `True`, returns each data variable reconstructed from all azimuthal modes.

    Returns
    -------
    xarray.Dataset
        Dataset containing the requested openPMD records. If no files are provided, or the files cannot be opened, an empty dataset is returned.

    Raises
    ------
    NotImplementedError
        If the files appear to be in ADIOS2 format, identified by the `.bp` suffix.
    ValueError
        If `records` is `None`, if the requested record is unavailable, if multiple particle species are requested, or if the `records` list mixes unsupported or ambiguous record names.

    Examples
    --------

    ???+ example "Read all grid-based variables"

        ```python
        ds = ozzy.open("openpmd", files, records="fields")

        # ds is an xarray.Dataset containing all available grid-based variables.
        ```

    ???+ example "Read one particle species"

        ```python
        ds_electrons = ozzy.open("openpmd", files, records="electrons")

        # ds_electrons is an xarray.Dataset containing particle data for the
        # `electrons` species, if that species exists in the files.
        ```
    """

    # TODO: accept vectorial components of field quantities as well (e.g. Er, Ez)

    try:
        if len(files) > 0:

            # Check file format (HDF5 or ADIOS2)

            if files[-1][-2:] == "bp":
                raise NotImplementedError(
                    "The files appear to be in ADIOS2 format (.bp). This has not been implemented yet."
                )

            # Parse records keyword

            # - map out all available records

            op_obj = OpenPMDTimeSeries(os.path.commonpath(files), check_all_files=False)

            fld_records = op_obj.avail_fields
            part_species = op_obj.avail_species

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
                        ds = read_sort(files, separate_theta_modes, fields=["all"])
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
                            ds = read_sort(
                                files, separate_theta_modes, species=part_species[0]
                            )
                    case _:
                        if rec in fld_records:
                            ds = read_sort(files, separate_theta_modes, fields=[rec])
                        elif rec in part_species:
                            ds = read_sort(files, separate_theta_modes, species=rec)
                        else:
                            raise ValueError(
                                f"Can't find record '{rec}' in OpenPMD file(s)."
                            )

            else:

                if all([rec in fld_records for rec in records]):
                    ds = read_sort(files, separate_theta_modes, fields=records)
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

    except OSError:
        ds = new_dataset()

    return ds


# ---------------------------------------------------------------------------- #
#                           Backend-specific methods                           #
# ---------------------------------------------------------------------------- #


class Methods:
    """_There are currently no openPMD-specific methods._"""

    # HACK: add method to convert units to normalized, given a reference plasma density -> but maybe make this a general method for all ozzy data objects

    ...
