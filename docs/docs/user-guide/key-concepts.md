
# Key concepts

Here are the most important things to understand about ozzy and the upstream packages it uses.

## Data objects

!!! info
    This is a very brief introduction to the data objects used by ozzy. 
    Please refer to the ["Data structures" section of xarray's User Guide](https://docs.xarray.dev/en/latest/user-guide/data-structures.html) for a complete tour.

As [mentioned before](getting-started/index.md), [xarray][xarray] offers two types of object that can store information alongside a given dataset. You can imagine these data objects as a plot, in the sense that they contain all the information that a plot usually does: the data iself, axes, variable names and units, notes, etc.

### DataArray

A [DataArray][xarray.DataArray] is the smallest unit of a data object in xarray. In the analogy of the data objects as plots, a DataArray would correspond to a single curve in a chart.

A DataArray has the following properties:

|  DataArray `da`    |                          |
| :---------- | :----------------------------------- |
| `da.values`       | the data, in the form of an [ndarray][numpy.ndarray] |
| `da.dims`       | the names of the data's dimensions (e.g. `'y','x'` instead of `0,1`) |
| `da.coords`    | the axes for each dimension (there may be several for the same dimension), which are called [Coordinates][xarray.Coordinates] in xarray |
| `da.attrs` | any other user-defined metadata |


### Dataset

A [Dataset][xarray.Dataset] is a bundle of one or more DataArrays (in fact it can also be empty). In the analogy of the data plot, a Dataset can be any combination of plots and subplots; from a single curve to an ensemble of several charts with different axes and different data curves.

This is particularly useful when we have several quantities (i.e., DataArrays, or variables) that are all defined on the same axes, for example the different components of the electric field. However, the different variables in a Dataset don't *have to* share axes and dimensions.

A Dataset object contains:

|  Dataset `ds` |                          |
| :------------- | :----------------------------------- |
| `ds.data_vars` | the quantities inside the Dataset, available as a dictionary mapping their names to the respective DataArrays |
| `ds.dims`      | the names of the dimensions associated with the different quantity arrays |
| `ds.coords`    | axes, i.e. [xarray Coordinates][xarray.Coordinates] |
| `ds.attrs`     | any other user-defined metadata |


### Specific methods

Besides some general methods that are available to data objects (see [*Data object methods*](../reference/data-objects/index.md)), ozzy also makes different methods available depending on the type of data (see [*Data-type-specific methods*](../reference/data-objects/data-type-methods.md)) and the simulation code that produced it (see [*Backend-specific methods*](../reference/data-objects/backend-methods.md)).
Access to these specific methods is granted based on two attributes: `'pic_data_type'` and `'data_origin'`. These attributes should be set when initializing a new data object with [`ozzy.DataArray()`][ozzy.core.DataArray] or [`ozzy.Dataset()`][ozzy.core.Dataset]. For example:

!!! example "Initializing new data objects"

    === "DataArray"

        ```python
        import ozzy as oz
        da = oz.DataArray(pic_data_type='grid', data_origin='ozzy')
        print(da)
        # <xarray.DataArray ()>
        # array(nan)
        # Attributes:
        #     pic_data_type:  grid
        #     data_origin:    ozzy
        ```

    === "Dataset"

        ```python
        import ozzy as oz
        ds = oz.Dataset(pic_data_type='grid', data_origin='ozzy')
        print(ds)
        # <xarray.Dataset>
        # Dimensions:  ()
        # Data variables:
        #     *empty*
        # Attributes:
        #     pic_data_type:  grid
        #     data_origin:    ozzy
        ```

The following values are accepted for these two attributes:

|  Attribute    |  Accepted values                   | Default      |
| :---------- | :----------------------------------- | :----------- |
| `'pic_data_type'`       | `'grid'`, `'part'` | `None` |
| `'data_origin'`       | `'ozzy'`, `'osiris'`, `'lcode'` | `None` |


### Table of data objects

The [`open_compare`][ozzy.core.open_compare] function allows the user to open several sets of data from different simulation folders and/or simulation codes, and returns them organized into a table where each row corresponds to a simulation folder and each column to a quantity. The returned object is in fact a [`pandas.DataFrame`][pandas.DataFrame], which is a powerful implementation of a table with column and row labels and fast look-up methods (see [Pandas][pandas] for more information).


## Indexing

!!! info
    Please see the [section on "Indexing and selecting data" in xarray's User Guide](https://docs.xarray.dev/en/latest/user-guide/indexing.html) for a complete explanation of available indexing methods.

Besides standard array indexing (such as `a[i,j]`), the main ways to select slices of data in DataArrays or Datasets are `.sel()` and `.isel()`. A simple example is shown below.

???+ example annotate "Example of indexing methods"

    === "DataArray"

        ```python
        import numpy as np
        import ozzy as oz

        # Create a 2D DataArray
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-3, 3, 30)
        X, Y = np.meshgrid(x, y)
        ne = np.exp(-(X**2 + Y**2) / 2)

        da = oz.DataArray(
            data=ne,
            dims=["y", "x"],
            coords={"x": x, "y": y},
            name="ne",
            pic_data_type="grid",
            data_origin="ozzy",
        )

        # Select line-out at center of x axis
        # The following are all equivalent
        da[:, 24]
        da.isel(x=24) #(1)!
        da.sel(x=0.0, method="nearest") #(2)!

        print(da.sel(x=0.0, method="nearest"))
        # <xarray.DataArray 'ne' (y: 30)>
        # array([...])
        # Coordinates:
        #     x        float64 0.102
        #   * y        (y) float64 -3.0 -2.793 -2.586 -2.379 ... 2.379 2.586 2.793 3.0
        # Attributes:
        #     pic_data_type:  grid
        #     data_origin:    ozzy
        ```

        1. See [`xarray.DataArray.isel`][xarray.DataArray.isel].
        2. See [`xarray.DataArray.sel`][xarray.DataArray.sel].

   
    === "Dataset"

        ```python
        import ozzy as oz
        import numpy as np

        # Create coordinates
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-3, 3, 30)
        X, Y = np.meshgrid(x, y)

        # Create data variables
        ne = np.exp(-(X**2 + Y**2) / 2)
        Ex = np.sin(x) * np.exp(-x**2 / 10)

        ds = oz.Dataset(
            data_vars={
                'ne': (['y', 'x'], ne),
                'Ex': (['x'], Ex)
            },
            coords={'x': x, 'y': y},
            attrs={
                'pic_data_type': 'grid',
                'data_origin': 'ozzy'
            }
        )

        # Select data at center of x axis
        # The following are equivalent
        # Note that positional indexing does not work on Datasets
        ds.isel(x=24) #(1)!
        ds.sel(x=0.0, method="nearest") #(2)!

        print(ds.sel(x=0.0, method="nearest")) #(3)!
        # <xarray.Dataset>
        # Dimensions:  (y: 30)
        # Coordinates:
        #     x        float64 0.102
        #   * y        (y) float64 -3.0 -2.793 -2.586 -2.379 ... 2.379 2.586 2.793 3.0
        # Data variables:
        #     ne       (y) float64 0.01105 0.02012 0.0351 ... 0.0351 0.02012 0.01105
        #     Ex       float64 0.1018
        # Attributes:
        #     pic_data_type:  grid
        #     data_origin:    ozzy

        ```

        3. See [`xarray.Dataset.isel`][xarray.Dataset.isel].
        4. See [`xarray.Dataset.sel`][xarray.Dataset.sel].
        5. Notice how each data variable inside the Dataset was sliced.

When data objects are organized in a table ([`pandas.DataFrame`](pandas.DataFrame)), items can be accessed either via the row and column labels or with a numerical index, with [`.loc`][pandas.DataFrame.loc] or [`.at`][pandas.DataFrame.at] and [`.iloc`][pandas.DataFrame.iloc] or [`.iat`][pandas.DataFrame.iat], respectively.

???+ example "Indexing elements in a DataFrame (table)"

    ```python
    import ozzy as oz
    import pandas as pd
    
    # Create empty Datasets to serve as placeholders
    ds_sim1_ne = oz.Dataset()
    ds_sim1_Ez = oz.Dataset()
    ds_sim2_ne = oz.Dataset()
    ds_sim2_Ez = oz.Dataset()

    # Create a DataFrame with Dataset objects, 
    # similar to the output of ozzy.open_compare()
    df = pd.DataFrame(
        [[ds_sim1_ne, ds_sim2_ne], [ds_sim1_Ez, ds_sim2_Ez]],
        index=["Simulation 1", "Simulation 2"],
        columns=["ne", "Ez"],
    )
    print(df)
    #               ne  Ez
    # Simulation 1  []  []
    # Simulation 2  []  []
    ```
    We obtain one of the empty datasets when we select a single table cell:

    ```python
    # The following are equivalent
    df.loc["Simulation 1", "Ez"]
    df.iloc[0, 1]
    df.at["Simulation 1", "Ez"]
    df.iat[0, 1]

    print(df.iloc[0, 1])
    # <xarray.Dataset>
    # Dimensions:  ()
    # Data variables:
    #     *empty*
    # Attributes:
    #     pic_data_type:  None
    #     data_origin:    None
    ```

    Slicing a row or column returns a [`pandas.Series`][pandas.Series] object.

    ```python
    # Selecting the second row
    df.loc["Simulation 2"]
    # Selecting the first column
    df.iloc[:, 0]

    print(df.loc["Simulation 2"])
    # ne    []
    # Ez    []
    # Name: Simulation 2, dtype: object
    ```

## Data chunking and lazy loading

A common issue with simulation files is their sheer size, which often implies long loading, processing and plotting times. One strategy to deal with extremely large files is to load them into the machine's working memory in smaller "chunks", which is called data chunking. Another strategy is called lazy loading, where data is not actually processed until absolutely necessary.
Both of these techniques are used in ozzy thanks to the [Dask](https://www.dask.org/) package, which is also [integrated into xarray](https://docs.xarray.dev/en/stable/user-guide/dask.html).

Files read by ozzy will generally be [Dask arrays](https://docs.dask.org/en/stable/array.html) under the hood. This does not change much in the way you interact with the data object, with the exception that operations on it will not actually be computed until you explicitly say so, with the `.compute`(1) or `.load`(2) methods. Below is an example demonstrating how this works.
{ .annotate }

1.  See [`xarray.DataArray.compute`][xarray.DataArray.compute] or [`xarray.Dataset.compute`][xarray.Dataset.compute].
2.  See [`xarray.DataArray.load`][xarray.DataArray.compute] or [`xarray.Dataset.load`][xarray.Dataset.compute].

!!! info

    Please see ["Using Dask with xarray" from the xarray User Guide](https://docs.xarray.dev/en/stable/user-guide/dask.html#using-dask-with-xarray) for more detail.

???+ example "Understanding lazy loading"

    ```python
    import dask.array as da
    import numpy as np
    import ozzy as oz

    # Create a large dataset that would typically be too big to fit in memory
    large_data = np.random.rand(1000000, 1000)  # 1 million x 1000 array

    # Initialize a Dataset with chunking
    dask_data = da.from_array(large_data, chunks=(100000, 100))
    ds = oz.Dataset(
        {"large_variable": (["x", "y"], dask_data)},
    )
    print("-> Dataset created, but data not loaded into memory yet.")
    print(ds)

    # Perform a computation that doesn't require loading all the data
    result = ds.large_variable.mean(dim="y")
    print("\n-> Computation defined, but not yet executed:")
    print(result)

    # Trigger actual computation
    print("\n-> Triggering computation:")
    result = result.compute()
    print(result)
    ```
    This produces the following output:
    ```
    -> Dataset created, but data not loaded into memory yet.
    <xarray.Dataset>
    Dimensions:         (x: 1000000, y: 1000)
    Dimensions without coordinates: x, y
    Data variables:
        large_variable  (x, y) float64 dask.array<chunksize=(100000, 100), meta=np.ndarray>
    Attributes:
        pic_data_type:  None
        data_origin:    None

    -> Computation defined, but not yet executed:
    <xarray.DataArray 'large_variable' (x: 1000000)>
    dask.array<mean_agg-aggregate, shape=(1000000,), dtype=float64, chunksize=(100000,), chunktype=numpy.ndarray>
    Dimensions without coordinates: x

    -> Triggering computation:
    <xarray.DataArray 'large_variable' (x: 1000000)>
    array([0.50542762, 0.50724898, 0.48675328, ..., 0.50791182, 0.5187294 ,
        0.49262436])
    Dimensions without coordinates: x
    ```
