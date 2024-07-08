
# Key concepts

## Data objects

!!! info
    This is a very brief introduction to the data objects used by ozzy. 
    Please refer to the ["Data structures" section of xarray's User Guide](https://docs.xarray.dev/en/latest/user-guide/data-structures.html) for a complete tour.

The logic behind [xarray][] (and therefore ozzy) consists of handling numerical data as a "package" that includes the axis information and other metadata besides the actual data itself, as opposed to a simple array with numbers.

This package is the [DataArray][xarray.DataArray]. It contains (let `da` be a DataArray):


`da.values`

:   the data, in the form of an [ndarray][numpy.ndarray]

`da.dims`

:   the names of the data's dimensions (e.g. `'y','x'` instead of `0,1`)

`da.coords`
 
:   the axes for each dimension (there may be several for the same dimension), which are called [Coordinates][xarray.Coordinates] in xarray

`da.attrs`

:   any other user-defined metadata

We can also place several DataArray objects in a larger package: this is a [Dataset][xarray.Dataset]. 

This is particularly useful when we have several quantities that are all defined on the same axes, for example the different components of the electric field. However, the different variables in a Dataset don't *have to* share axes and dimensions. A Dataset object (`ds`) contains:

`ds.data_vars`

:   the quantities inside the Dataset, available in a dictionary mapping their names to the respective DataArrays

`ds.dims`

:   the names of the dimensions associated with the different quantities

`ds.coords`

:    axes, i.e. [xarray Coordinates][xarray.Coordinates]

`ds.attrs`

:   any other user-defined metadata


## Indexing

## Array chunks
