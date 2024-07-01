<!-- TODO: explain defaults etc. -->

# OSIRIS backend definition

## Available file types

At the moment, the following types of OSIRIS output files can be read by ozzy:

- [x] grid (`DENSITY`, `FLD`, `PHA`)
- [x] particles (`RAW`)
- [ ] particle tracks (`TRACKS`)


## Default metadata

Ozzy simply imports most of the metadata stored in OSIRIS HDF5 files as [Dataset][xarray.Dataset] attributes (all attribute names are converted to lower case). 

The `'LABEL'` or `'LABELS'` attributes are renamed to `'long_name'`, since this is the default property that xarray looks for when labelling quantities in plots. All the label and unit metadata is encased in `'$...$'` so as to be rendered as LaTeX formulas in plots.

In general, the names of the data dimensions correspond to the notation in OSIRIS (`'x1'`, `'x2'`, `'x3'`), while the time dimension is given the name `'t'`. An additional coordinate called `'iter'`, which contains the iteration number for a given time step, is indexed to the time dimension and attached to each dataset. 

!!! important "Naming convention with a moving window"

    


