import numpy as np
import pandas as pd
import xarray as xr

from .backend import Backend, list_avail_backends
from .grid_mixin import GridMixin
from .part_mixin import PartMixin
from .utils import get_user_methods, stopwatch

xr.set_options(keep_attrs=True)

# -----------------------------------------------------------------------
# Get information about all mixin classes
# -----------------------------------------------------------------------

backend_names = list_avail_backends()

func_table = {"func_name": [], "var": [], "value": []}

backend_mixins = []
for bk in backend_names:
    backend = Backend(bk)
    backend_mixins.append(backend.mixin)

    for method in get_user_methods(backend.mixin):
        func_table["func_name"].append(method)
        func_table["var"].append("data_origin")
        func_table["value"].append(bk)

    del backend

pic_data_type_mixins = {"part": PartMixin, "grid": GridMixin}
for pdtype, pdtype_mixin in pic_data_type_mixins.items():
    for method in get_user_methods(pdtype_mixin):
        func_table["func_name"].append(method)
        func_table["var"].append("pic_data_type")
        func_table["value"].append(pdtype)
pic_data_type_mixins = list(pic_data_type_mixins.values())

mixins = backend_mixins + pic_data_type_mixins


# -----------------------------------------------------------------------
# Define gatekeeper metaclass (to control access to mixin methods)
# -----------------------------------------------------------------------

gatekeeper_table = pd.DataFrame(func_table)


class Gatekeeper(type):
    def __call__(cls, *args, **kwargs):
        inst = super().__call__(*args, **kwargs)
        user_methods = get_user_methods(cls)

        for method in user_methods:
            setattr(inst, method, cls.doorman(getattr(inst, method)))

        return inst

    @classmethod
    def doorman(cls, func):
        def wrapped(*args, **kwargs):
            inst = func.__self__

            if func.__name__ in inst.__class__.__dict__:
                return func(*args, **kwargs)

            else:
                try:
                    row = gatekeeper_table.loc[func.__name__]

                    instance_value = inst._obj.attrs[row.var]

                    if isinstance(instance_value, str):
                        instance_value = [instance_value]

                    if row.value in instance_value:
                        return func(*args, **kwargs)
                    else:
                        raise AttributeError(
                            f"{func.__name__} method is only accessible when {row.var} is {row.value}. However,the dataset object's {row.var} attribute is {inst._obj.attrs[row.var]}."
                        )

                except KeyError:
                    raise KeyError(
                        f"{func.__name__} method was not found in class gatekeeper table"
                    )
                except AttributeError:
                    raise

        return wrapped


# -----------------------------------------------------------------------
# Define Ozzy accessor class
# -----------------------------------------------------------------------


@xr.register_dataset_accessor("ozzy")
class OzzyAccessor(*mixins, metaclass=Gatekeeper):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def coord_to_physical_distance(self, coord: str, n0: float, units: str = "m"):
        # HACK: make this function pint-compatible
        if not any([units == opt for opt in ["m", "cm"]]):
            raise KeyError('Error: "units" keyword must be either "m" or "cm"')

        # Assumes n0 is in cm^(-3), returns skin depth in meters
        skdepth = 3e8 / 5.64e4 / np.sqrt(n0)
        if units == "cm":
            skdepth = skdepth * 100.0

        if coord not in self._obj.coords:
            print(
                "\nWARNING: Could not find coordinate in dataset. No changes made to dataset."
            )
            newds = self._obj
        else:
            newcoord = coord + "_" + units
            newds = self._obj.assign_coords(
                {newcoord: skdepth * self._obj.coords[coord]}
            )
            newds[newcoord] = newds[newcoord].assign_attrs(
                long_name="$" + coord + "$", units=r"$\mathrm{" + units + "}$"
            )

        return newds

    @stopwatch
    def save(self, path):
        self._obj.to_netcdf(path, engine="h5netcdf", compute=True, invalid_netcdf=True)

        print('     -> Saved file "' + path + '" ')
