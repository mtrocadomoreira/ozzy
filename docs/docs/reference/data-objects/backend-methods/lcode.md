# LCODE-specific methods

The methods in this page are accessible to a data object if:

```python {.annotate}
<data_obj>.attrs['data_origin'] == 'lcode'#(1)!
```

1.  `<data_obj>` may be either `ozzy.DataArray` or `ozzy.Dataset`

::: ozzy.backends.lcode_backend.Methods