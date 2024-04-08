import xarray as xr


def new_dataset(
    pic_data_type: str | list[str] | None = None,
    data_origin: str | list[str] | None = None,
    *args,
    **kwargs,
) -> xr.Dataset:
    ds = xr.Dataset(*args, **kwargs)
    ds = ds.assign_attrs({"pic_data_type": pic_data_type, "data_origin": data_origin})
    return ds
