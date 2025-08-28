# Methods for grid data

The methods in this page are accessible to a data object if:

```python {.annotate}
<data_obj>.attrs['pic_data_type'] == 'grid'#(1)!
```

1.  `<data_obj>` may be either `ozzy.DataArray` or `ozzy.Dataset`

::: ozzy.grid_mixin.GridMixin