<!-- TODO: explain pid's and tags -->

# OSIRIS backend

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

    When there is a moving window, the `'_box'` suffix is appended to the name of the dimension(s) concerned, since xarray requires the same window axes to concatenate grid data along time. The actual, time-varying axes are stored as a separate coordinate indexed to the same dimension.

    For example, for a two-dimensional window with a longitudinal axis initially spanning $[-14,2] ~ k_p^{-1}$, the [Dataset][xarray.Dataset] obtained from the simulation data is shown below, depending on whether the simulation moves the window along `x1` or not.

    === With a moving window

        ```python
            print(ds)
            # <xarray.Dataset>
            # Dimensions:  (x2: 256, x1_box: 512, t: 31)
            # Coordinates:
            #     x1       (t, x1_box) float64 -13.98 -13.95 -13.92 ... 301.9 302.0 302.0
            #   * x2       (x2) float64 0.0 0.03125 0.0625 0.09375 ... 7.875 7.906 7.938 7.969
            #   * x1_box   (x1_box) float64 -13.98 -13.95 -13.92 -13.89 ... 1.922 1.953 1.984
            #   * t        (t) float64 0.0 10.0 20.0 30.0 40.0 ... 270.0 280.0 290.0 300.0
            #     iter     (t) int32 0 1280 2560 3840 5120 ... 33280 34560 35840 37120 38400
            # Data variables:
            #     charge   (x2, x1_box, t) float32 dask.array<chunksize=(256, 512, 1), meta=np.ndarray>
            # Attributes:
            #     move c:     [1 0]
            #     ...
        ```

    === No moving window

        ```python
            print(ds)
            # <xarray.Dataset>
            # Dimensions:  (x2: 256, x1: 512, t: 31)
            # Coordinates:
            #   * x1       (x1) float64 -13.98 -13.95 -13.92 -13.89 ... 1.922 1.953 1.984
            #   * x2       (x2) float64 0.0 0.03125 0.0625 0.09375 ... 7.875 7.906 7.938 7.969
            #   * t        (t) float64 0.0 10.0 20.0 30.0 40.0 ... 270.0 280.0 290.0 300.0
            #     iter     (t) int32 0 1280 2560 3840 5120 ... 33280 34560 35840 37120 38400
            # Data variables:
            #     charge   (x2, x1, t) float32 dask.array<chunksize=(256, 512, 1), meta=np.ndarray>
            # Attributes: 
            #     move c:     [0 0]
            #     ...
        ```


Some quantities stored in OSIRIS HDF5 files are given specific labels and numbers instead of the ones attached to the file. These quantities are stored in a dictionary that maps the quantity name in the HDF5 files to a list containing two elements, the first for the new label and the second for the new units. The list for these quantities can be inspected with:
```python
import ozzy as oz
print(oz.backends.osiris_backend.special_vars)
# {'ene': ['$E_{\\mathrm{kin}}$', '$m_\\mathrm{sp} c^2$']}
```

## Entry-point `read` function

::: ozzy.backends.osiris_backend
    options:
      members:
      - read