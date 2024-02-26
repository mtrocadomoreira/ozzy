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

def ave_vphi_from_waterfall(da, dcells, xvar='zeta', yvar='t'):

    # define dcells in each direction: dx, dt

    # check if dcells in either direction is odd (and correct if not)

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

    for i in np.arange(mx, Nx-mx):
        for j in np.arange(mt, Nt-mt):

            window = data[j-mt:j+mt+1, i-mx:i+mx+1]

            fftdata = abs(np.fft.fftshift( np.fft.fft2(window) ))
            factor = np.nansum(fftdata)
            fftdata = fftdata/factor

            vphi[j,i] = np.sum(fftdata*vphi)

    # Deal with margins




    return