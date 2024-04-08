import numpy as np

from .utils import axis_from_extent, bins_from_axis

# TODO: mean_rms_grid


class GridMixin:
    def coords_from_extent(self, mapping: dict[str, tuple[float, float]]):
        for k, v in mapping.items():
            nx = self._obj.sizes[k]
            ax = axis_from_extent(nx, v)
        return self._obj.assign_coords({k: ax})

    def get_space_dims(self, time_dim: str = "t"):
        return list(set(list(self._obj.coords)) - {time_dim})

    def get_bin_edges(self, time_dim: str = "t"):
        bin_edges = []
        for axis in self._obj.get_space_dims(time_dim):
            axis_arr = np.array(self[axis])
            bin_edges.append(bins_from_axis(axis_arr))
        return bin_edges
