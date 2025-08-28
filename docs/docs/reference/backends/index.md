# Backends

Please navigate to a specific section for more information about the implementation of each simulation file type.


<div class="grid cards center single-column" markdown>

- [__LCODE__](lcode.md)
- [__OSIRIS__](osiris.md)
- [__ozzy__](ozzy.md)
</div>

If you're looking for the backend-specific methods that you can call on a data object, see [*Data object methods → Backend-specific methods*](../data-objects/backend-methods/index.md).

## Interface class

!!! info

    This section should only be relevant if you're planning to add support for a new backend or for debugging purposes.

    The `Backend` class serves as an interface between [ozzy's main file-reading functions](../../user-guide/reading-files.md) and the modules for each implemented backend. 

<!-- ## ozzy.backend -->

::: ozzy.backend_interface