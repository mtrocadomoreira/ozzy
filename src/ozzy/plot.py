# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import os

import cmcrameri  # noqa
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns
import xarray as xr

from . import tol_colors as tc

# TODO: write docstrings


def cmap_exists(name):
    try:
        plt.cm.get_cmap(name)
        return True
    except ValueError:
        pass
    return False


# Import fonts
avail_fonts = []
font_dirs = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")
font_files = fm.findSystemFonts(fontpaths=font_dirs)
for font_file in font_files:
    fm.fontManager.addfont(font_file)
    font_props = fm.FontProperties(fname=font_file)
    font_name = font_props.get_name()
    if font_name not in avail_fonts:
        avail_fonts.append(font_name)

# Import some Paul Tol colormaps
tc_cmaps = ["rainbow_PuRd", "iridescent", "sunset", "nightfall"]
for col in tc_cmaps:
    if not cmap_exists(col):
        plt.cm.register_cmap(col, tc.tol_cmap(col))

# Define the default color cycler for curves
color_wheel = list(tc.tol_cset("muted"))

# Define the default parameters
ozparams = {
    "mathtext.fontset": "cm",
    "font.serif": ["Source Serif 4", "Noto Serif", "serif"],
    "font.sans-serif": ["Arial", "Helvetica", "sans"],
    "text.usetex": False,
    "axes.grid": False,
    "axes.prop_cycle": plt.cycler("color", color_wheel),
    "grid.color": ".9",
    "axes.linewidth": "0.75",
    "xtick.major.width": "0.75",
    "ytick.major.width": "0.75",
    "xtick.minor.width": "0.5",
    "ytick.minor.width": "0.5",
    "xtick.minor.size": "3.5",
    "ytick.minor.size": "3.5",
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "lines.linewidth": "0.75",
    # "figure.figsize": ("8.0", "4.8"),
    "figure.dpi": "300",
    # "image.cmap": "rocket",
    "savefig.format": "pdf",
    "savefig.transparent": True,
    # "legend.fontsize": "x-small",
}

sns.set_theme(
    style="ticks",
    font="serif",
    rc=ozparams,
)

# Set default colormaps
xr.set_options(cmap_divergent="cmc.vik", cmap_sequential="cmc.lipari")
