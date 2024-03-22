import numpy as np
import xarray as xr

from .backend import Backend
from .grid_methods import GridMixin
from .part_methods import PartMixin
from .utils import stopwatch


class OzzyDatasetBase(xr.Dataset):
    __slots__ = ("_data_type", "_data_origin")

    def __init__(
        self,
        data_type: str | None = None,
        data_origin: str | list[str] | None = "ozzy",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.data_type = data_type
        self.data_origin = (
            [data_origin] if isinstance(data_origin, str) else data_origin
        )

    # TODO: define __str__ and __repr__

    @property
    def data_origin(self):
        return self._data_origin

    @data_origin.setter
    def data_origin(self, arg):
        self._data_origin = arg

    @data_origin.deleter
    def data_origin(self):
        self.data_origin = None

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, arg):
        self._data_type = arg

    @data_type.deleter
    def data_type(self):
        self._data_type = None

    def coord_to_physical_distance(self, coord: str, n0: float, units: str = "m"):
        # HACK: make this function pint-compatible
        if not any([units == opt for opt in ["m", "cm"]]):
            raise KeyError('Error: "units" keyword must be either "m" or "cm"')

        # Assumes n0 is in cm^(-3), returns skin depth in meters
        skdepth = 3e8 / 5.64e4 / np.sqrt(n0)
        if units == "cm":
            skdepth = skdepth * 100.0

        if coord not in self.coords:
            print(
                "\nWARNING: Could not find coordinate in dataset. No changes made to dataset."
            )
            newds = self
        else:
            newcoord = coord + "_" + units
            newds = self.assign_coords({newcoord: skdepth * self.coords[coord]})
            newds[newcoord] = newds[newcoord].assign_attrs(
                long_name="$" + coord + "$", units=r"$\mathrm{" + units + "}$"
            )

        return newds

    @stopwatch
    def save(self, path):
        self.to_netcdf(path, engine="h5netcdf", compute=True, invalid_netcdf=True)

        print('     -> Saved file "' + path + '" ')


def dataset_cls_factory(
    backends: Backend | list[Backend] | None = None, data_type: str | None = None
):
    # Sort out backend input

    if backends is Backend:
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
        dtype_str = data_type.title()
    except AttributeError:
        dtype_str = ""

    try:
        dtype_mixin = [dtype_key[data_type]]
    except KeyError:
        dtype_mixin = []

    # Define new class

    from_classes = [OzzyDatasetBase] + backends_mixin + dtype_mixin

    cls_name = dorigin_str.title() + dtype_str.title() + "Dataset"

    NewClass = type(
        cls_name,
        tuple(from_classes),
        {"data_type": dtype_str, "data_origin": dorigin_str},
    )

    return NewClass
