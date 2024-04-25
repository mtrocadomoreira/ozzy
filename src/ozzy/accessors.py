import dask.array as daskarr
import numpy as np
import pandas as pd
import xarray as xr

from .backend import Backend, _list_avail_backends
from .grid_mixin import GridMixin
from .part_mixin import PartMixin
from .utils import get_user_methods, stopwatch

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

# TODO: add working examples to docstrings
# TODO: get latex to work or eliminate latex from docstrings
# TODO: change apparent names of classes rendered by mkdocstrings


def _coord_to_physical_distance(instance, coord: str, n0: float, units: str = "m"):
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
        newcoord = coord + "_" + units
        new_inst = instance._obj.assign_coords(
            {newcoord: skdepth * instance._obj.coords[coord]}
        )
        new_inst[newcoord] = new_inst[newcoord].assign_attrs(
            long_name="$" + coord + "$", units=r"$\mathrm{" + units + "}$"
        )

    return new_inst


def _save(instance, path):
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
        da = da.assign_coords({dim: kaxis})

        da.coords[dim].attrs["long_name"] = (
            r"$k(" + da.coords[dim].attrs["long_name"].strip("$") + r")$"
        )
        da.coords[dim].attrs["units"] = (
            r"$\left(" + da.coords[dim].attrs["units"].strip("$") + "\right)^{-1}$"
        )

    # Calculate FFT

    fftdata = abs(np.fft.fftshift(np.fft.fftn(da.data, axes=axes, **kwargs), axes=axes))

    # Define new DataArray object

    dout = da.copy(data=daskarr.array(fftdata, chunks=da.chunks))

    return dout


@xr.register_dataset_accessor("ozzy")
class OzzyDataset(*mixins, metaclass=Gatekeeper):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def coord_to_physical_distance(self, coord: str, n0: float, units: str = "m"):
        r"""Convert coordinate to physical units based on the plasma density $n_0$.

        Parameters
        ----------
        coord : str
            Name of coordinate to convert.
        n0 : float
            Plasma electron density in $\mathrm{cm}^{-3}$.
        units : str, optional
            Units of returned physical distance. Either `'m'` for meters or `'cm'` for centimeters.

        Returns
        -------
        xarray.Dataset
            A new Dataset with the additional converted coordinate.

        Examples
        --------

        ??? example "Example 1"

            ```python
            >>> import ozzy as oz
            >>> ds = oz.Dataset({'z': [0, 1, 2]})
            >>> ds_m = ds.ozzy.coord_to_physical_distance(ds, 'z', 1e18) # z in meters
            >>> ds_cm = ds.ozzy.coord_to_physical_distance(ds, 'z', 1e18, units='cm') # z in cm
            ```
        """
        return _coord_to_physical_distance(self, coord, n0, units)

    @stopwatch
    def save(self, path):
        """Save data object to an HDF5 (default) or NetCDF file.

        Parameters
        ----------
        path : str
            The path to save the file to. Specify the file ending as `'.h5'` for HDF5 or `'.nc'` for NetCDF.

        Examples
        --------
        >>> ds = ozzy.Dataset(...)
        >>> ds.ozzy.save('data.h5')
        """
        _save(self, path)

    @stopwatch
    def fft(self, data_var: str, axes=None, dims: list[str] | None = None, **kwargs):
        """Take FFT of variable in Dataset along specified axes.

        Parameters
        ----------
        data_var : str
            The data variable to take FFT of.
        axes : list[int], optional
            The integer indices of the axes to take FFT along.
        dims : list[str], optional
            The names of the dimensions to take FFT along. Overrides `axes`.
        **kwargs
            Additional keyword arguments passed to `[numpy.fft.fftn][]`.

        Returns
        -------
        xarray.DataArray
            The FFT result as a new DataArray.

        Examples
        --------

        """
        return _fft(self._obj[data_var], axes, dims, **kwargs)


@xr.register_dataarray_accessor("ozzy")
class OzzyDataArray(*mixins, metaclass=Gatekeeper):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def coord_to_physical_distance(self, coord: str, n0: float, units: str = "m"):
        r"""Convert coordinate to physical units based on the plasma density $n_0$.

        Parameters
        ----------
        coord : str
            Name of coordinate to convert.
        n0 : float
            Plasma electron density in $\mathrm{cm}^{-3}$.
        units : str, optional
            Units of returned physical distance. Either `'m'` for meters or `'cm'` for centimeters.
            Default is `'m'`.

        Returns
        -------
        xarray.DataArray
            A new DataArray with the additional converted coordinate.

        Examples
        --------

        ??? example "Example 1"

            ```python
            >>> import ozzy as oz
            >>> ds = oz.Dataset({'z': [0, 1, 2]})
            >>> ds_m = ds.ozzy.coord_to_physical_distance(ds, 'z', 1e18) # z in meters
            >>> ds_cm = ds.ozzy.coord_to_physical_distance(ds, 'z', 1e18, units='cm') # z in cm
            ```
        """
        return _coord_to_physical_distance(self, coord, n0, units)

    @stopwatch
    def save(self, path):
        """Save data object to an HDF5 (default) or NetCDF file.

        Parameters
        ----------
        path : str
            The path to save the file to. Specify the file ending as `'.h5'` for HDF5 or `'.nc'` for NetCDF.

        Examples
        --------
        >>> ds = ozzy.DataArray(...)
        >>> ds.ozzy.save('data.h5')
        """
        _save(self, path)

    @stopwatch
    def fft(self, axes=None, dims: list[str] | None = None, **kwargs):
        """Take FFT of DataArray along specified axes.

        Parameters
        ----------
        axes : list[int], optional
            The integer indices of the axes to take FFT along.
        dims : list[str], optional
            The names of the dimensions to take FFT along. Overrides `axes`.
        **kwargs
            Additional keyword arguments passed to `[numpy.fft.fftn][]`.

        Returns
        -------
        xarray.DataArray
            The FFT result as a new DataArray.

        Examples
        --------
        >>> da = xr.DataArray(...)
        >>> da_fft = da.ozzy.fft(dims=['x', 'z'])
        """
        return _fft(self._obj, axes, dims, **kwargs)
