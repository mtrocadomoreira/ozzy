from .utils import stopwatch
from .ozdataset import OzDataset
import os
import re
import collections
import pandas as pd
import xarray as xr
from importlib.resources import files

lcode_data_file = files("ozzy").joinpath("lcode_file_key.csv")
lcode_regex = pd.read_csv(lcode_data_file, sep=";", header=0)

lcode_pattern = r"([\w-]*?)(\d{5}|\d{6}\.\d{3})?[m|w]?\.([a-z]{3})"
lcode_ending = ["swp", "dat", "det", "bin", "bit", "pls"]


def check_file_key(file):
    for row in lcode_regex.itertuples(index=False):
        pattern = row.regex
        match = re.fullmatch(pattern, os.path.basename(file))
        if match is not None:
            break

    return (row, match)


def sort_files_into_quants(files):
    pattern = re.compile(lcode_pattern)
    matches = (pattern.fullmatch(f) for f in files if pattern.fullmatch(f) is not None)
    matchfn = (f for f in files if pattern.fullmatch(f) is not None)

    quants_dict = collections.defaultdict(list)

    for m, f in zip(matches, matchfn):
        # timestr = "" if m.group(2) is None else m.group(2)
        label = m.group(1).strip("_-")  # removesuffix(tstr).
        if f not in quants_dict[label]:
            quants_dict[label].append(f)

    return quants_dict


def sort_quants_into_types(quants_dict):
    qtypes_dict = collections.defaultdict(list)
    for k, v in quants_dict.items():
        file = v[0]

        type_info, match = check_file_key(file)
        cat = type_info.cat
        subcat = type_info.subcat

        # TODO: finish this function


@stopwatch
def lcode_concat_time(ds, files):
    ds = xr.concat(ds, "t", fill_value={"q": 0.0})
    ds.coords["t"].attrs["long_name"] = "$t$"
    ds.coords["t"].attrs["units"] = r"$\omega_p^{-1}$"
    ds = ds.sortby("t")
    ds.attrs["source"] = os.path.commonpath(files)
    ds.attrs["files_prefix"] = os.path.commonprefix(
        [os.path.basename(f) for f in files]
    )

    return ds


def read_lcode_parts(files, pattern_info, as_series=True):
    print("Reading files...")

    ds_t = []
    for file in files:
        print("  - " + file)

        ds_tmp = lcode_parse_parts(file, pattern_info)

        if pattern_info.subcat == "beamfile":
            bfbit_path = os.path.join(os.path.dirname(file), "beamfile.bit")
            if os.path.exists(bfbit_path):
                with open(bfbit_path, "r") as f:
                    thistime = float(f.read())
                ds_tmp = ds_tmp.assign_coords({"t": [thistime]})

        elif pattern_info.subcat != "lost":
            ds_tmp = lcode_append_time(ds_tmp, file)

        ds_t.append(ds_tmp)

    # Get file type of all files so as to allow mix between
    # beamfile and tb*.swp
    subcat_all = [lcode_identify_data_type(f)[0].subcat for f in files]

    if any([(sc == "parts") | (sc == "species") for sc in subcat_all]) & (
        as_series is True
    ):
        print(
            "\nConcatenating along time... \
            (this may take a while for particle data)"
        )
        # t0 = time.process_time()
        ds = lcode_concat_time(ds_t, files)
        # print(" -> Took " + str(time.process_time() - t0) + " s")
    else:
        assert len(ds_t) == 1
        ds = ds_t[0]

    return ds


def read_lcode_grid(files, as_series, pattern_info, match, axes_lims):
    print("Reading files...")

    ds_t = []
    for file in files:
        print("  - " + file)
        ds_tmp = lcode_parse_grid(file, pattern_info, match)

        if pattern_info.time == "single":
            ds_tmp = lcode_append_time(ds_tmp, file)

        ds_t.append(ds_tmp)

    if (not as_series) | (pattern_info.time == "full"):
        assert len(ds_t) == 1
        ds = ds_t[0]

    else:
        print("\nConcatenating along time...")
        ds = lcode_concat_time(ds_t, files)

    if axes_lims is not None:
        ds = coords_from_extent(ds, axes_lims)

    return ds


def read_lcode(files, as_series, axes_lims):
    # assuming files is already sorted into a single type
    # of data (no different kinds of files)
    # TODO: make sure that this accepts a list of files of different quantities (which would be merged in a single dataset)

    pattern_info, match = lcode_identify_data_type(files[0])

    if match is None:
        raise TypeError("Could not identify the type of LCODE data file.")

    match pattern_info.cat:
        case "grid":
            if axes_lims is None:
                print(
                    "\nWARNING: axis extents were not specified. \
                        Dataset object(s) will not have coordinates.\n"
                )
            ds = read_lcode_grid(files, as_series, pattern_info, match, axes_lims)

        case "parts":
            ds = read_lcode_parts(files, pattern_info, as_series)

        case "info":
            raise NotImplementedError(
                "Backend for this type of file has not been \
                    implemented yet. Exiting."
            )

        case "uncat":
            raise NotImplementedError(
                "Backend for this type of file has not been \
                    implemented yet. Exiting."
            )

    return OzDataset(ds)
