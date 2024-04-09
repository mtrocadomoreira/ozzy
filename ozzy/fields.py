import numpy as np
import xarray as xr
from tqdm import tqdm

from .utils import stopwatch


def _get_kaxis(axis):
    nx = axis.size
    dx = (axis[-1] - axis[0]) / nx
    kaxis = np.fft.fftshift(np.fft.fftfreq(nx, dx))
    return kaxis


# --- Diagnostics ---


@stopwatch
def ave_vphi_from_waterfall(
    da: xr.DataArray,
    dcells: int | tuple | dict = 11,
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

    print(f"Number of cells in each direction:\n  {dx = }, {dt = }")

    # Check if dcells in either direction is odd (and correct if not)

    if dx % 2 == 0:
        print("-> Window size in horizontal direction was even number, adding +1")
        dx = dx + 1
    if dt % 2 == 0:
        print("-> Window size in vertical direction was even number, adding +1")
        dt = dt + 1

    # Define vphi map for each subwindow

    xax = da.coords[xvar].to_numpy()
    tax = da.coords[yvar].to_numpy()

    kx = _get_kaxis(xax[0:dx])
    kt = _get_kaxis(tax[0:dt])
    Kx, Kt = np.meshgrid(kx, kt)
    vphi_map = 1.0 - Kt / Kx
    vphi_map[np.where(Kx == 0)] = 0

    # Define margins

    mx = int(np.floor(dx * 0.5))
    mt = int(np.floor(dt * 0.5))

    data = da.to_numpy()
    vphi = np.zeros_like(data)
    Nt, Nx = data.shape

    # Loop along center of data

    print("\nCalculating the phase velocity...")

    for i in tqdm(np.arange(mx, Nx - mx)):
        for j in np.arange(mt, Nt - mt):  # probably can leave this progress bar out
            window = data[j - mt : j + mt + 1, i - mx : i + mx + 1]

            fftdata = abs(np.fft.fftshift(np.fft.fft2(window)))
            factor = np.nansum(fftdata)
            fftdata = fftdata / factor

            vphi[j, i] = np.sum(fftdata * vphi_map)

    # Deal with margins

    print("\nFilling the margin cells not covered by the moving window...")

    with tqdm(total=100) as pbar:
        nmargincells = 2 * (Nx * mt + Nt * mx - 2 * mx * mt)

        # - corners
        vphi[0:mt, 0:mx] = vphi[mt, mx]
        vphi[-mt:, -mx:] = vphi[-(mt + 1), -(mx + 1)]
        vphi[0:mt, -mx:] = vphi[mt, -(mx + 1)]
        vphi[-mt:, 0:mx] = vphi[-(mt + 1), mx]

        newprog = 100 * 4 * mx * mt / nmargincells
        pbar.update(newprog)

        # - up/down
        for j in np.arange(0, mt - 1):
            vphi[j, mx:-mx] = vphi[mt, mx:-mx]
            vphi[-(j + 1), mx:-mx] = vphi[-(mt + 1), mx:-mx]
            newprog = newprog + 100 * (Nx - 2 * mx) / nmargincells
            pbar.update(newprog)

        # - left/right
        for i in np.arange(0, mx - 1):
            vphi[mt:-mt, i] = vphi[mt:-mt, mx]
            vphi[mt:-mt, -(i + 1)] = vphi[mt:-mt, -(mx + 1)]
            newprog = newprog + 100 * (Nt - 2 * mt) / nmargincells
            pbar.update(newprog)

    # Create DataArray object

    res = xr.DataArray(
        vphi,
        coords=da.coords,
        dims=da.dims,
        name="v_phi",
        attrs={"long_name": r"$v_\phi$", "units": "$c$"},
    )

    print("\nDone!")

    return res
