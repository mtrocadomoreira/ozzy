
# Ozzy backend

When a file is saved via [`Dataset.ozzy.save()`][ozzy.accessors.OzzyDataset.save] or [`DataArray.ozzy.save()`][ozzy.accessors.OzzyDataArray.save], the data and metadata are mapped straightforwardly onto an HDF5 file structure (or NetCDF, if this is the selected format). This backend simply imports the file and ensures that the `'pic_data_type'` and `'data_origin'` are initialized correctly.

## Entry-point `read` function

::: ozzy.backends.ozzy_backend
    options:
      members:
      - read