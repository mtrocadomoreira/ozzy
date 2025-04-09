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
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
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


def _copy_time_var(
    ds_t: xr.Dataset | xr.DataArray, ds: xr.Dataset | xr.DataArray, time_var: str
):
    """
    Copy a time variable from one xarray object to another by expanding dimensions.

    Parameters
    ----------
    ds_t : xarray.Dataset or xarray.DataArray
        Source xarray object containing the time variable to be copied.
    ds : xarray.Dataset or xarray.DataArray
        Target xarray object to which the time variable will be added.
    time_var : str
        Name of the time variable to copy.

    Returns
    -------
    xarray.Dataset or xarray.DataArray
        The input dataset with an expanded dimension for the time variable.
    """
    ds_out = ds.expand_dims({time_var: [ds_t[time_var]]})
    ds_out[time_var].attrs = ds_t[time_var].attrs

    return ds_out


def _convert_coords_to_period_index(
    peak_data: xr.DataArray,
    comoving_var: str,
    new_data_var: str,
    period_var: str,
):
    """
    Convert coordinate variables to a dataset with a period index.

    Parameters
    ----------
    peak_data : xarray.DataArray
        DataArray containing the peak data with coordinates.
    comoving_var : str
        Name of the comoving coordinate variable.
    new_data_var : str
        Name for the new data variable in the output dataset.
    period_var : str
        Name for the period dimension in the output dataset.

    Returns
    -------
    xarray.Dataset
        Dataset with the peak data converted to use period indexing.
    """
    ds_out = xr.Dataset(data_vars={new_data_var: (period_var, peak_data.data)})
    ds_out[new_data_var].attrs = peak_data[comoving_var].attrs

    # Convert other coordinate variables with positions of zero crossings into data variables
    # (there may be more than one coordinate, e.g. with different units, or e.g. "x1" and "x1_box")
    for coord in peak_data.coords:
        if (peak_data[comoving_var].dims == peak_data[coord].dims) and (
            coord != comoving_var
        ):
            new_var = f"{new_data_var}_{coord}"
            ds_out = ds_out.assign({new_var: (period_var, peak_data[coord].data)})
            ds_out[new_var].attrs = peak_data[coord].attrs

    return ds_out


def _sectionalize_field_data(
    da_t: xr.DataArray,
    comoving_var: str,
    max_periods_per_mw: int | float,
    expected_wvl: float,
):
    """
    Divide field data into sections based on expected wavelength.

    Parameters
    ----------
    da_t : xarray.DataArray
        DataArray containing the field data.
    comoving_var : str
        Name of the comoving coordinate variable.
    max_periods_per_mw : int or float
        Maximum number of periods per moving window.
    expected_wvl : float
        Expected wavelength of the oscillations.

    Returns
    -------
    xarray.core.groupby.DataArrayGroupByBins
        DataArray grouped by bins along the comoving coordinate.

    Examples
    --------
    ???+ example "Divide field data into sections"
        ```python
        import xarray as xr
        import numpy as np

        # Create a sample field
        x = np.linspace(0, 100, 1000)
        y = np.sin(2 * np.pi * x / 10)  # wavelength of 10
        field = xr.DataArray(y, coords={"x1": x}, dims="x1")

        # Divide into sections with max 3 periods per section
        sections = _sectionalize_field_data(
            field,
            comoving_var="x1",
            max_periods_per_mw=3,
            expected_wvl=10
        )

        print(len(sections))
        # Output will depend on the number of sections created
        ```
    """
    xmin = da_t[comoving_var].min().compute().to_numpy()
    xmax = da_t[comoving_var].max().compute().to_numpy()

    total_len = xmax - xmin
    sections = np.ceil(total_len / (max_periods_per_mw * expected_wvl))

    axis_bins = np.linspace(xmin, xmax, int(sections) + 1, endpoint=True)
    grp_sections = da_t.groupby_bins(comoving_var, axis_bins)
    return grp_sections


def _find_zero_crossings(
    da_t: xr.DataArray,
    comoving_var: str,
    amplitude_mode: str,
    period_var: str,
    expected_wvl: float | None = None,
):
    """
    Find zero crossings in field data.

    Parameters
    ----------
    da_t : xarray.DataArray
        DataArray containing the field data.
    comoving_var : str
        Name of the comoving coordinate variable.
    amplitude_mode : str
        Mode for finding zero crossings. Options are `'noisy'` or `'smooth'`.
    period_var : str
        Name for the period dimension in the output dataset.
    expected_wvl : float or None, optional
        Expected wavelength of the oscillations, required for `'noisy'` mode.

    Returns
    -------
    xarray.Dataset
        Dataset containing the positions of zero crossings.
    """
    data = -1 * abs(da_t)

    if amplitude_mode == "noisy":
        dx1 = da_t[comoving_var][1] - da_t[comoving_var][0]

        min_height = float(abs(data.min().compute()) / 10)
        min_distance = np.round(0.95 * expected_wvl / 2 / dx1)

        options = {"height": [-min_height, 0.0], "distance": min_distance}

    elif amplitude_mode == "smooth":
        options = {}
        pass

    peaks, _ = find_peaks(data.to_numpy(), **options)
    zeros_locs = data[comoving_var][peaks]

    ds_zcr = _convert_coords_to_period_index(
        zeros_locs, comoving_var, "zero_crossings", period_var
    )

    return ds_zcr


def _find_amplitude_maxima(
    da_t: xr.DataArray,
    comoving_var: str,
    amplitude_mode: str,
    period_var: str,
    expected_wvl: float | None = None,
):
    """
    Find amplitude maxima in field data.

    Parameters
    ----------
    da_t : xarray.DataArray
        DataArray containing the field data.
    comoving_var : str
        Name of the comoving coordinate variable.
    amplitude_mode : str
        Mode for finding amplitude maxima. Options are `'noisy'` or `'smooth'`.
    period_var : str
        Name for the period dimension in the output dataset.
    expected_wvl : float or None, optional
        Expected wavelength of the oscillations, required for `'noisy'` mode.

    Returns
    -------
    xarray.Dataset
        Dataset containing the positions and values of amplitude maxima.
    """
    if amplitude_mode == "noisy":
        dx1 = da_t[comoving_var][1] - da_t[comoving_var][0]

        min_height = float(da_t.std().compute()) * 2 / 3
        min_distance = np.round(0.95 * expected_wvl / dx1)

        options = {"height": min_height, "distance": min_distance}

    elif amplitude_mode == "smooth":
        options = {}
        pass

    peaks, _ = find_peaks(da_t.to_numpy(), **options)

    peak_locs = da_t[comoving_var][peaks]
    peak_vals = da_t[peaks]

    ds_max = _convert_coords_to_period_index(
        peak_locs, comoving_var, "max_locs", period_var
    )
    ds_max["max_amplitude"] = xr.DataArray(
        peak_vals.data, dims=period_var, attrs=peak_vals.attrs
    )

    return ds_max


# --- Diagnostics ---


# TODO: deal with features that are not implemented yet (fft, quasistatic z fixed)
# TODO: explain what phi_err is exactly
# TODO: explain how fit works exactly
# TODO: add example (perhaps using sample data?)
# TODO: throw error if data isn't waterfall (2D with t and x1_box)
# TODO: if xvar is not the horizontal index coordinate, fails with a weird error (delta_x becomes an array) -> better error handling, or maybe make xvar the index first
@stopwatch
def vphi_from_fit(
    da: xr.DataArray,
    x_zero: float,
    xvar: str = "x1_box",
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
                plt.title(f"Fit window #{i}, at time index {j}")
                plt.ylabel("Field")
                plt.xlabel(f"Longitudinal coordinate ({xvar})")
                plt.legend()
                plt.show()
                # TODO: add more information to input prompt e.g.:
                # Getting error of fit > 1. Here are plots of the fit. Please press enter to proceed.
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
            .dropna(xvar + "_window")[xvar]
            .mean()
            .data
        )

    # Create Dataset object

    res = xr.Dataset(
        {
            "vphi": ([tvar, xvar], vphi),
            "phi": ([tvar, xvar], phi),
            "phi_err": ([tvar, xvar], phi_err),
        },
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


# TODO: check examples
def local_maxima_and_zero_crossings(
    da,
    comoving_var: str = "x1_box",
    transv_var: str = "x2",
    tvar: str = "t",
    transv_range=None,
    transv_irange=None,
    transv_pos=None,
    transv_ipos=None,
    amplitude_mode="noisy",
    expected_wvl: float = 2 * np.pi,
    amplitude_max_for="negative_charge",
):
    """
    Find local field maxima and zero crossings in a DataArray.

    This function analyzes a field (typically an electric field) to identify
    local maxima and zero crossings along a specified dimension. It can process
    the data in different ways depending on whether the field data is noisy or smooth.

    Parameters
    ----------
    da : xarray.DataArray
        The data array containing the field to analyze.
    comoving_var : str
        The name of the coordinate representing the comoving dimension.
    transv_var : str
        The name of the coordinate representing the transverse dimension.
    tvar : str
        The name of the coordinate representing time.
    transv_range : tuple | list | numpy.ndarray, optional
        Range of transverse positions to average over, specified as (min, max).
    transv_irange : tuple | list | numpy.ndarray, optional
        Range of transverse indices to average over, specified as (min, max).
    transv_pos : float, optional
        Specific transverse position to analyze.
    transv_ipos : int, optional
        Specific transverse index to analyze.
    amplitude_mode : str
        Method for handling amplitude analysis. Must be either `'noisy'` or `'smooth'`.
        For `'noisy'` data, a moving window average is applied before analysis.
    expected_wvl : float
        Expected wavelength of the oscillations in the field in normalized units (i.e. $k_p^{-1}$) used for window sizing.
    amplitude_max_for : str
        Specifies which charge sign to find the maximum accelerating amplitude for.
        Must be either `'negative_charge'` or `'positive_charge'`.

    Returns
    -------
    tuple
        A tuple containing two [xarray.Dataset][] objects:

        - First element: Dataset with local maxima information

        - Second element: Dataset with zero crossing information

    Raises
    ------
    ValueError
        If required coordinates are missing from the DataArray.

        If invalid options are provided for `amplitude_mode` or `amplitude_max_for`.

        If invalid ranges or positions are specified for transverse selection.

    Notes
    -----
    The function processes data differently based on the `amplitude_mode`:

    - For `'noisy'` data: Applies a moving window average before analysis

    - For `'smooth'` data: Analyzes the raw data directly

    Examples
    --------
    ???+ example "Basic usage with default parameters"
        ```python
        import xarray as xr
        import numpy as np

        # Create a sample dataset with a sinusoidal field
        x = np.linspace(0, 10*np.pi, 1000)
        y = np.linspace(-5, 5, 20)
        t = np.array([0.0, 1.0, 2.0])

        # Create field data with some noise
        field = np.zeros((len(t), len(y), len(x)))
        for i in range(len(t)):
            for j in range(len(y)):
                field[i, j, :] = np.sin(x) + 0.1*np.random.randn(len(x))

        # Create DataArray
        da = xr.DataArray(
            field,
            coords={'t': t, 'x2': y, 'x1_box': x},
            dims=['t', 'x2', 'x1_box']
        )

        # Find zero crossings and maxima
        maxima, zeros = local_maxima_and_zero_crossings(da)

        # The returned datasets contain information about zero crossings and maxima
        # zeros contains 'zero_crossings' coordinate
        # maxima contains 'max_locs' and 'max_vals' coordinates
        ```

    ???+ example "Using custom parameters for a smooth field"
        ```python
        import xarray as xr
        import numpy as np

        # Create a sample dataset with a clean sinusoidal field
        x = np.linspace(0, 10*np.pi, 1000)
        y = np.linspace(-5, 5, 20)
        t = np.array([0.0, 1.0, 2.0])

        # Create clean field data
        field = np.zeros((len(t), len(y), len(x)))
        for i in range(len(t)):
            for j in range(len(y)):
                field[i, j, :] = np.sin(x)

        # Create DataArray
        da = xr.DataArray(
            field,
            coords={'t': t, 'x2': y, 'x1_box': x},
            dims=['t', 'x2', 'x1_box']
        )

        # Find zero crossings and maxima with custom parameters
        maxima, zeros = local_maxima_and_zero_crossings(
            da,
            comoving_var="x1_box",
            transv_range=(-2, 2),  # Average over this transverse range
            amplitude_mode="smooth",  # Use smooth mode for clean data
            amplitude_max_for="positive_charge"  # Find positive field amplitude maximum
        )
        ```
    """
    # Set constants
    max_periods_per_mw = 16
    period_var = "i_period"

    print("Finding local field maxima and zero crossings...")

    # -------------------------------------------------
    # Input checks and error handling
    # -------------------------------------------------

    # Check that all variables are in DataArray
    for var in [comoving_var, transv_var, tvar]:
        if var not in da.coords:
            raise ValueError(f"Could not find variable '{var}' in DataArray")

    # Throw error if amplitude_mode isn't one of accepted options
    if (amplitude_mode != "noisy") and (amplitude_mode != "smooth"):
        raise ValueError(
            "Invalid input for argument 'amplitude_mode'. Valid options are 'noisy' or 'smooth'"
        )

    if amplitude_max_for == "positive_charge":
        pass

    elif amplitude_max_for == "negative_charge":
        da = -1 * da

    else:
        # Throw error if amplitude_max_for isn't one of accepted options
        raise ValueError(
            "Invalid input for argument 'amplitude_max_for'. Valid options are 'negative_charge' or 'positive_charge'"
        )

    # -------------------------------------------------
    # Get subregion according to specified arguments
    # -------------------------------------------------

    if transv_range is not None:
        if len(transv_range) != 2:
            raise ValueError(
                "Invalid input for argument 'transv_range': expecting an iterable object (e.g. tuple, list, numpy.ndarray, etc.) containing two elements"
            )

        da_sub = da.sel({transv_var: slice(*transv_range)}).mean(dim=transv_var)

        if len(da_sub) == 0:
            raise ValueError(
                f"No data found in range {transv_range} for '{transv_var}' coordinate"
            )
    elif transv_irange is not None:
        if len(transv_irange) != 2:
            raise ValueError(
                "Invalid input for argument 'transv_irange': expecting an iterable object (e.g. tuple, list, numpy.ndarray, etc.) containing two elements"
            )

        da_sub = da.isel({transv_var: slice(*transv_irange)}).mean(dim=transv_var)

    elif transv_pos is not None:
        if (transv_pos > da[transv_var].max()) or (transv_pos < da[transv_var].min()):
            raise ValueError(
                f"Value for 'transv_pos' is outside the available range for the coordinate '{transv_var}'"
            )

        da_sub = da.sel({transv_var: transv_pos}, method="nearest")
    elif transv_ipos is not None:
        da_sub = da.isel({transv_var: transv_ipos})
    else:
        if (da[transv_var].max() < 0) or (da[transv_var].min() > 0):
            print(
                "WARNING: Taking line-out at transverse position that is closest to 0."
            )
        da_sub = da.sel({transv_var: 0.0}, method="nearest")

    # -------------------------------------------------
    # Loop along time, depending on amplitude_mode
    # -------------------------------------------------

    all_zcr = []
    all_max = []

    if amplitude_mode == "noisy":
        # --- Apply moving window ---

        # Get number of cells for moving window
        dx1 = da_sub[comoving_var][1] - da_sub[comoving_var][0]
        ncells = np.round(expected_wvl / 4 / dx1)
        # ...and make sure that number is odd
        if (ncells % 2) == 0:
            ncells = ncells - 1

        # Apply moving window
        field_data = da_sub.rolling(
            {comoving_var: int(ncells)}, center=True, min_periods=1
        ).mean()

        # --- Loop along time ---

        for t in tqdm(field_data[tvar]):
            da_t = field_data.sel({tvar: t})

            # Split into sections

            grp_sections = _sectionalize_field_data(
                da_t, comoving_var, max_periods_per_mw, expected_wvl
            )

            # Loop over sections

            all_sections_zcr = []
            all_sections_max = []

            for _, da_t_s in grp_sections:
                ds_zcr_s = _find_zero_crossings(
                    da_t_s,
                    comoving_var,
                    amplitude_mode,
                    period_var,
                    expected_wvl,
                )
                ds_max_s = _find_amplitude_maxima(
                    da_t_s,
                    comoving_var,
                    amplitude_mode,
                    period_var,
                    expected_wvl,
                )

                all_sections_zcr.append(ds_zcr_s)
                all_sections_max.append(ds_max_s)

            # Reassemble sections
            result_zcr = xr.concat(all_sections_zcr, period_var)
            result_max = xr.concat(all_sections_max, period_var)

            # Assign time coordinate
            result_zcr = _copy_time_var(da_t, result_zcr, tvar)
            result_max = _copy_time_var(da_t, result_max, tvar)

            all_zcr.append(result_zcr)
            all_max.append(result_max)

    elif amplitude_mode == "smooth":
        field_data = da_sub

        # --- Loop along time ---

        for t in tqdm(field_data[tvar]):
            da_t = field_data.sel({tvar: t})

            ds_zcr = _find_zero_crossings(
                da_t,
                comoving_var,
                amplitude_mode,
                period_var,
            )
            ds_max = _find_amplitude_maxima(
                da_t,
                comoving_var,
                amplitude_mode,
                period_var,
            )

            # Assign time coordinate
            result_zcr = _copy_time_var(da_t, ds_zcr, tvar)
            result_max = _copy_time_var(da_t, ds_max, tvar)

            all_zcr.append(result_zcr)
            all_max.append(result_max)

    # -------------------------------------------------
    # Harmonize i_period coordinate
    # -------------------------------------------------

    # Find time with largest number of periods
    for ds_all, locs_var in zip([all_zcr, all_max], ["zero_crossings", "max_locs"]):
        i_ref = 0
        ref_ds = ds_all[i_ref]
        nperiods = ref_ds.sizes[period_var]

        for i, ds_t in enumerate(ds_all):
            if ds_t.sizes[period_var] > nperiods:
                ref_ds = ds_t
                nperiods = ds_t.sizes[period_var]
                i_ref = i

        # Assign ordered period coordinate to reference dataset
        ref_ds = ref_ds.assign_coords(
            {period_var: (period_var, np.flip(np.arange(nperiods)))},
        )

        # Interpolate all other time_steps
        f_interp = interp1d(
            ref_ds[locs_var].isel(**{tvar: 0}).data,
            ref_ds[locs_var][period_var].data,
            kind="nearest",
            bounds_error=False,
            fill_value=(nperiods, -1),
        )

        for i, ds_t in enumerate(ds_all):
            if i == i_ref:
                ds_all[i] = ref_ds
            else:
                new_i_arr = f_interp(ds_t[locs_var].isel(**{tvar: 0}).data)

                # Get rid of duplicate indices
                u, c = np.unique(new_i_arr, return_counts=True)
                dup = u[c > 1]
                dup_c = c[c > 1]
                for val, count in zip(dup, dup_c):
                    new_i_arr[np.where(new_i_arr == val)] = new_i_arr[
                        np.where(new_i_arr == val)
                    ] + 1.0 / count * np.flip(np.arange(count))

                ds_t_out = ds_t.assign_coords(
                    {period_var: (period_var, new_i_arr)},
                )
                ds_all[i] = ds_t_out

    # -------------------------------------------------
    # Reassemble along time coordinate
    # -------------------------------------------------

    ds_zeros = xr.concat(all_zcr, tvar)
    ds_max = xr.concat(all_max, tvar)

    return ds_max, ds_zeros
