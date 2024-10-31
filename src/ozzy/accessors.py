# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import dask.array as daskarr
import numpy as np
import pandas as pd
import xarray as xr

from .backend_interface import Backend, _list_avail_backends
from .grid_mixin import GridMixin
from .part_mixin import PartMixin
from .utils import get_user_methods, set_attr_if_exists, stopwatch, tex_format

xr.set_options(keep_attrs=True)

# -----------------------------------------------------------------------
# Get information about all mixin classes
# -----------------------------------------------------------------------

backend_names = _list_avail_backends()

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
# Define Ozzy accessor classes
# -----------------------------------------------------------------------


def _coord_to_physical_distance(
    instance,
    coord: str,
    n0: float,
    new_coord: None | str = None,
    new_label: None | str = None,
    units: str = "m",
    set_as_default: bool = True,
):
    # HACK: make this function pint-compatible
    if not any([units == opt for opt in ["m", "cm"]]):
        raise KeyError('Error: "units" keyword must be either "m" or "cm"')

    # Assumes n0 is in cm^(-3), returns skin depth in meters
    skdepth = 3e8 / 5.64e4 / np.sqrt(n0)
    if units == "cm":
        skdepth = skdepth * 100.0

    if coord not in instance._obj.coords:
        print(
            "\nWARNING: Could not find coordinate in dataset. No changes made to dataset."
        )
        new_inst = instance._obj
    else:
        if new_coord is None:
            nwcoord = "_".join((coord, units))
        else:
            nwcoord = new_coord

        new_inst = instance._obj.assign_coords(
            {nwcoord: skdepth * instance._obj.coords[coord]}
        )
        new_inst[nwcoord].attrs["units"] = r"$\mathrm{" + units + "}$"

        nwlabel = nwcoord
        if new_label is None:
            if new_coord is None:
                if "long_name" in new_inst[coord].attrs:
                    nwlabel = new_inst[coord].attrs["long_name"]
        else:
            assert isinstance(new_label, str)
            nwlabel = new_label

        # latexify label
        if not (nwlabel.startswith("$") & nwlabel.endswith("$")):
            nwlabel = tex_format(nwlabel)

        new_inst[nwcoord].attrs["long_name"] = nwlabel

        if set_as_default:
            new_inst = new_inst.swap_dims({coord: nwcoord})

    return new_inst


def _save(instance, path):
    dobj = instance._obj
    for metadata in ["pic_data_type", "data_origin"]:
        dobj = set_attr_if_exists(dobj, metadata, str_doesnt="")
        # if metadata in dobj.attrs:
        #     if dobj.attrs[metadata] is None:
        #         dobj.attrs[metadata] = ""

    instance._obj.to_netcdf(path, engine="h5netcdf", compute=True, invalid_netcdf=True)
    print('     -> Saved file "' + path + '" ')


def _get_kaxis(axis):
    """Helper function to get the Fourier-transformed axis values for a given axis defined in real space.

    Parameters
    ----------
    axis : numpy.ndarray
        The real-space axis values.

    Returns
    -------
    numpy.ndarray
        The Fourier-transformed axis values.

    Examples
    --------
    >>> x = np.linspace(0, 10, 100)
    >>> kx = ozzy.accessors._get_kaxis(x)
    """
    nx = axis.size
    dx = (axis[-1] - axis[0]) / nx
    kaxis = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(nx, dx))
    return kaxis


# TODO: check whether FFT is working correctly
def _fft(da: xr.DataArray, axes=None, dims: list[str] | None = None, **kwargs):
    # determine which axes should be used
    if dims is not None:
        try:
            axes = [da.get_axis_num(dim) for dim in dims]
        except KeyError:
            raise KeyError(
                f"One or more of the dimensions specified in 'dims' keyword ({dims}) was not found in the DataArray."
            )

    # Get k axes and their metadata

    for ax in axes:
        dim = da.dims[ax]
        if dim not in da.coords:
            raise KeyError(
                f"Dimension {dim} was not found in coordinates of DataArray. Please provide a coordinate for this dimension."
            )
        kaxis = _get_kaxis(da.coords[dim].to_numpy())
        dim_attrs = da[dim].attrs
        da = da.assign_coords({dim: kaxis})
        da[dim].attrs = dim_attrs

        set_attr_if_exists(
            da[dim], "long_name", lambda x: r"$k(" + x.strip("$") + r")$", f"$k_{dim}$"
        )
        set_attr_if_exists(
            da[dim],
            "units",
            lambda x: r"$\left(" + x.strip("$") + r"\right)^{-1}$",
            "a.u.",
        )

    # Calculate FFT

    fftdata = abs(np.fft.fftshift(np.fft.fftn(da.data, axes=axes, **kwargs), axes=axes))

    # Define new DataArray object

    dout = da.copy(data=daskarr.from_array(fftdata, chunks="auto"))
    set_attr_if_exists(dout, "long_name", ("FFT(", ")"), "FFT")
    set_attr_if_exists(dout, "units", lambda x: x)

    return dout


@xr.register_dataset_accessor("ozzy")
class OzzyDataset(*mixins, metaclass=Gatekeeper):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def coord_to_physical_distance(
        self,
        coord: str,
        n0: float,
        units: str = "m",
        new_coord: None | str = None,
        new_label: None | str = None,
        set_as_default: bool = True,
    ) -> xr.Dataset:
        r"""Convert a coordinate to physical units based on the plasma density $n_0$.

        This function calculates the skin depth based on the provided `n0` value and scales the specified coordinate `coord` by the skin depth. The scaled coordinate is assigned a new name (`new_coord` or a default name) and added to the dataset as a new coordinate. The new coordinate can also be assigned a custom label (`new_label`).

        Parameters
        ----------
        coord : str
            Name of coordinate to convert.
        n0 : float
            Value for the plasma electron density used to calculate the skin depth, in $\mathrm{cm}^{-3}$.
        new_coord : str, optional
            The name to assign to the new coordinate. If not provided, a default name is generated based on `coord` and `units`.
        new_label : str, optional
            The label (`"long_name"` attribute) to assign to the new coordinate. If not provided, the label of `coord` is used, if available.
        units : str, optional
            The physical units for the new coordinate. Must be either `"m"` for meters or `"cm"` for centimeters.
        set_as_default : bool, optional
            If `True`, the new coordinate is set as the default coordinate for the corresponding dimension, replacing `coord`.

        Returns
        -------
        xarray.Dataset
            A new Dataset with the additional converted coordinate.

        Examples
        --------

        ???+ example "Converting normalized time units to propagation distance"

            ```python
            import ozzy as oz
            ds = oz.Dataset(data_vars={'var1': [3,4,5]}, coords={'t': [0,1,2]}, dims='t')
            ds_m = ds.ozzy.coord_to_physical_distance('t', 1e18, new_coord='z') # z in m
            ds_cm = ds.ozzy.coord_to_physical_distance('t', 1e18, units='cm', new_coord='z') # z in cm
            ```

        ???+ example "Convert $r$ coordinate to centimeters with new label"

            ```python
            import ozzy as oz
            import numpy as np

            ds = oz.Dataset({'var': np.random.rand(5, 10)},
                            coords={'x2': np.linspace(0, 1, 10)})
            n0 = 1e17  # cm^-3
            ds_new = ds.ozzy.coord_to_physical_distance('x2', n0, new_coord='r', units='cm')
            ```
        """
        return _coord_to_physical_distance(
            self,
            coord,
            n0,
            units=units,
            new_coord=new_coord,
            new_label=new_label,
            set_as_default=set_as_default,
        )

    @stopwatch
    def save(self, path):
        """Save data object to an HDF5 (default) or NetCDF file.

        Parameters
        ----------
        path : str
            The path to save the file to. Specify the file ending as `'.h5'` for HDF5 or `'.nc'` for NetCDF.

        Examples
        --------

        ??? example "Save empty Dataset"

            ```python
            import ozzy as oz
            ds = oz.Dataset()
            ds.ozzy.save('empty_file.h5')
            #  -> Saved file "empty_file.h5"
            # -> 'save' took: 0:00:00.197806
            ```
        """
        _save(self, path)

    @stopwatch
    def fft(
        self,
        data_var: str,
        axes: list[int] | None = None,
        dims: list[str] | None = None,
        **kwargs,
    ) -> xr.DataArray:
        """Calculate the Fast Fourier Transform (FFT) of a variable in a [`Dataset`][xarray.Dataset] along specified dimensions. Take FFT of variable in Dataset along specified axes.

        !!! warning

            This method has not been thoroughly checked for accuracy yet. Please double-check your results with a different FFT function.

        Parameters
        ----------
        data_var : str
            The data variable to take FFT of.
        axes : list[int], optional
            The integer indices of the axes to take FFT along.
        dims : list[str], optional
            Dimensions along which to compute the FFT. If provided, this takes precedence over `axes`.
        **kwargs
            Additional keyword arguments passed to [`numpy.fft.fftn`][numpy.fft.fftn].

        Returns
        -------
        xarray.DataArray
            The FFT result as a new DataArray.


        Examples
        --------

        ???+ example "1D FFT"

            ```python
            import ozzy as oz
            import numpy as np

            # Create a 1D variable in a [Dataset][xarray.Dataset]
            x = np.linspace(0, 10, 100)
            da = oz.Dataset(data_vars = {'f_x' : np.sin(2 * np.pi * x)}, coords=[x], dims=['x'], pic_data_type='grid')

            # Compute the 1D FFT
            da_fft = da.ozzy.fft('f_x', dims=['x'])
            # -> 'fft' took: 0:00:00.085525
            ```

        ???+ example "2D FFT"

            ```python
            import ozzy as oz
            import numpy as np

            # Create a 2D DataArray
            x = np.linspace(0, 10, 100)
            y = np.linspace(0, 5, 50)
            X, Y = np.meshgrid(x, y)
            da = oz.Dataset(data_vars = {'f_xy': np.sin(2 * np.pi * X) * np.cos(2 * np.pi * Y)},
                    coords=[y, x], dims=['y', 'x'], pic_data_type='grid')

            # Compute the 2D FFT
            da_fft = da.ozzy.fft(dims=['x', 'y'])
            # -> 'fft' took: 0:00:00.006278
            ```

        """
        return _fft(self._obj[data_var], axes, dims, **kwargs)


@xr.register_dataarray_accessor("ozzy")
class OzzyDataArray(*mixins, metaclass=Gatekeeper):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def coord_to_physical_distance(
        self,
        coord: str,
        n0: float,
        units: str = "m",
        new_coord: None | str = None,
        new_label: None | str = None,
        set_as_default: bool = True,
    ) -> xr.DataArray:
        r"""Convert a coordinate to physical units based on the plasma density $n_0$.

        This function calculates the skin depth based on the provided `n0` value and scales the specified coordinate `coord` by the skin depth. The scaled coordinate is assigned a new name (`new_coord` or a default name) and added to the dataset as a new coordinate. The new coordinate can also be assigned a custom label (`new_label`).

        Parameters
        ----------
        coord : str
            Name of coordinate to convert.
        n0 : float
            Value for the plasma electron density used to calculate the skin depth, in $\mathrm{cm}^{-3}$.
        new_coord : str, optional
            The name to assign to the new coordinate. If not provided, a default name is generated based on `coord` and `units`.
        new_label : str, optional
            The label (`"long_name"` attribute) to assign to the new coordinate. If not provided, the label of `coord` is used, if available.
        units : str, optional
            The physical units for the new coordinate. Must be either `"m"` for meters or `"cm"` for centimeters.
        set_as_default : bool, optional
            If `True`, the new coordinate is set as the default coordinate for the corresponding dimension, replacing `coord`.

        Returns
        -------
        xarray.DataArray
            A new DataArray with the additional converted coordinate.

        Examples
        --------

        ???+ example "Converting normalized time units to propagation distance"

            ```python
            import ozzy as oz
            da = oz.DataArray([3,4,5], coords={'t': [0,1,2]}, dims='t')
            da_m = da.ozzy.coord_to_physical_distance('t', 1e18, new_coord='z') # z in m
            da_cm = da.ozzy.coord_to_physical_distance('t', 1e18, units='cm', new_coord='z') # z in cm
            ```

        ???+ example "Convert $r$ coordinate to centimeters with new label"

            ```python
            import ozzy as oz
            import numpy as np

            da = oz.DataArray({'var': np.random.rand(5, 10)},
                            coords={'x2': np.linspace(0, 1, 10)})
            n0 = 1e17  # cm^-3
            da_new = da.ozzy.coord_to_physical_distance('x2', n0, new_coord='r', units='cm')
            ```
        """
        return _coord_to_physical_distance(
            self,
            coord,
            n0,
            units=units,
            new_coord=new_coord,
            new_label=new_label,
            set_as_default=set_as_default,
        )

    @stopwatch
    def save(self, path):
        """Save data object to an HDF5 (default) or NetCDF file.

        Parameters
        ----------
        path : str
            The path to save the file to. Specify the file ending as `'.h5'` for HDF5 or `'.nc'` for NetCDF.

        Examples
        --------

        ??? example "Save empty DataArray"

            ```python
            import ozzy as oz
            ds = oz.DataArray()
            ds.ozzy.save('empty_file.h5')
            #  -> Saved file "empty_file.h5"
            # -> 'save' took: 0:00:00.197806
            ```
        """
        _save(self, path)

    @stopwatch
    def fft(
        self, axes: list[int] | None = None, dims: list[str] | None = None, **kwargs
    ) -> xr.DataArray:
        """Calculate the Fast Fourier Transform (FFT) of a [`DataArray`][xarray.DataArray] along specified dimensions.

        !!! warning

            This method has not been thoroughly checked for accuracy yet. Please double-check your results with a different FFT function.

        Parameters
        ----------
        axes : list[int], optional
            The integer indices of the axes to take FFT along.
        dims : list[str], optional
            Dimensions along which to compute the FFT. If provided, this takes precedence over `axes`.
        **kwargs
            Additional keyword arguments passed to [`numpy.fft.fftn`][numpy.fft.fftn].

        Returns
        -------
        xarray.DataArray
            The FFT result as a new DataArray.

        Examples
        --------

        ???+ example "1D FFT"

            ```python
            import ozzy as oz
            import numpy as np

            # Create a 1D DataArray
            x = np.linspace(0, 10, 100)
            da = oz.DataArray(np.sin(2 * np.pi * x), coords=[x], dims=['x'], pic_data_type='grid')

            # Compute the 1D FFT
            da_fft = da.ozzy.fft(dims=['x'])
            # -> 'fft' took: 0:00:00.085525
            ```

        ???+ example "2D FFT"

            ```python
            import ozzy as oz
            import numpy as np

            # Create a 2D DataArray
            x = np.linspace(0, 10, 100)
            y = np.linspace(0, 5, 50)
            X, Y = np.meshgrid(x, y)
            da = oz.DataArray(np.sin(2 * np.pi * X) * np.cos(2 * np.pi * Y),
                    coords=[y, x], dims=['y', 'x'], pic_data_type='grid')

            # Compute the 2D FFT
            da_fft = da.ozzy.fft(dims=['x', 'y'])
            # -> 'fft' took: 0:00:00.006278
            ```
        """
        return _fft(self._obj, axes, dims, **kwargs)
