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
    The following methods are defined within specific mixin classes: `GridMixin` (`grid_mixin.py`) and `PartMixin` (`part_mixin.py`).

## Grid data

::: ozzy.grid_mixin

## Particle data

::: ozzy.part_mixin
