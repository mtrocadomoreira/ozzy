import xarray as xr


class OzDataset(xr.Dataset):
    __slots__ = ("pic_data_type", "origin")


class GridMixin:
    def grid_method(self):
        print("i am grid")


class PartMixin:
    def part_method(self):
        print("i am part")


class BackendMixin:
    def custom_method(self):
        print("i am custom")


def dataset_factory(pic_data_type, origin):
    dtypes = {"grid": GridMixin, "part": PartMixin}
    otypes = {"osiris": BackendMixin}

    # class NewClass(OzDataset, dtypes[pic_data_type], otypes[origin]):
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)

    knight_class = type(
        "MyName",
        (OzDataset, dtypes[pic_data_type], otypes[origin]),
        {"pic_data_type": pic_data_type, "origin": origin},
    )

    return knight_class


cust_cls = dataset_factory("grid", "osiris")
obj = cust_cls(OzDataset())
obj.grid_method()
print(type(obj))
print(isinstance(obj, xr.Dataset))
print(obj.pic_data_type)
print(obj.origin)
