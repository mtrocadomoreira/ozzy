import numpy as np
import xarray as xr
from tqdm import tqdm

from .utils import stopwatch


def _xcorr_axis(nx, deltax):
    return np.linspace(-nx * deltax, nx * deltax, 2 * nx + 1)


def _shift_from_xcorr(
    arr1: np.ndarray,
    arr2: np.ndarray,
    nx: int | None = None,
    deltax: float | None = None,
    xcorr_axis: np.ndarray | None = None,
):
    # Determine whether axis info is there
    if xcorr_axis is None:
        if nx is None or deltax is None:
            raise ValueError(
                "If xcorr_axis is not provided, nx and deltax must be provided."
            )
        xcorr_axis = _xcorr_axis(nx, deltax)

    # Calculate correlation, get maximum shift
    corr = np.correlate(arr1, arr2, mode="full")
    max_val = np.max(corr)
    zero_val = corr[corr.size]

    ind = np.argmax(corr)

    if (max_val == zero_val) & (ind != nx):
        print(
            "WARNING: max and zero value of cross correlation are the same. May be finding a shift when there is none."
        )
    return xcorr_axis[ind]


# --- Diagnostics ---


@stopwatch
def vphi_from_xcorr(
    da: xr.DataArray,
    xvar: str = "x1",
    tvar: str = "t",
    window_len: float = 2.5,
    k: float | str = 1.0,
) -> xr.Dataset:
    delta_x = (da.coords[xvar][1] - da.coords[xvar][0]).data
    delta_t = (da.coords[tvar][1] - da.coords[tvar][0]).data

    wvl = 2 * np.pi / k
    dx = int(np.ceil(window_len * wvl / delta_x))
    if dx % 2 == 0:
        dx = dx + 1

    Nt = da.sizes[tvar]
    Nx = da.sizes[xvar]

    # Define margin and prepare data

    mx = int(np.floor(dx * 0.5))

    data = da.to_numpy()
    shift = np.zeros_like(data)
    vphi = np.zeros_like(data)

    # Prepare shift axis

    x_corr = _xcorr_axis(dx, delta_x)

    # Loop along center of data

    print("\nCalculating the phase...")

    for j in tqdm(np.arange(1, Nt)):
        for i in np.arange(mx, Nx - mx):
            window_t = data[j, i - mx : i + mx + 1]
            window_t_minus = data[j - 1, i - mx : i + mx + 1]

            shift[j, i] = _shift_from_xcorr(window_t, window_t_minus, xcorr_axis=x_corr)

        shift[j, :] = shift[j, :] + shift[j - 1, :]

    # Deal with left and right margins

    for i in np.arange(0, mx):
        shift[:, i] = shift[:, mx]
        shift[:, -(i + 1)] = shift[:, -(mx + 1)]

    # Calculate phase velocity

    print("\nCalculating the phase velocity...")

    vphi = 1 + np.gradient(shift, delta_t, axis=0)

    # Create Dataset object

    res = xr.Dataset(
        {
            "vphi": (da.dims, vphi),
            "shift": (da.dims, shift),
        },
        coords=da.coords,
    )

    res["vphi"] = res["vphi"].assign_attrs({"long_name": r"$v_\phi$", "units": "$c$"})
    res["shift"] = res["shift"].assign_attrs(
        {"long_name": r"$\delta \xi$", "units": "$k_p^{-1}$"}
    )

    print("\nDone!")

    return res
