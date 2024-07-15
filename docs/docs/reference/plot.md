
<!-- - explain that everything is bundled with xarray, seaborn

- default colormaps and color schemes
- default rcparams

- available fonts
- available colormaps

- adding custom colormaps etc -->

In order to set ozzy's aesthetic options as defaults, and to have access to its color maps, color schemes and fonts, the plotting submodule must be imported:

```python
import ozzy.plot as oplt
```

## Defaults

The default plotting options loaded as [matplotlib `rcParams`](https://matplotlib.org/stable/users/explain/customizing.html) by ozzy can be printed with:

```python
import ozzy.plot as oplt
print(oplt.ozparams)
```

The remaining defaults are:

| Defaults | | 
|------|----|
| Curve color scheme | `'tol.muted'`  |   
| Sequential colormap |  `'cmc.lipari'`  |  
| Diverging colormap |  `'cmc.vik'`   |  
| Font |  Noto Serif  |  

## Functions

::: ozzy.plot