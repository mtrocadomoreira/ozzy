# TODO: copy existing statistics functions to this file
# TODO: make statistics functions compatible with refactored code

import numpy as np

# Utility functions


def get_space_dims(ds, time_dim="t"):
    return list(set(list(ds.coords)) - {time_dim})


def bins_from_axis(axis):
    vmin = axis[0] - 0.5 * (axis[1] - axis[0])
    binaxis = axis + 0.5 * (axis[1] - axis[0])
    binaxis = np.insert(binaxis, 0, vmin)
    return binaxis


def bin_edges_from_ds(axes_ds, time_dim="t"):
    bin_edges = []
    for axis in get_space_dims(axes_ds, time_dim):
        axis_arr = np.array(axes_ds[axis])
        bin_edges.append(bins_from_axis(axis_arr))
    return bin_edges


# Actual functions
