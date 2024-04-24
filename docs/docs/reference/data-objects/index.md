
# Data Objects

Ozzy is implemented according to the "accessor" model[^1] made available by [xarray](https://xarray.dev/). This means that all the Ozzy functionality built on top of xarray data objects can be accessed via 
```python
xarray.Dataset.ozzy.<method>
```
or 
```python
xarray.DataArray.ozzy.<method>
```

[^1]: See [_Extending xarray using accessors_](https://docs.xarray.dev/en/latest/internals/extending-xarray.html)

???+ example

    Using the `save()` method to save a data object (in this case, a [Dataset][xarray.Dataset]).

    ```python
    >>> import xarray as xr
    >>> import ozzy as oz
    >>> ds = xr.Dataset()
    >>> ds.ozzy.save('test.h5')
    ```

Ozzy's custom methods are defined in two accessor classes:

* `ozzy.accessors.OzzyDataset`
* `ozzy.accessors.OzzyDataArray`

Strictly speaking, the path to each of those methods should be `ozzy.accessors.OzzyDataset.<method>`, for example. However, this documentation page presents the methods as if they were under `xarray.Dataset.ozzy.<method>`, which is effectively how the user can access them.

???+ note "Note for developers"

    The methods in each accessor class can access the actual data object via `data_obj.ozzy._obj`. This is only relevant when defining new methods in the accessor classes.

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
