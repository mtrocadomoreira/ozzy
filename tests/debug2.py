import xarray as xr

from ozzy_refactor.ozdataset import OzzyDatasetBase  # noqa

ds1 = xr.Dataset()  # noqa

ds2 = OzzyDatasetBase()

ods = OzzyDatasetBase(data_origin="lcode")

print(ds2.pic_data_type)
