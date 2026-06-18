# openPMD backend

## Available file types

At the moment, ozzy can read openPMD files in HDF5 format, whether with group-, file- or variable-based [iteration encoding](https://openpmd-api.readthedocs.io/en/0.15.1/usage/concepts.html#iteration-and-series).

## Default metadata

The metadata from openPMD files is mostly converted into xarray `attrs`, while unit-related metadata is also used to rescale the actual data.

The backend reads metadata from two places:

- `openpmd_viewer.OpenPMDTimeSeries`, especially `fields_metadata` and the `metadata` returned by `get_field(...)`.
- Raw HDF5 attributes via `h5py`

For field data, `unitSI` is used to rescale field values, `timeOffset` to shift `t`, and `gridUnitSI` / `gridUnitSIPerDimension` to rescale spatial coordinates. Then each data variable, or `DataArray`, gets a TeX label, compact display units derived from `unitDimension`, and selected attributes like `geometry`, `type`, `geometryParameters`, `fieldSmoothing`, `gridGlobalOffset`, plus `theta_mode` for geometries with azimuthal mode decomposition.

For particle data, metadata is collected from the attributes both at particle and species level. These attributes are used for weighting correction, `unitSI` conversion, labels and units. The dataset for each species will contain two additional attributes: `species_name` and `unique_pids`. Particle `id`, when present, is renamed to `pid`.



## Entry-point `read` function

::: ozzy.backends.openpmd_backend
    options:
      members:
      - read