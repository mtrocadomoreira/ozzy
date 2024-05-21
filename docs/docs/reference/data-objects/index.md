
# Data object methods

Ozzy is implemented according to [xarray](https://xarray.dev/)'s accessor model[^1]. All the ozzy functionality built on top of xarray data objects ([Datasets][xarray.Dataset] or [DataArrays][xarray.DataArray]) can then be accessed via 

=== "DataArray"

    ```python
    xarray.DataArray.ozzy.<method>
    ```

=== "Dataset"

    ```python
    xarray.Dataset.ozzy.<method>
    ```

[^1]: See [_Extending xarray using accessors_](https://docs.xarray.dev/en/latest/internals/extending-xarray.html)

???+ example

    Saving a [Dataset][xarray.Dataset] object:

    ```python
    >>> import ozzy as oz
    >>> ds = oz.Dataset()
    >>> ds.ozzy.save('test.h5')
         -> Saved file "test.h5" 
        -> 'save' took: 0:00:00.212650
    ```

??? note "Note for developers"

    Ozzy's custom methods are defined in two accessor classes:

    * `ozzy.accessors.OzzyDataset`
    * `ozzy.accessors.OzzyDataArray`

    Strictly speaking, the path to each method should be for example `ozzy.accessors.[OzzyDataset|OzzyDataArray].<method>`. However, this documentation page presents the methods as if they were under `xarray.[Dataset|DataArray].ozzy.<method>`, which is effectively how the user can access them.

    The methods in each accessor class can access the actual data object via `<data_obj>.ozzy._obj`. This is only relevant when defining new methods in the accessor classes.

    !!! example

        ```python
        >>> import xarray as xr
        >>> import ozzy as oz
        >>> ds = xr.Dataset()
        >>> assert ds == ds.ozzy._obj
        True
        ```

## xarray.Dataset.ozzy

### ::: ozzy.accessors.OzzyDataset

## xarray.DataArray.ozzy

### ::: ozzy.accessors.OzzyDataArray
