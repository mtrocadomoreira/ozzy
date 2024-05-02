import os

import dask
import xarray as xr
from tqdm import tqdm

from ..new_dataobj import new_dataset
from ..utils import print_file_item, stopwatch

general_regex_pattern = (
    r"([\w-]*?)[-_]?(\d*)[-_]?([\w]*?)\.(h5|hdf)"  # r"([\w-]+)-(\d{6})\.(h5|hdf)"
)
general_file_endings = ["h5"]
quants_ignore = None

# TODO: write docstrings


def config_ozzy(ds):
    if ("t" in ds.coords) & ("t" not in ds.dims):
        assert ds["t"].size == 1
        ds = ds.expand_dims(dim={"t": 1}, axis=ds[list(ds)[0]].ndim)

    return ds


@stopwatch
def read(files, **kwargs):
    try:
        with dask.config.set({"array.slicing.split_large_chunks": True}):
            try:
                ds = xr.open_mfdataset(files, chunks="auto", engine="h5netcdf")
                [print_file_item(file) for file in files]
            except ValueError:
                ds_t = []
                [print_file_item(file) for file in files]
                for file in tqdm(files):
                    ds_tmp = xr.open_dataset(file, engine="h5netcdf", chunks="auto")
                    ds_t.append(config_ozzy(ds_tmp))
                print("\nConcatenating along time... (this may take a while)")
                ds = xr.concat(ds_t, "t", fill_value={"q": 0.0})

            ds = ds.assign_attrs(
                source=os.path.commonpath(files),
                files_prefix=os.path.commonprefix([os.path.basename(f) for f in files]),
            )

            for metadata in ["pic_data_type", "data_origin"]:
                if metadata in ds.attrs:
                    if ds.attrs[metadata] == "":
                        ds.attrs[metadata] = None

    except OSError:
        ds = new_dataset()

    return ds


# Defines specific methods for data from this code
class Methods:
    """Mixin class for operations exclusively on ozzy data.

    The methods in this class are accessible to a data object[^1] when `<data_obj>.attrs['data_origin'] == 'ozzy'`.

    [^1]: A data object (`<data_obj>`) may be a [Dataset][xarray.Dataset] or a [DataArray][xarray.DataArray].

    This class is currently empty.

    """

    ...
