
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/docs/assets/ozzy_logo_dark.svg" >
  <source media="(prefers-color-scheme: light)" srcset="docs/docs/assets/ozzy_logo.svg">
    <img width="250" title="ozzy logo" alt="ozzy logo" src="docs/docs/assets/ozzy_logo.svg">
</picture>

# 

Ozzy is a data visualization and data wrangling Python package geared towards **particle-in-cell (PIC) simulations** and the **plasma physics** community.

Ozzy exploits the [xarray](https://xarray.dev/) package as well as several other upstream packages to make data manipulation as lazy as possible.

> [!WARNING]
> The documentation for the first version of ozzy is still in development. The documentation website is not online yet.

### **Why ozzy?**

- **Any simulation code**
    
    Read and plot simulation data written by any PIC simulation code. Write the backend to parse the data once and move on. *Currently available*: [OSIRIS](https://osiris-code.github.io/) and [LCODE](https://lcode.info/).

- **Labeled dimensions** (thanks to [xarray](https://xarray.dev/))

    Think like a physicist, not like a software engineer. You'll never have to wonder which numerical index corresponds to the $x$ dimension of that array again.      
  
- **No file size too large** (thanks to [Dask](https://www.dask.org/))

    Chunking and lazy-loading of large data files are handled automatically by [xarray](https://xarray.dev/) and [Dask](https://www.dask.org/).

- **Flexible**

    We embrace [xarray](https://xarray.dev/) and [Dask](https://www.dask.org/) data objects, but you don't have to. Easily manipulate your data as trusty [NumPy](https://numpy.org/) arrays whenever convenient.

- **Beautiful plots with one line of code**

    Ozzy lays the groundwork using the dataset's metadata.


## Installation

### pip

### conda

Head to the documentation page to see some examples of how to get started.

## Documentation

All the documentation can be found at ...

## Acknowledgment

Please note that `ozzy.plot` uses two [color maps developed by Fabio Crameri](https://www.fabiocrameri.ch/colourmaps/) by default: `vik` (divergent) and `lipari` (sequential). These color maps should be acknowledged if used in a published image, for example with:

> The Scientific color map lipari[^1] is used in this study to prevent visual distortion of the data and exclusion of readers with colour-vision deficiencies[^2].

More information here.

[^1]: F. Crameri, "Scientific colour maps". Zenodo, Oct. 05, 2023. [doi: 10.5281/zenodo.8409685](http://doi.org/10.5281/zenodo.8409685).

[^2]: F. Crameri, G.E. Shephard, and P.J. Heron, "The misuse of colour in science communication". Nat. Commun. **11**, 5444 (2020). [doi: 10.1038/s41467-020-19160-7](https://doi.org/10.1038/s41467-020-19160-7). 


## License

Copyright (C) 2024 Mariana Moreira - All Rights Reserved 

You may use, distribute and modify this code under the terms of the MIT License.

---

- paul tol
- fonts

"copyright statement, the license notice and the license text"


Xarray bundles portions of pandas, NumPy and Seaborn, all of which are available under a "3-clause BSD" license:

pandas: setup.py, xarray/util/print_versions.py
NumPy: xarray/core/npcompat.py
Seaborn: _determine_cmap_params in xarray/core/plot/utils.py
Xarray also bundles portions of CPython, which is available under the "Python Software Foundation License" in xarray/core/pycompat.py.

Xarray uses icons from the icomoon package (free version), which is available under the "CC BY 4.0" license.

The full text of these licenses are included in the licenses directory.


<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/docs/assets/ozzy_icon_dark.svg" >
  <source media="(prefers-color-scheme: light)" srcset="docs/docs/assets/ozzy_icon.svg">
  <img width="60" title="ozzy icon" alt="ozzy icon" src="docs/docs/assets/ozzy_icon.svg">
</picture>

