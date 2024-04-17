
# General data object methods

## Introduction

Ozzy is implemented according to the "accessor" model of [xarray](https://xarray.dev/) (see [_Extending xarray using accessors_](https://docs.xarray.dev/en/latest/internals/extending-xarray.html)). This means that all the Ozzy functionality built on top of xarray data objects can be accessed with `xarray.Dataset.ozzy.<method>` or `xarray.DataArray.ozzy.<method>`.

## General methods

::: ozzy.ozzy_accessor

## Specific methods depending on the data type

### Grid data - `'grid'`

::: ozzy.grid_mixin

### Particle data - `'part'`

::: ozzy.part_mixin

## Specific methods depending on the file backend

<!-- TODO: get mkdocstrings to find submodule backends -->

### Ozzy - `'ozzy'`

<!-- ::: ozzy.backends.ozzy_backend -->

### OSIRIS - `'osiris'`

<!-- ::: ozzy.backends.osiris_backend -->

### LCODE - `'lcode'`

<!-- ::: ozzy.backends.lcode_backend -->
