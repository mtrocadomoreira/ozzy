# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import numpy as np

from .utils import axis_from_extent, bins_from_axis

# TODO: mean_rms_grid


class GridMixin:
    def coords_from_extent(self, mapping: dict[str, tuple[float, float]]):
        """Add coordinates to [DataArray][xarray.DataArray] | [Dataset][xarray.Dataset] based on axis extents.

        For each axis name and extent tuple in the mapping, get the axis values and assign them to a new coordinate in the data object.

        Parameters
        ----------
        mapping : dict[str, tuple[float, float]]
            Dictionary mapping axis names to (min, max) extents

        Returns
        -------
        obj : Same type as self._obj
            Object with added coordinate values

        Examples
        --------

        ???+ example "Example 1"

            ```python
            import ozzy as oz
            da = oz.DataArray(np.zeros((4,3)), dims=['x', 'y'], pic_data_type='grid')
            mapping = {'x': (0, 1), 'y': (-1, 2)}
            da = da.ozzy.coords_from_extent(mapping)
            ```
        """
        ds_new = self._obj
        for k, v in mapping.items():
            nx = self._obj.sizes[k]
            ax = axis_from_extent(nx, v)
            ds_new = ds_new.assign_coords({k: ax})
        return ds_new

    def get_space_dims(self, t_var: str = "t"):
        """Get names of spatial dimensions.

        Returns coordinate names that are not the time dimension.

        Parameters
        ----------
        t_var : str, default 't'
            Name of time dimension

        Returns
        -------
        list[str]
            Spatial coordinate names

        Examples
        --------

        ???+ example "Example 1"

            ```python
            import ozzy as oz
            ds = oz.Dataset(...)
            spatial_dims = ds.ozzy.get_space_dims('t')
            print(spatial_dims)
            ```
        """
        return list(set(list(self._obj.dims)) - {t_var})

    def get_bin_edges(self, t_var: str = "t"):
        """Get bin edges along each spatial axis.

        Calculates bin edges from coordinate values. This is useful for binning operations (see example below).

        Parameters
        ----------
        t_var : str, default 't'
            Name of time dimension

        Returns
        -------
        list[np.ndarray]
            List of bin edges for each spatial axis

        Examples
        --------

        ???+ example "Using numpy.histogramdd"

            ```python
            import numpy as np
            bin_edges = axes_ds.ozzy.get_bin_edges('t')
            dist, edges = np.histogramdd(part_coords, bins=bin_edges, weights=ds_i[w_var])
            ```
        """
        bin_edges = []
        for axis in self._obj.ozzy.get_space_dims(t_var):
            axis_arr = np.array(self._obj[axis])
            bin_edges.append(bins_from_axis(axis_arr))
        return bin_edges
