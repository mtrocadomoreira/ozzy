# Welcome to Ozzy

Ozzy is a data viz and data wrangling tool geared towards particle-in-cell (PIC) simulations and the plasma physics community. Ozzy's philosophy is to make the analysis of simulation data originating from multiple simulation codes and often contained in large files as easy as possible.

Ozzy exploits the [xarray](https://xarray.dev/) package as well as several other upstream packages to make data manipulation as lazy as possible.

## Why Ozzy?

* **Generality**

    Read and plot simulation data written by multiple PIC simulation codes. Write the backend to parse a particular type of simulation data once and move on.

* **Think like a physicist, not like a software engineer**

    Refer to labeled dimensions and dataset variables instead of having to wonder which numerical index corresponds to the $x$ dimension of that array again.

* **Let the code stay organized so you don't have to**

    Where the data goes, the metadata goes. So you don't have to wonder what that array was again.

* **No file size too large**
  
    Let the chunking and lazy-loading of large data files be handled automatically by the [Dask](https://www.dask.org/) package.

* **Fast and furious**

    Vectorized operations, fast [Pandas](https://pandas.pydata.org/)-like indexing, and more options to make your code even faster.

* **Flexibility**

    Easily manipulate your data as trusty old [NumPy](https://numpy.org/) arrays if that calls to you.

For full documentation visit [mkdocs.org](https://www.mkdocs.org).

## Getting started

* how does xarray work (datasets, dataarrays, etc)
* how do pandas dataframes work

* `mkdocs new [dir-name]` - Create a new project.
* `mkdocs serve` - Start the live-reloading docs server.
* `mkdocs build` - Build the documentation site.
* `mkdocs -h` - Print help message and exit.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.

