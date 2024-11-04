
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/docs/assets/ozzy_logo_dark.svg" >
  <source media="(prefers-color-scheme: light)" srcset="docs/docs/assets/ozzy_logo.svg">
    <img width="250" title="ozzy logo" alt="ozzy logo" src="docs/docs/assets/ozzy_logo.svg">
</picture>

# 

Ozzy is a data visualization and data wrangling Python package geared towards **particle-in-cell (PIC) simulations** and the **plasma physics** community.

Ozzy's philosophy is to make the analysis of simulation data originating from multiple simulation codes and often contained in large files as easy as possible by building on the powerful features of the [xarray](https://xarray.dev/) package.


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

> [!IMPORTANT]
> Ozzy requires Python >= 3.10.

A detailed guide is available in the ["Installation" page of the documentation](https://mtrocadomoreira.github.io/ozzy/user-guide/installation/).

We highly recommend installing ozzy in its own virtual environment.

### conda (recommended)

```bash
conda install ozzy-pic
```

### pip

```bash
python3 -m pip install ozzy-pic
```


Head to the documentation page to see some [examples of how to get started](https://mtrocadomoreira.github.io/ozzy/user-guide/getting-started/).

## Documentation

All the documentation can be found at [https://mtrocadomoreira.github.io/ozzy](https://mtrocadomoreira.github.io/ozzy).

## Acknowledgment

Please consider acknowledging ozzy if you use it to produce images or results published in a scientific publication, for example by including the following text in the acknowledgments and/or citing ozzy's Zenodo reference[^1]:

> The data and plots in this publication were processed with ozzy[^1], a freely available data visualization and analysis package.

[^1]: M. Moreira, “Ozzy: A flexible Python package for PIC simulation data analysis and visualization”. Zenodo, Jul. 16, 2024. [doi: 10.5281/zenodo.12752995](https://doi.org/10.5281/zenodo.12752995).

In addition, please note that `ozzy.plot` uses two [color maps developed by Fabio Crameri](https://www.fabiocrameri.ch/colourmaps/) (licensed under an MIT license) by default: vik (diverging) and lipari (sequential). **These color maps should be acknowledged if used in a published image**, for example with:

> The Scientific colour map lipari[^2] is used in this study to prevent visual distortion of the data and exclusion of readers with colour-vision deficiencies[^3].

[^2]: F. Crameri, "Scientific colour maps". Zenodo, Oct. 05, 2023. [doi: 10.5281/zenodo.8409685](http://doi.org/10.5281/zenodo.8409685).

[^3]: F. Crameri, G.E. Shephard, and P.J. Heron, "The misuse of colour in science communication". Nat. Commun. **11**, 5444 (2020). [doi: 10.1038/s41467-020-19160-7](https://doi.org/10.1038/s41467-020-19160-7). 

More information about the colour libraries used by ozzy can be found in the ["Plotting" section of the User Guide]().


## License

Copyright &copy; 2024 Mariana Moreira - All Rights Reserved 

You may use, distribute and modify this code under the terms of the MIT License.

Ozzy bundles [Paul Tol's colour schemes definition](https://personal.sron.nl/~pault/), which is available under a ["3-clause BSD" license](https://opensource.org/license/BSD-3-Clause). The qualitative colour scheme "muted" is used by default in `ozzy.plot`.

The plotting submodule of ozzy (`ozzy.plot`) also bundles a few different fonts under the [SIL Open Font License (OFL)](https://openfontlicense.org/), which is a free and open-source license. The full text of these licenses is included for each font in the fonts directory (`src/ozzy/fonts/`). See more details about the bundled fonts and their copyright notices in the ["License" section of the documentation](https://mtrocadomoreira.github.io/ozzy/about/license/#fonts).



<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/docs/assets/ozzy_icon_dark.svg" >
  <source media="(prefers-color-scheme: light)" srcset="docs/docs/assets/ozzy_icon.svg">
  <img width="60" title="ozzy icon" alt="ozzy icon" src="docs/docs/assets/ozzy_icon.svg">
</picture>

