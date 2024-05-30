# Welcome to

<figure markdown="span">
  ![ozzy logo](assets/ozzy_logo.svg#only-light){ width="280" }
  ![ozzy logo](assets/ozzy_logo_dark.svg#only-dark){ width="280" }
  <figcaption>PIC simulation data analysis for the lazy and impatient</figcaption>
</figure>

Ozzy is a data visualization and data wrangling tool geared towards particle-in-cell (PIC) simulations and the plasma physics community. Ozzy's philosophy is to make the analysis of simulation data originating from multiple simulation codes and often contained in large files as easy as possible.

Ozzy exploits the [xarray](https://xarray.dev/) package as well as several other upstream packages to make data manipulation as lazy as possible.

[Get started](user-guide/installation.md){ .md-button .md-button--primary}

## Why ozzy?

<div class="grid cards" markdown>

-   :material-chart-box-multiple:{ .lg .middle } __Any simulation code__

    ---

    Read and plot simulation data written by any PIC simulation code. Write the backend to parse the data once and move on.

    [:octicons-arrow-right-24: Reading files](user-guide/reading-files.md)

-   :material-axis-arrow:{ .lg .middle } __Labeled dimensions__

    ---

    Think like a physicist, not like a software engineer. You'll never have to wonder which numerical index corresponds to the $x$ dimension of that array again.

    <!-- Refer to labeled dimensions and dataset variables instead of having to wonder which numerical index corresponds to the $x$ dimension of that array again. -->

    [:octicons-arrow-right-24: Indexing](user-guide/key-concepts.md)

-   :material-chart-box-plus-outline:{ .lg .middle } __Keep the metadata__

    ---

    _Which file was this again?_ Let the code stay organized so you don't have to. Attributes go where the array goes.

    [:octicons-arrow-right-24: Data objects](user-guide/key-concepts.md)

-   :material-arm-flex:{ .lg .middle } __No file size too large__

    ---

    Chunking and lazy-loading of large data files (_ugh, right?_) are handled automatically by [xarray](https://xarray.dev/) and [Dask](https://www.dask.org/).

    [:octicons-arrow-right-24: Array chunks](user-guide/key-concepts.md)

-   :material-lightning-bolt:{ .lg .middle } __Fast and furious__

    ---
    Vectorized operations, fast [Pandas](https://pandas.pydata.org/)-like indexing, and more to make your analysis run even faster.

    [:octicons-arrow-right-24: Notes on speed](user-guide/speed.md)

-   :material-yoga:{ .lg .middle } __Stay flexible__

    ---

    We embrace [xarray](https://xarray.dev/) and [Dask](https://www.dask.org/), but you don't have to. Easily manipulate your data as trusty [NumPy](https://numpy.org/) arrays whenever convenient.

    [:octicons-arrow-right-24: Data analysis](user-guide/analysis.md)

-   :material-flower-tulip:{ .lg .middle } __Beautiful plots with one line of code__

    ---

    Ozzy lays the groundwork using the dataset's metadata.

    [:octicons-arrow-right-24: Plotting](user-guide/plotting.md)

-   :material-scale-balance:{ .lg .middle } __Open Source, MIT__

    ---

    Ozzy is licensed under MIT and available on [GitHub](https://github.com/mtrocadomoreira/ozzy).

    [:octicons-arrow-right-24: License](about/license.md)

</div>


## Acknowledgment



## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

