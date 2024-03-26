import numpy as np
import xarray as xr

from .utils import stopwatch


class OzzyDatasetBase(xr.Dataset):
    # __slots__ = ("pic_data_type", "data_origin")
    __slots__ = tuple()

    def __init__(
        self,
        # attrs=None,
        *args,
        **kwargs,
    ):
        # self["pic_data_type"] = None
        # self["data_origin"] = None
        super().__init__(*args, **kwargs)

        new_attrs = {"pic_data_type": None, "data_origin": None}

        # attrs = {} if attrs is None else attrs
        for key, deflt in new_attrs.items():
            # self.attrs[key] = attrs[key] if key in attrs else deflt
            self.attrs[key] = deflt

        # self.pic_data_type = pic_data_type
        # self.data_origin = (
        #     [data_origin] if isinstance(data_origin, str) else data_origin
        # )

    # TODO: define __str__ and __repr__

    # @property
    # def data_origin(self):
    #     return self._data_origin

    # @data_origin.setter
    # def data_origin(self, arg):
    #     self._data_origin = arg

    # @data_origin.deleter
    # def data_origin(self):
    #     self.data_origin = None

    # @property
    # def pic_data_type(self):
    #     return self._pic_data_type

    # @pic_data_type.setter
    # def pic_data_type(self, arg):
    #     self._pic_data_type = arg

    # @pic_data_type.deleter
    # def pic_data_type(self):
    #     self._pic_data_type = None

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
