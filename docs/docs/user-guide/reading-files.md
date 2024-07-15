# Reading files

One of the main motivations behind ozzy is to be able to easily integrate different simulation file formats into the same plotting and analysis workflow (in this case with Python). In addition, we try to make it easy to add new backend instructions to ozzy to parse new file formats.

Here is a list of simulation file formats that ozzy can read currently or which will be implemented soon (besides [ozzy's own format](../reference/backends/submodules/ozzy.md), of course):

<div class="annotate" markdown>

- [x] [OSIRIS](https://osiris-code.github.io/) (1)
- [x] [LCODE](https://lcode.info/2d/) (2)
- [ ] [openPMD](https://github.com/openPMD)

</div>

1.  Please see the reference page for the [OSIRIS backend submodule](../reference/backends/submodules/osiris.md) for more details. Not all types of simulation output may be available yet.
2.  Please see the reference page for the [LCODE backend submodule](../reference/backends/submodules/lcode.md). Not all types of simulation output may be available yet.
   

There are three main functions to open simulation files:

* [`open`][ozzy.open] - for a single file

* [`open_series`][ozzy.open_series] - for a time series of files, where each file corresponds to a different time
* [`open_compare`][ozzy.open_compare] - for any combination of quantities and folder structures; particularly useful for comparisons across different runs, either stemming from a single simulation code or several

In general, these functions expect the file format(s) as their first argument.

## Reading a single file

In order to open a single file, the path to the file must be specified. This path can be relative, absolute, and it can include `~` as a shortcut to the user's home directory as well as [glob patterns](https://en.wikipedia.org/wiki/Glob_(programming))(1).
{ .annotate }

1.  Note that ozzy will only open the first file in case it finds several files matching the pattern.

!!! example "Opening a single file"

    === "OSIRIS"

        ```python
        import ozzy as oz
        ds = oz.open('osiris', '~/path/to/file/e1-000020.h5')
        ```

    === "LCODE"

        LCODE simulation files do not contain any axis information, so we can supply the simulation window size in order to define the axis coordinates (optional).

        ```python
        import ozzy as oz
        ds = oz.open(
            'lcode', 'path/to/file/ez02500.swp', 
            axes_lims = {'x1': (-100,0.0), 'x2': (0.0, 6.0)}
        )
        ```

    === "ozzy"

        ```python
        import ozzy as oz
        ds = oz.open('ozzy', '/Users/Ada/Desktop/Ex_max_mean.h5')
        ```


## Reading a series of files


The output from PIC simulations is often dumped into files at certain timesteps, and therefore often organized according to simulation time. Ozzy can easily treat all the files related to a given quantity as a single dataset with an additional time axis.

!!! example annotate "Opening files as a time series"

    === "OSIRIS"

        For this example, let's say we have the following typical OSIRIS output folder structure:

        ```
        .
        └── my_sim/
            └── MS/
                ├── FLD/
                │   └── e1/
                │       ├── e1-000000.h5
                │       ├── e1-000001.h5
                │       ├── e1-000002.h5
                │       ├── ...
                │       └── e1-000050.h5
                ├── DENSITY
                └── RAW
        ```
        To open the $E_z$ field data (called `e1` in OSIRIS) as a time series, we could use:

        ``` python
        import ozzy as oz
        ds = oz.open_series(
            'osiris', 
            'my_sim/**/e1-*.h5', 
            nfiles=10,#(1)!
        )
        ```

        1.  We use the optional `nfiles` argument to open only the first 10 files.


    === "LCODE"

        Let's say we have the following folder containing LCODE $E_z$ field data both as 2D maps and on-axis line-outs:

        ```
        .
        └── my_lcode_sim/
            ├── ez00200.swp
            ├── ez00400.swp
            ├── ez00600.swp
            ├── ...
            ├── ez02000.swp
            ├── xi_00200.swp
            ├── xi_00400.swp
            ├── xi_00600.swp
            ├── ...
            ├── xi_02000.swp
            ├── xi_Ez_00200.swp
            ├── xi_Ez_00400.swp
            ├── xi_Ez_00600.swp
            ├── ...
            └── xi_Ez_02000.swp
        ```

        We can read the 2D field maps with:

        ```python
        import ozzy as oz
        ds = oz.open_series(
            'lcode', 
            'my_lcode_sim/ez*.swp', 
            axes_lims={'x1': (-100,0.0), 'x2': (0.0, 6.0)}, #(1)!
        )
        ```

        1.  Appending information about the simulation window so that the Dataset contains axis information ([Coordinates][xarray.Coordinates]).

        We could also read the lineouts of $E_z$ with:

        ```python
        import ozzy as oz
        ds = oz.open_series('lcode', 'my_lcode_sim/xi_Ez_*.swp')
        ```
        Note that we do not need to specify the axis limits with the keyword argument `axes_lims` since ozzy automatically tries to obtain the $\xi$ axis information from the `xi_?????.swp` files.

    === "ozzy"

        Given the following directory, which contains a time series of ozzy data in HDF5 format:

        ```
        /usr/
        └── ada/
            └── analysis/
                └── my_data/
                    ├── Ez_0001.h5
                    ├── Ez_0002.h5
                    ├── Ez_0003.h5
                    ├── ...
                    └── Ez_0050.h5
        ```
        We can open the first three files with:

        ``` python
        import ozzy as oz
        ds = oz.open_series('ozzy', '~/my_data/Ez_*.h5', nfiles=3)
        ```


## Reading many different types of files

We often want to compare the output of several different simulations, or "runs", for the same quantity. The  [`open_compare`][ozzy.open_compare] function tries to make this comparison as easy as possible, organizing the imported data in a table(1) with labels for each different case and quantity.
{ .annotate }

1.  For more information about the format of this table, see [*Table of data objects* in *Key concepts*](key-concepts.md#table-of-data-objects).


!!! example "Opening multiple files for comparison"

    Let's say we want to compare field data from multiple runs which are organized in the following folder structure:

    ```
    .
    └── MySimulations/
        ├── OSIRIS/
        │   ├── run_1/
        │   │   └── e1-000020.h5
        │   └── run_2/
        │       └── e1-000020.h5
        └── LCODE/
            ├── run_1/
            │   └── ez02500.swp
            └── run_2/
                └── ez05000.swp
    ```
    We can use the following arguments to exclude the folder `LCODE/run_2` (since it corresponds to the wrong time in our example) and read the rest of the files:

    ```python
    import ozzy as oz

    df = oz.open_compare(
        file_types=['osiris', 'lcode'],
        path='/MySimulations',
        runs=['**/run_1', 'OSIRIS/run_2'],
        quants=['e1', 'ez'],
        axes_lims={'x1': (-100, 0), 'x2': (0, 6)},
    )
    print(df)
    #                 e1    ez
    # OSIRIS/run_1  [ds]   []
    # OSIRIS/run_2  [ds]   []
    # LCODE/run_1    []   [ds]
    ```
    Individual datasets can be accessed for example with:

    ```python
    osiris_run1_e1 = df.at['OSIRIS/run_1', 'e1']
    lcode_run1_ez = df.at['LCODE/run_1', 'ez']
    ```

<!-- TODO: convert run to a coordinate -->

### Manipulating the comparison table

Below are a couple of examples demonstrating how the [DataFrame][pandas.DataFrame] returned by `open_compare` can be manipulated with the help of methods like [`pandas.DataFrame.map`][pandas.DataFrame.map] and [`pandas.DataFrame.iterrows`][pandas.DataFrame.iterrows].

!!! example annotate "Convert all datasets to physical units"

    ```python
    import ozzy as oz

    df = oz.open_compare(
        file_types='osiris',
        path='/path/to/simulations',
        runs=['run_1', 'run_2', 'run_3'],
        quants='charge-electrons'
    )

    # Define a function to convert coordinates to physical units
    def convert_to_physical(ds, n0):
        if 'z' not in ds.coords:
            ds = ds.ozzy.coord_to_physical_distance('t', n0, new_coord='z')#(1)!
        return ds
        
    # Define plasma densities for each run
    n0_values = {'run_1': 7e14, 'run_2': 1e18, 'run_3': 3e18}  

    df = df.map(lambda run: convert_to_physical(df.at[run, 'charge-electrons'], n0_values[run]))#(2)!
    ```

    1.  See [`xarray.Dataset.ozzy.coord_to_physical_distance`][ozzy.accessors.OzzyDataset.coord_to_physical_distance].
    2.  See [`pandas.DataFrame.map`][pandas.DataFrame.map].
   

!!! example annotate "Iterate along rows"

    ```python
    import ozzy as oz

    df = oz.open_compare(
        'lcode'
        path='/path/to/simulations',
        runs='run_baseline',
        quants=['er','bf'],
    )

    for run, row in df.iterrows():#(1)!
        print(f"Processing run: {run}")
        ds_er = row['er']
        ds_bf = row['bf']
    ```

    1.  See [`pandas.DataFrame.iterrows`][pandas.DataFrame.iterrows].