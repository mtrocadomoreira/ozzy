
# Welcome to

<figure markdown="span">
  ![ozzy logo](assets/ozzy_logo.svg#only-light){ width="280" }
  ![ozzy logo](assets/ozzy_logo_dark.svg#only-dark){ width="280" }
  <figcaption>PIC simulation data analysis for the lazy and impatient</figcaption>
</figure>

Ozzy is a data visualization and data wrangling tool geared towards particle-in-cell (PIC) simulations and the plasma physics community. Ozzy's philosophy is to make the analysis of simulation data originating from multiple simulation codes and often contained in large files as easy as possible by building on the powerful features of the [xarray](https://xarray.dev/) package.

<p markdown="span" style="margin:2em; text-align:center;"> 
    [Get started](user-guide/installation/index.md){ .md-button .md-button--primary}
</p>


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

    [:octicons-arrow-right-24: Indexing](user-guide/key-concepts.md#indexing)

-   :material-chart-box-plus-outline:{ .lg .middle } __Keep the metadata__

    ---

    _Which file was this again?_ Let the code stay organized so you don't have to. Attributes go where the array goes.

    [:octicons-arrow-right-24: Data objects](user-guide/key-concepts.md#data-objects)

-   :material-arm-flex:{ .lg .middle } __No file size too large__

    ---

    Chunking and lazy-loading of large data files (_ugh, right?_) are handled automatically by [xarray](https://xarray.dev/) and [Dask](https://www.dask.org/).

    [:octicons-arrow-right-24: Data chunking and lazy-loading](user-guide/key-concepts.md#data-chunking-and-lazy-loading)

-   :material-lightning-bolt:{ .lg .middle } __Fast and furious__

    ---
    Vectorized operations, fast [Pandas](https://pandas.pydata.org/)-like indexing, and more to make your analysis run even faster.

    [:octicons-arrow-right-24: Notes on speed](user-guide/speed.md "Page under development")

-   :material-yoga:{ .lg .middle } __Stay flexible__

    ---

    We embrace [xarray](https://xarray.dev/) and [Dask](https://www.dask.org/), but you don't have to. Easily manipulate your data as trusty [NumPy](https://numpy.org/) arrays whenever convenient.

    [:octicons-arrow-right-24: Data analysis](user-guide/analysis.md "Page under development")

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

Please consider acknowledging ozzy if you use it to produce images or results published in a scientific publication, for example by including the following text in the acknowledgments or citing ozzy's Zenodo reference[^1]:

> The data and plots in this publication were processed with ozzy[^1], a freely available data visualization and analysis package.

[^1]: M. Moreira, “Ozzy: A flexible Python package for PIC simulation data analysis and visualization”. Zenodo, Jul. 16, 2024. [doi: 10.5281/zenodo.12752995](https://doi.org/10.5281/zenodo.12752995).

In addition, please note that the plotting submodule of ozzy uses two [color maps developed by Fabio Crameri](https://www.fabiocrameri.ch/colourmaps/) (licensed under an MIT license) by default: `vik` (diverging) and `lipari` (sequential). **These color maps should be acknowledged if used in a published image**, for example with:

> The Scientific colour map lipari[^2] is used in this study to prevent visual distortion of the data and exclusion of readers with colour-vision deficiencies[^3].

[^2]: F. Crameri, "Scientific colour maps". Zenodo, Oct. 05, 2023. [doi: 10.5281/zenodo.8409685](http://doi.org/10.5281/zenodo.8409685).

[^3]: F. Crameri, G.E. Shephard, and P.J. Heron, "The misuse of colour in science communication". Nat. Commun. **11**, 5444 (2020). [doi: 10.1038/s41467-020-19160-7](https://doi.org/10.1038/s41467-020-19160-7). 

See the ["Plotting" section of the User Guide](user-guide/plotting.md) for more information.
