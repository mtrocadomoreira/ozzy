import numpy as np
import xarray as xr


def dataset_cls_factory(
    backends: Backend | list[Backend] | None = None, pic_data_type: str | None = None
):
    # Sort out backend input

    if isinstance(backends, Backend):
        backends = [backends]
    elif backends is None:
        backends = []

    backends_mixin = [bknd.mixin for bknd in backends]

    if len(backends) > 1:
        dorigin_str = "mixed"
    elif len(backends):
        dorigin_str = backends[0].name
    elif len(backends) == 0:
        dorigin_str = "ozzy"

    # Sort out data type input

    dtype_key = {"grid": GridMixin, "part": PartMixin}

    try:
        dtype_str = pic_data_type.title()
    except AttributeError:
        dtype_str = ""

    try:
        dtype_mixin = [dtype_key[pic_data_type]]
    except KeyError:
        dtype_mixin = []

    # Define new class

    from_classes = [OzzyDatasetBase] + backends_mixin + dtype_mixin

    cls_name = dorigin_str.title() + dtype_str.title() + "Dataset"

    Accessor = type(
        cls_name,
        tuple(from_classes),
        {"pic_data_type": dtype_str, "data_origin": dorigin_str},
    )

    Accessor = xr.register_dataset_accessor("ozzy")(Accessor)
    return


# @xr.register_dataset_accessor("ozzy")
class OzzyAccessor:
    def __init__(self, xarray_obj):
        new_obj = xarray_obj.assign_attrs({"pic_data_type": None})
        self._obj = new_obj
        self._myprop = None

    def get_sizes(self):
        sz = self._obj.sizes
        print("The sizes are: ", sz)
        return sz


OzzyAccessor = xr.register_dataset_accessor("ozzy")(OzzyAccessor)

# OzzyAccessor = xr.register_dataset_accessor(OzzyAccessor, "ozzy")

ds = xr.Dataset()

ds = xr.Dataset({"longitude": np.linspace(0, 10), "latitude": np.linspace(0, 20)})

ds.ozzy.get_sizes()
print(ds.ozzy._myprop)

ds2 = ds.assign_attrs({"myattr": "hello"})
ds3 = xr.Dataset(ds2)

print(ds2)
print(ds3)
