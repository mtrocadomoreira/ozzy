import os
import numpy as np
import xarray as xr
from . import ozzy as oz
import time

# --- Helper functions ----



# --- Diagnostics ---

def ave_vphi_from_waterfall():

    # set up rolling window

    # for each region:
        # take 2D fft of waterfall data

        # calculate 2d vphi from fft
        # normalize
        # sum entire region
        # save value in new grid

    return