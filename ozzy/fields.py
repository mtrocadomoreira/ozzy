import numpy as np
import xarray as xr
from tqdm import tqdm

from .utils import stopwatch


def _get_kaxis(axis):
    nx = axis.size
    dx = (axis[-1] - axis[0]) / nx
    kaxis = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(nx, dx))
    return kaxis


def _get_snr(data):
    mx = np.max(data)
    sd = np.std(data)
    return mx / sd


# --- Diagnostics ---


def vphi_from_fft(data, xax, tax):
    kx = _get_kaxis(xax)
    kt = _get_kaxis(tax)

    fftdata = abs(np.fft.fftshift(np.fft.fft2(data, norm="forward")))

    inds = np.argmax(fftdata)
    indt, indx = np.unravel_index(inds, fftdata.shape)

    vphi_val = 1.0 - kt[indt] / kx[indx]

    dkx = kx[1] - kx[0]
    dkt = kt[1] - kt[0]

    vphi_min = 1 - (kt[indt] + 0.5 * dkt) / (kx[indx] - 0.5 * dkx)
    vphi_max = 1 - (kt[indt] - 0.5 * dkt) / (kx[indx] + 0.5 * dkx)

    vphi_err_pos = np.abs(vphi_val - vphi_max)
    vphi_err_neg = np.abs(vphi_val - vphi_min)
    vphi_snr = _get_snr(fftdata)

    return (vphi_val, vphi_err_pos, vphi_err_neg, vphi_snr)


def phase_from_xcorr(da1: xr.DataArray, da2: xr.DataArray, var: str = "x1"):
    xcorr = xr.apply_ufunc(
        np.correlate,
        da1,
        da2,
        vectorize=True,
        kwargs=dict(mode="full"),
        dask="allowed",
        input_core_dims=[[var], [var]],
        exclude_dims={var},
        output_core_dims=[[var]],
        output_dtypes=[float],
    )

    # TODO: check that both axes of da1 and da2 are the same

    axmin = np.min(da1.coords[var]).data
    axis = da1.coords[var].to_numpy() - axmin

    ax_corr = np.concatenate((np.flip(-axis[1:]), axis))
    xcorr = xcorr.assign_coords({var: ax_corr})

    dshift = max(xcorr)["x1"].data

    return dshift


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

    x_corr = np.linspace(-dx * delta_x, dx * delta_x, 2 * dx + 1)

    # Loop along center of data

    print("\nCalculating the phase...")

    for j in tqdm(np.arange(1, Nt)):
        for i in np.arange(mx, Nx - mx):
            window_t = data[j, i - mx : i + mx + 1]
            window_t_minus = data[j - 1, i - mx : i + mx + 1]

            # calculate correlation, get maximum shift
            corr = np.correlate(window_t, window_t_minus, mode="full")
            max_val = np.max(corr)
            zero_val = corr[dx]

            ind = np.argmax(corr)

            if (max_val == zero_val) & (ind != dx):
                print("Warning: max and zero value of correlation are the same.")

            shift[j, i] = x_corr[ind]

        shift[j, :] = shift[j, :] + shift[j - 1, :]

    # Deal with margins

    for mat in [shift]:
        # - left/right
        for i in np.arange(0, mx):
            mat[:, i] = mat[:, mx]
            mat[:, -(i + 1)] = mat[:, -(mx + 1)]

    # Calculate phase velocity

    print("\nCalculating the phase velocity...")

    # TODO: check that the gradient gets us the phase velocity

    vphi = np.gradient(shift, delta_t, axis=0)

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


@stopwatch
def ave_vphi_from_waterfall(
    da: xr.DataArray,
    dcells: int | tuple | dict = 31,
    xvar: str = "x1",
    yvar: str = "t",
) -> xr.DataArray:
    """Calculates the average phase velocity within a 2D moving window from waterfall field data

    Parameters
    ----------
    da : xarray.DataArray
        Field waterfall data (2D)
    dcells : int | tuple | dict, optional
        Number of cells for the 2D moving window. If 'int' is given, the same number is taken for both directions. By default 11
    xvar : str, optional
        Name of the horizontal coordinate in the DataArray object, by default 'x1'
    yvar : str, optional
        Name of the vertical coordinate in the DataArray object, by default 't'

    Returns
    -------
    xarray.DataArray
        DataArray object containing the 2D phase velocity map (same dimensions as input data).
    """

    # Define dcells in each direction: dx, dt

    match dcells:
        case int():
            dx = dcells
            dt = dcells
        case tuple():
            dx = dcells[1]
            dt = dcells[0]
        case dict():
            dx = dcells[xvar]
            dt = dcells[yvar]
        case _:
            raise TypeError(
                '"dcells" keyword must be either of type int, tuple or dict'
            )

    # Check if dcells in either direction is odd (and correct if not)

    if dx % 2 == 0:
        print("-> Window size in horizontal direction was even number, adding +1")
        dx = dx + 1
    if dt % 2 == 0:
        print("-> Window size in vertical direction was even number, adding +1")
        dt = dt + 1

    # Check whether several wavelengths are contained in a single window

    if xvar in da.coords:
        deltax = da[xvar][1] - da[xvar][0]
        winlen = dx * deltax
        win_wvl = winlen / (2 * np.pi)

        # print(
        #     f"\nAssuming that the horizontal axis is in normalized units, the window size along this direction corresponds to {float(win_wvl)} plasma wavelengths."
        # )

        if win_wvl < 2.5:
            ncells_min = np.ceil(2.5 * 2 * np.pi / deltax)
            print(
                f"WARNING: For an accurate measurement, the window length should be at least 2.5 plasma wavelengths. This would correspond to {int(ncells_min)} cells in this case."
            )

    # Define vphi map for each subwindow

    xax = da.coords[xvar]
    tax = da.coords[yvar]

    kx = _get_kaxis(xax[0:dx].to_numpy())
    kt = _get_kaxis(tax[0:dt].to_numpy())
    # Kx, Kt = np.meshgrid(kx, kt)
    # vphi_map = 1.0 - Kt / Kx
    # vphi_map[np.where(Kx == 0)] = 0

    # Define margins

    mx = int(np.floor(dx * 0.5))
    mt = int(np.floor(dt * 0.5))

    data = da.to_numpy()
    vphi = np.zeros_like(data)
    vphi_err_pos = np.zeros_like(data)
    vphi_err_neg = np.zeros_like(data)
    vphi_snr = np.zeros_like(data)
    Nt, Nx = da.shape

    # Loop along center of data

    print("\nCalculating the phase velocity...")

    for i in tqdm(np.arange(mx, Nx - mx)):
        for j in np.arange(mt, Nt - mt):
            window = data[j - mt : j + mt + 1, i - mx : i + mx + 1]

            fftdata = abs(np.fft.fftshift(np.fft.fft2(window, norm="forward")))
            # factor = np.nansum(fftdata)
            # fftdata = fftdata / factor

            inds = np.argmax(fftdata)
            indt, indx = np.unravel_index(inds, fftdata.shape)

            vphi_val = 1.0 - kt[indt] / kx[indx]

            dkx = kx[1] - kx[0]
            dkt = kt[1] - kt[0]

            vphi_min = 1 - (kt[indt] + 0.5 * dkt) / (kx[indx] - 0.5 * dkx)
            vphi_max = 1 - (kt[indt] - 0.5 * dkt) / (kx[indx] + 0.5 * dkx)

            vphi[j, i] = vphi_val
            vphi_err_pos[j, i] = np.abs(vphi_val - vphi_max)
            vphi_err_neg[j, i] = np.abs(vphi_val - vphi_min)
            vphi_snr[j, i] = _get_snr(fftdata)

            # if _get_snr(fftdata) < 100.0:
            #     print(
            #         f"\nWARNING: Signal-to-noise ratio of FFT of window at ({i}, {j}) is {float(_get_snr(fftdata)):.2f}, which is below the threshold of 100. You may want to consider decreasing the window size.\n"
            #     )

    # Deal with margins

    print("\nFilling the margin cells not covered by the moving window...")

    for mat in [vphi, vphi_err_pos, vphi_err_neg, vphi_snr]:
        # - corners
        mat[0:mt, 0:mx] = mat[mt, mx]
        mat[-mt:, -mx:] = mat[-(mt + 1), -(mx + 1)]
        mat[0:mt, -mx:] = mat[mt, -(mx + 1)]
        mat[-mt:, 0:mx] = mat[-(mt + 1), mx]

        # - up/down
        for j in np.arange(0, mt):  # mt - 1
            mat[j, mx:-mx] = mat[mt, mx:-mx]
            mat[-(j + 1), mx:-mx] = mat[-(mt + 1), mx:-mx]

        # - left/right
        for i in np.arange(0, mx):  # mx - 1
            mat[mt:-mt, i] = mat[mt:-mt, mx]
            mat[mt:-mt, -(i + 1)] = mat[mt:-mt, -(mx + 1)]

    # Create Dataset object

    res = xr.Dataset(
        {
            "vphi": (da.dims, vphi),
            "vphi_err_pos": (da.dims, vphi_err_pos),
            "vphi_err_neg": (da.dims, vphi_err_neg),
            "vphi_snr": (da.dims, vphi_snr),
        },
        coords=da.coords,
    )

    res["vphi"] = res["vphi"].assign_attrs({"long_name": r"$v_\phi$", "units": "$c$"})

    # res = xr.DataArray(
    #     vphi,
    #     coords=da.coords,
    #     dims=da.dims,
    #     name="v_phi",
    #     attrs={"long_name": r"$v_\phi$", "units": "$c$"},
    # )

    print("\nDone!")

    return res
