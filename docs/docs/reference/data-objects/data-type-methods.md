# Data-type-specific methods

These methods can be accessed via the standard accessor way, i.e.:

`>>> xarray.Dataset.ozzy.<method>`

`>>> xarray.DataArray.ozzy.<method>`

## Grid data - `'grid'`

Accessible if `data_obj.attrs['pic_data_type'] == 'grid'`, where `data_obj` can be an `xarray.Dataset` or `xarray.DataArray`.

::: ozzy.grid_mixin

## Particle data - `'part'`

Accessible if `data_obj.attrs['pic_data_type'] == 'part' `, where `data_obj` can be an `xarray.Dataset` or `xarray.DataArray`.

::: ozzy.part_mixin