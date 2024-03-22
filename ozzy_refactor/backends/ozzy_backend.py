import os

import dask

from .. import core as oz
from ..ozdataset import OzzyDatasetBase
from ..utils import print_file_item, stopwatch

general_regex_pattern = r"([\w-]+)-(\d{6})\.(h5|hdf)"
general_file_endings = ["h5"]
quants_ignore = None


def config_ozzy(ds):
    if ("t" in ds.coords) & ("t" not in ds.dims):
        assert ds["t"].size == 1
        ds = ds.expand_dims(dim={"t": 1}, axis=ds[list(ds)[0]].ndim)

    return ds


@stopwatch
def read(files):
    try:
        with dask.config.set({"array.slicing.split_large_chunks": True}):
            try:
                ds = oz.open_mfdataset(files, chunks="auto", engine="h5netcdf")
                print_file_item(file for file in files)
            except ValueError:
                ds_t = []
                for file in files:
                    print_file_item(file)
                    ds_tmp = oz.open_dataset(file, engine="h5netcdf", chunks="auto")
                    ds_t.append(config_ozzy(ds_tmp))
                print("\nConcatenating along time... (this may take a while)")
                ds = oz.concat(ds_t, "t", fill_value={"q": 0.0})

            ds = ds.assign_attrs(
                source=os.path.commonpath(files),
                files_prefix=os.path.commonprefix([os.path.basename(f) for f in files]),
            )

    except OSError:
        ds = OzzyDatasetBase(data_origin="ozzy")

    return OzzyDatasetBase(ds)


# Defines specific methods for data from this code
class Methods: ...
