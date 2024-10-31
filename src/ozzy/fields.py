# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

"""
This submodule includes functions to analyze field data.
"""

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.optimize import curve_fit
from tqdm import tqdm

from .utils import stopwatch

# --- Helper functions ---


def _coarsen_into_blocks(
    da: xr.DataArray, var: str, ncells: int, boundary: str = "trim", side: str = "right"
):
    """
    Coarsen a xarray.DataArray into blocks along a specified dimension.

    Parameters
    ----------
    da : xarray.DataArray
        The input xarray.DataArray to be coarsened.
    var : str
        The name of the dimension along which to coarsen the data.
    ncells : int
        The number of cells to coarsen over.
    boundary : str, optional
        How to handle boundaries. One of `'trim'`, `'pad'`, or `'drop'`. Default is `'trim'`.
    side : str, optional
        Which side to trim or pad on. One of `'left'` or `'right'`. Default is `'right'`.

    Returns
    -------
    xarray.DataArray
        The coarsened xarray.DataArray with a new dimension `'window'` representing the blocks.

    Examples
    --------
    >>> import xarray as xr
    >>> da = xr.DataArray(np.random.rand(10, 20), dims=('x', 'y'))
    >>> da_blocks = _coarsen_into_blocks(da, 'x', 2)
    >>> print(da_blocks)
    <xarray.DataArray (window: 5, x_window: 2, y: 20)>
    array([[[0.97876793, 0.50170379, ..., 0.63642584, 0.92491362],
            [0.22611329, 0.51015634, ..., 0.9770265 , 0.94467706]],
           [[0.82265108, 0.66233855, ..., 0.28416621, 0.96093203],
            [0.35831461, 0.67536946, ..., 0.73078818, 0.59865027]],
           ...,
           [[0.57375793, 0.03718399, ..., 0.19866444, 0.83261985],
            [0.13949275, 0.59865447, ..., 0.94888057, 0.38344152]]])
    """
    da_blocks = da.coarsen({var: ncells}, boundary=boundary, side=side)
    da_blocks = da_blocks.construct({var: ("window", var + "_window")})

    return da_blocks


# --- Diagnostics ---


# TODO: deal with features that are not implemented yet (fft, quasistatic z fixed)
# TODO: explain what phi_err is exactly
# TODO: explain how fit works exactly
# TODO: add example (perhaps using sample data?)
@stopwatch
def vphi_from_fit(
    da: xr.DataArray,
    x_zero: float,
    xvar: str = "x1",
    tvar: str = "t",
    window_len: float = 1.0,
    k: float | str = 1.0,
    boundary: str = "trim",
    quasistatic_fixed_z: bool = False,
):
    r"""
    Measure the phase ($\phi$) and phase velocity ($v_\phi$) from stacked lineouts of a wave (waterfall data) by fitting a sinusoidal function to blocks of data.

    Parameters
    ----------
    da : xarray.DataArray
        The input xarray.DataArray containing the data to be analyzed.

        The data should be two-dimensional: time or propagation distance along one dimension, and a longitudinal coordinate along the other dimension.
    x_zero : float
        Position along the longitudinal coordinate where the sine should be considered to start, and with respect to which the phase will be measured. For example, a seed position.
    xvar : str, optional
        The name of the spatial dimension along which to perform the fit. Default is `'x1'`.
    tvar : str, optional
        The name of the time or propagation dimension. Default is `'t'`.
    window_len : float, optional
        The length of the window (in units of the plasma wavelength) over which to perform the fit. Default is `1.0`.
    k : float | str, optional
        The wavenumber to use in the definition of the window length. If `'fft'`, the wavenumber will be calculated from the FFT of the data. Default is `1.0`.
    boundary : str, optional
        How to handle boundaries when coarsening the data into blocks. One of `'trim'`, `'pad'`, or `'drop'`. See [xarray.DataArray.coarsen][].
    quasistatic_fixed_z : bool, optional
        If True, the phase velocity is calculated assuming a quasistatic approximation with a fixed z-dimension. Default is False.

    Returns
    -------
    xarray.Dataset
        A dataset containing the calculated phase velocity (`'vphi'`), phase (`'phi'`), and phase error (`'phi_err'`).

    """
    # Sort out input arguments

    k_fft = False
    if isinstance(k, str):
        match k:
            case "fft":
                k_fft = True
            case _:
                raise ValueError('k argument must be either a numerical value or "fft"')

    # Define fit function

    def fit_func_wconst(x, phi, amp, kvar, x0):
        return amp * np.sin(kvar * (x - x0) + phi)

    def fit_func(kconst, x0_const):
        def wrapped(x, phi, amp):
            return fit_func_wconst(x, phi, amp, kvar=kconst, x0=x0_const)

        return wrapped

    # Determine window size

    if k_fft:
        pass
        # take FFT of full data along xvar
        # find peaks of spectrum for each z
        # take average of peaks

    delta_x = (da.coords[xvar][1] - da.coords[xvar][0]).data
    delta_t = (da.coords[tvar][1] - da.coords[tvar][0]).data

    wvl = 2 * np.pi / k
    dx = int(np.ceil(window_len * wvl / delta_x))

    # Split data into blocks

    da_blocks = _coarsen_into_blocks(da, xvar, dx, boundary)
    nw = da_blocks.sizes["window"]
    # nx = da_blocks.sizes[xvar + "_window"]

    # Prepare data

    Nt = da.sizes[tvar]

    phi = np.zeros((Nt, nw))
    phi_err = np.zeros((Nt, nw))
    vphi = np.zeros((Nt, nw))

    # Loop along center of data

    print("\nCalculating the phase...")

    lastphi = 0.0

    for j in tqdm(np.arange(1, Nt)):
        if k_fft:
            # k = _k_from_fft(...)

            pass

        for i in range(nw - 1, -1, -1):
            window_da = da_blocks.isel({"window": i, tvar: j}).dropna(xvar + "_window")
            window = window_da.to_numpy()
            axis = window_da[xvar].to_numpy()

            # Set bounds and initial guess

            initguess = [lastphi, np.max(window)]
            bounds = (
                [lastphi - np.pi, 0.05 * np.max(window)],
                [lastphi + np.pi, np.inf],
            )

            # Fit

            pars, pcov = curve_fit(
                fit_func(k, x_zero),
                axis,
                window,
                p0=initguess,
                bounds=bounds,
            )

            perr = np.sqrt(np.diag(pcov))

            if perr[0] > 1:
                f, ax = plt.subplots()
                ax.plot(axis, window, label="data")
                ax.plot(axis, fit_func(k, x_zero)(axis, pars[0], pars[1]), label="fit")
                plt.legend()
                plt.show()
                input()

            phi[j, i] = pars[0]
            phi_err[j, i] = perr[0]
            lastphi = pars[0]

        lastphi = phi[j, -1]

    # Calculate vphi

    print("\nCalculating the phase velocity...")

    dphi_dz = np.gradient(phi, delta_t, axis=0, edge_order=2)

    if quasistatic_fixed_z:
        dphi_dxi = np.gradient(phi, delta_x, axis=1, edge_order=2)
        vphi = dphi_dxi / (dphi_dz - dphi_dxi)
    else:
        vphi = 1 - dphi_dz

    # Prepare new x axis

    x_blocks = np.zeros((nw,))
    for i in np.arange(0, nw):
        x_blocks[i] = (
            da_blocks.isel({"window": i, tvar: 0})
            .dropna(xvar + "_window")["x1"]
            .mean()
            .data
        )

    # Create Dataset object

    res = xr.Dataset(
        {"vphi": (da.dims, vphi), "phi": (da.dims, phi), "phi_err": (da.dims, phi_err)},
        coords={tvar: da.coords[tvar].data, xvar: x_blocks},
    )
    for var in res.coords:
        res[var].attrs = da[var].attrs

    res["vphi"] = res["vphi"].assign_attrs({"long_name": r"$v_\phi$", "units": r"$c$"})
    res["phi"] = res["phi"].assign_attrs(
        {"long_name": r"$\phi$", "units": r"$\mathrm{rad}$"}
    )

    print("\nDone!")

    return res
