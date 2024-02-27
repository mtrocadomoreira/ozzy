import os
import numpy as np
import xarray as xr
from . import ozzy as oz
import time

# --- Helper functions ----

def get_kaxis(axis):
    nx = axis.size
    dx = (axis[-1]-axis[0]) / nx
    kaxis = np.fft.fftshift(np.fft.fftfreq(nx,dx))
    return kaxis

# --- Diagnostics ---

def ave_vphi_from_waterfall(da, dcells=11, xvar='zeta', yvar='t'):
    """Calculates the average phase velocity within a 2D moving window from waterfall field data

    Parameters
    ----------
    da : xarray.DataArray
        Field waterfall data (2D)
    dcells : int | tuple | dict, optional
        Number of cells for the 2D moving window. If 'int' is given, the same number is taken for both directions. By default 11
    xvar : str, optional
        Name of the horizontal coordinate in the DataArray object, by default 'zeta'
    yvar : str, optional
        Name of the vertical coordinate in the DataArray object, by default 't'

    Returns
    -------
    xarray.DataArray
        DataArray object containing the 2D phase velocity map (same dimensions as input data).
    """   

    # define dcells in each direction: dx, dt

    match type(dcells):
        case int:
            dx = dcells
            dt = dcells
        case tuple:
            dx = dcells[1]
            dt = dcells[0]
        case dict:
            dx = dcells[xvar]
            dt = dcells[yvar]
        case _:
            raise Exception('Error: format of "dcells" keyword not recognized')

    # check if dcells in either direction is odd (and correct if not)

    if dx % 2 == 0:
        print('Window size in horizontal direction was even number, adding +1')
        dx = dx + 1
    if dt % 2 == 0:
        print('Window size in vertical direction was even number, adding +1')
        dt = dt + 1

    # define margins

    mx = floor(dx * 0.5)
    mt = floor(dt * 0.5)

    data = da.to_numpy()
    vphi = np.zeros_like(data)
    Nt, Nx = data.shape

    xax = data.coords[xvar].to_numpy()
    tax = data.coords[yvar].to_numpy()

    # Define vphi map for each subwindow

    kx = get_kaxis(xax[0:dx])
    kt = get_kaxis(tax[0:dt])
    Kx, Kt = np.meshgrid(kx,kt)
    vphi_map = 1.0 - Ky / Kx
    vphi_map[np.where(Kx == 0)] = 0

    # Loop along center of data

    print('\nCalculating the phase velocity...')

    for i in np.arange(mx, Nx-mx):
        for j in np.arange(mt, Nt-mt):

            window = data[j-mt:j+mt+1, i-mx:i+mx+1]

            fftdata = abs(np.fft.fftshift( np.fft.fft2(window) ))
            factor = np.nansum(fftdata)
            fftdata = fftdata/factor

            vphi[j,i] = np.sum(fftdata*vphi)

    # Deal with margins

    # - corners
    vphi[0:mt,0:mx] = vphi[mt,mx]
    vphi[-mt:,-mx:] = vphi[-(mt+1),-(mx+1)]
    vphi[0:mt,-mx:] = vphi[mt,-(mx+1)]
    vphi[-mt:,0:mx] = vphi[-(mt+1),mx]

    # - up/down
    for j in np.arange(0,mt-1):
        vphi[j,mx:-mx] = vphi[mt,mx:-mx]
        vphi[-(j+1),mx:-mx] = vphi[-(mt+1),mx:-mx]

    # - left/right
    for i in np.arange(0,mx-1):
        vphi[mt:-mt,i] = vphi[mt:-mt,mx]
        vphi[mt:-mt,-(i+1)] = vphi[mt:-mt,-(mx+1)]

    # Create DataArray object

    res = xr.DataArray(vphi, coords=data.coords, dims=data.dims, name='v_phi',
        attrs = {
            'long_name': '$v_\phi$',
            'units': '$c$'
        }
    )

    print('     Done!')

    return res