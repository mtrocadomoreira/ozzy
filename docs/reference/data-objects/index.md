
# Data Objects

Ozzy is implemented according to the "accessor" model of [xarray](https://xarray.dev/) (see [_Extending xarray using accessors_](https://docs.xarray.dev/en/latest/internals/extending-xarray.html)). This means that all the Ozzy functionality built on top of xarray data objects can be accessed via `xarray.Dataset.ozzy.<method>` or `xarray.DataArray.ozzy.<method>`.


## ::: ozzy.accessors.OzzyDataset

## ::: ozzy.accessors.OzzyDataArray