import xarray as xr


@xr.register_dataset_accessor("ozzy")
class OzzyAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        self._pic_data_type = None
        self._data_origin = None

    @property
    def pic_data_type(self):
        return self._pic_data_type

    @property
    def center(self):
        """Return the geographic center point of this dataset."""
        if self._center is None:
            # we can use a cache on our accessor objects, because accessors
            # themselves are cached on instances that access them.
            lon = self._obj.latitude
            lat = self._obj.longitude
            self._center = (float(lon.mean()), float(lat.mean()))
        return self._center

    def plot(self):
        """Plot data on a map."""
        return "plotting!"


# class Dataset(xr.Dataset):
#     __slots__ = (
#         "_pic_data_type",
#         "_data_origin",
#         "pic_data_type",
#         "data_origin",
#     )

#     def __init__(
#         self,
#         pic_data_type: str | None = None,
#         data_origin: str | list[str] | None = "ozzy",
#         *args,
#         **kwargs,
#     ):
#         self.pic_data_type = pic_data_type
#         self.data_origin = (
#             [data_origin] if isinstance(data_origin, str) else data_origin
#         )
#         super().__init__(*args, **kwargs)

#     def do(self, txt):
#         print(txt)


ds = xr.Dataset()
ds2 = OzzyAccessor(ds)

print(ds2.pic_data_type)

print(ds2._obj)


# ds = Dataset(pic_data_type="grid")
# print(ds.pic_data_type)

# ds2 = Dataset(ds)
# print((ds2.pic_data_type))

# ds2 = Dataset(ds, pic_data_type="raw")
# print(ds2.pic_data_type)

# ds2 = Dataset(ds)
# # print((ds2))
# print(ds2.pic_data_type)
