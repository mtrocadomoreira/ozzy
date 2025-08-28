# Methods for particle data

The methods in this page are accessible to a data object when:

```python {.annotate}
<data_obj>.attrs['pic_data_type'] == 'part'#(1)!
```

1.  `<data_obj>` may be either `ozzy.DataArray` or `ozzy.Dataset`

::: ozzy.part_mixin.PartMixin