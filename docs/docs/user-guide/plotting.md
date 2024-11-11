# Plotting

It is extremely easy to plot [xarray data objects](key-concepts.md#data-objects), for example simply by calling `xarray.DataArray.plot()`. Xarray wraps the [matplotlib][] library and makes its functions available as `DataArray` and `Dataset` methods.

!!! info

    Please consult the ["Plotting" section of xarray's User Guide](https://docs.xarray.dev/en/latest/user-guide/plotting.html) to learn about all of its plotting capabilities.

??? tip "Interactive plots"

    It is also very easy to produce [interactive plots of xarray data objects with hvPlot](https://hvplot.holoviz.org/user_guide/Gridded_Data.html).

Though xarray's plotting capabilities can be used directly, ozzy does some extra aesthetic tinkering when the plotting submodule, [`ozzy.plot`](../reference/plot.md), is loaded. This submodule activates the following defaults (among others):

| Defaults | | 
|------|----|
| Curve color scheme | `'tol.muted'`  |   
| Sequential colormap |  `'cmc.lipari'`  |  
| Diverging colormap |  `'cmc.vik'`   |  
| Font |  Noto Serif  |  


<!-- TODO: examples of lines, scatter, imshow, pcolormesh, etc. -->

<!-- TODO: examples of movie and interactive movie with hvplot -->


## Color maps and schemes

Ozzy aims to make scientific plots as **accessible** and as **scientific** as possible. In accordance with this principle, the default color maps and color schemes in `ozzy.plot` are perceptually uniform and readable by people with color-blindness. However, several color options that fulfill these criteria are available, most of which were developed by [Fabio Crameri](https://www.fabiocrameri.ch/colourmaps/) and [Paul Tol](https://personal.sron.nl/~pault/).

!!! warning "Acknowledging Fabio Crameri's "Scientific colour maps""

    Please note that color maps developed by Fabio Crameri, which includes the default color maps `vik` (diverging) and `lipari` (sequential), should be acknowledged if used in a published image, for example with:

    > The Scientific colour map lipari[^1] is used in this study to prevent visual distortion of the data and exclusion of readers with colour-vision deficiencies[^2].

[^1]: F. Crameri, "Scientific colour maps". Zenodo, Oct. 05, 2023. [doi: 10.5281/zenodo.8409685](http://doi.org/10.5281/zenodo.8409685).

[^2]: F. Crameri, G.E. Shephard, and P.J. Heron, "The misuse of colour in science communication". Nat. Commun. **11**, 5444 (2020). [doi: 10.1038/s41467-020-19160-7](https://doi.org/10.1038/s41467-020-19160-7). 


A sample of all available color maps and color schemes in `ozzy.plot` can be produced with:

```python
import ozzy.plot as oplt
oplt.show_cmaps()
```

## Fonts

Ozzy's plotting submodule also bundles a few different open-source fonts:

* [Crimson Pro](https://fonts.google.com/specimen/Crimson+Pro)
* [Maitree](https://fonts.google.com/specimen/Maitree?query=maitree)
* [Noto Serif](https://fonts.google.com/noto/specimen/Noto+Serif?query=noto+serif)
* [Roboto Serif](https://fonts.google.com/specimen/Roboto+Serif?query=roboto+serif) 
* [Source Serif 4](https://fonts.google.com/specimen/Source+Serif+4?query=source+serif) 
* [STIX Two Text](https://fonts.google.com/specimen/STIX+Two+Text?query=stix+two+text)

Alternatively, LaTeX font can be used for all text and labels with:

```python
import ozzy.plot as oplt #(2)!
oplt.plt.rcParams["text.usetex"] = True #(1)!
```

1.  The `'long_name'` and `'units'` attributes are automatically used by xarray to label plots.
2.  Note that `matplotlib` is imported into `ozzy.plot` as `plt`.

To see all available fonts on the system, use:

```python
import ozzy.plot as oplt
oplt.show_fonts(samples=True)
```

## See also

* The [seaborn](https://seaborn.pydata.org/index.html) library (used by ozzy to [set the figure context](https://seaborn.pydata.org/generated/seaborn.set_context.html))
* [matplotlib][matplotlib]



<!-- import ozzy.plot as oplt

oplt.show_cmaps(libraries=["tol", "cmc"], categories=["sequential", "qualitative"]) -->

<!-- # Plot with ozzy fonts
fonts = oplt.ozzy_fonts
nfonts = len(fonts)

axs = []
for i, font in enumerate(fonts):

    plt.rcParams["font.family"] = font
    fig, axtmp = plt.subplots()
    axs.append(axtmp)
    
    ds['np'].plot(x='t_offs_m', ax=axs[i])
    plt.ylim((0.97, 1.05))
    plt.xlim((0.0, 10.5))
    plt.grid()
    plt.title(r'Plasma density profile - ' + font)

    fig.set_figheight(2) -->

