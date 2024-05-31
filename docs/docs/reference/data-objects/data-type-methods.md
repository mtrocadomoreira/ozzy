---
status: in-progress
---

# Data-type-specific methods

These methods can be accessed via the standard [accessor](index.md) way, i.e.:

=== "DataArray"

    ```python
    xarray.DataArray.ozzy.<method>
    ```

=== "Dataset"

    ```python
    xarray.Dataset.ozzy.<method>
    ```

??? note "Note for developers"
    These methods are defined within specific mixin classes: `GridMixin` (`grid_mixin.py`) and `PartMixin` (`part_mixin.py`).


## ::: ozzy.grid_mixin


## ::: ozzy.part_mixin