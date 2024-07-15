# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import xarray as xr


def new_dataset(
    *args,
    pic_data_type: str | list[str] | None = None,
    data_origin: str | list[str] | None = None,
    **kwargs,
) -> xr.Dataset:
    if len(args) >= 1:
        if isinstance(args[0], xr.Dataset) | isinstance(args[0], xr.DataArray):
            kwargs["attrs"] = args[0].attrs

    ds = xr.Dataset(*args, **kwargs)

    if "pic_data_type" not in ds.attrs:
        ds.attrs["pic_data_type"] = pic_data_type
    if pic_data_type is not None:
        ds.attrs["pic_data_type"] = pic_data_type

    if "data_origin" not in ds.attrs:
        ds.attrs["data_origin"] = data_origin
    if data_origin is not None:
        ds.attrs["data_origin"] = data_origin

    for par in ["pic_data_type", "data_origin"]:
        for var in ds.data_vars:
            if par in ds[var].attrs:
                del ds[var].attrs[par]

    return ds


def new_dataarray(
    *args,
    pic_data_type: str | None = None,
    data_origin: str | None = None,
    **kwargs,
) -> xr.DataArray:
    if len(args) >= 1:
        if isinstance(args[0], xr.DataArray):
            kwargs["attrs"] = args[0].attrs

    da = xr.DataArray(*args, **kwargs)

    if "pic_data_type" not in da.attrs:
        da.attrs["pic_data_type"] = pic_data_type
    if pic_data_type is not None:
        da.attrs["pic_data_type"] = pic_data_type

    if "data_origin" not in da.attrs:
        da.attrs["data_origin"] = data_origin
    if data_origin is not None:
        da.attrs["data_origin"] = data_origin

    return da
