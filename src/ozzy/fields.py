import numpy as np
import xarray as xr
from scipy.signal import correlation_lags
from tqdm import tqdm

from .utils import stopwatch

# TODO: write docstrings


def _xcorr_axis(nx, deltax):
    return np.linspace(-nx * deltax, nx * deltax, 2 * nx - 1)


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

    if nx is None:
        nx = arr1.size

    # Calculate correlation, get maximum shift
    corr = np.correlate(arr1, arr2, mode="full")
    max_val = np.max(corr)
    zero_val = corr[arr1.size - 1]

    ind = np.argmax(corr)

    if (max_val == zero_val) & (ind != nx):
        # print(
        #     f"WARNING: max and zero value of cross correlation are the same: {max_val}, {zero_val}. Setting the shift to zero instead."
        # )
        ind = nx

    # f1, ax = plt.subplots()
    # plt.plot(xcorr_axis[0:nx], arr1)
    # plt.plot(xcorr_axis[0:nx], arr2)
    # plt.grid()
    # plt.show()

    # f2, ax = plt.subplots()
    # plt.plot(xcorr_axis, corr)
    # ylims = plt.ylim()
    # plt.vlines(xcorr_axis[ind], ylims[0], ylims[1], linestyles="--")
    # plt.grid()
    # plt.show()

    return xcorr_axis[ind]


# --- Diagnostics ---


@stopwatch
def vphi_from_xcorr_blocks(
    da: xr.DataArray,
    xvar: str = "x1",
    tvar: str = "t",
    window_len: float = 5.0,
    k: float | str = 1.0,
    boundary: str = "trim",
):
    delta_x = (da.coords[xvar][1] - da.coords[xvar][0]).data
    delta_t = (da.coords[tvar][1] - da.coords[tvar][0]).data

    wvl = 2 * np.pi / k
    dx = int(np.ceil(window_len * wvl / delta_x))

    # Nx = da.sizes[xvar]
    Nt = da.sizes[tvar]

    da_blocks = da.coarsen({xvar: dx}, boundary=boundary, side="right")
    da_blocks = da_blocks.construct(x1=("window", "x1_window"))
    nw = da_blocks.sizes["window"]
    nx = da_blocks.sizes["x1_window"]

    # Prepare data

    shift = np.zeros((Nt, nw))
    vphi = np.zeros((Nt, nw))

    # Prepare shift axis

    x_corr = correlation_lags(nx, nx) * delta_x
    assert x_corr[nx - 1] == 0

    # Loop along center of data

    print("\nCalculating the phase...")

    for j in tqdm(np.arange(1, Nt)):
        for i in np.arange(0, nw):
            window_t = (
                da_blocks.isel({"window": i, tvar: j}).dropna("x1_window").to_numpy()
            )
            window_t_minus = (
                da_blocks.isel({"window": i, tvar: j - 1})
                .dropna("x1_window")
                .to_numpy()
            )

            shift[j, i] = _shift_from_xcorr(window_t, window_t_minus, xcorr_axis=x_corr)

        shift[j, :] = shift[j, :] + shift[j - 1, :]

    # Calculate phase velocity

    print("\nCalculating the phase velocity...")

    vphi = 1 + np.gradient(shift, delta_t, axis=0, edge_order=2)

    # Prepare new x axis

    x_blocks = np.zeros((nw,))
    for i in np.arange(0, nw):
        x_blocks[i] = (
            da_blocks.isel({"window": i, tvar: 0}).dropna("x1_window")["x1"].mean().data
        )

    # Create Dataset object

    res = xr.Dataset(
        {
            "vphi": (da.dims, vphi),
            "shift": (da.dims, shift),
        },
        coords={tvar: da.coords[tvar].data, xvar: x_blocks},
    )
    for var in res.coords:
        res[var].attrs = da[var].attrs

    res["vphi"] = res["vphi"].assign_attrs({"long_name": r"$v_\phi$", "units": "$c$"})
    res["shift"] = res["shift"].assign_attrs(
        {"long_name": r"$\delta \xi$", "units": "$k_p^{-1}$"}
    )

    print("\nDone!")

    return res


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
        # for i in np.arange(mx, Nx - mx):
        for i in np.arange(Nx - mx - 1, mx - 1, -1):
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
