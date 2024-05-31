---
status: in-progress
---

# Backend-specific methods

The methods described in this section are exclusively applicable to specific data formats. In general, these methods can be accessed with:


=== "DataArray"

    ```python
    xarray.DataArray.ozzy.<method>
    ```

=== "Dataset"

    ```python
    xarray.Dataset.ozzy.<method>
    ``` 

<!-- A data object (`<data_obj>`) may be a [Dataset][xarray.Dataset] or a [DataArray][xarray.DataArray]. -->

??? note "Note for developers"
    These methods are defined within a mixin class called `Methods` which should be defined in each backend file (e.g. `backends/ozzy_backend.py`).


=== "Ozzy"

    ::: ozzy.backends.ozzy_backend.Methods

=== "OSIRIS"

    ::: ozzy.backends.osiris_backend.Methods

=== "LCODE"

    ::: ozzy.backends.lcode_backend.Methods


