import os

import cmcrameri  # noqa
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import seaborn as sns
import xarray as xr

from . import tol_colors as tc

# TODO: write docstrings

font_dirs = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")
font_files = fm.findSystemFonts(fontpaths=font_dirs)
for font_file in font_files:
    fm.fontManager.addfont(font_file)


def cmap_exists(name):
    try:
        plt.cm.get_cmap(name)
        return True
    except ValueError:
        pass
    return False


tc_cmaps = ["rainbow_PuRd", "iridescent", "sunset", "nightfall"]

for col in tc_cmaps:
    if not cmap_exists(col):
        plt.cm.register_cmap(col, tc.tol_cmap(col))

ozparams = {
    "mathtext.fontset": "cm",
    "font.serif": ["Noto Serif", "serif"],
    "font.sans-serif": ["Arial", "Helvetica", "sans"],
    "text.usetex": False,
    "axes.grid": False,
    "axes.prop_cycle": plt.cycler("color", list(tc.tol_cset("muted"))),
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
    "figure.figsize": ("8.0", "4.8"),
    "figure.dpi": "300",
    "image.cmap": "rocket",
    "savefig.format": "pdf",
    "savefig.transparent": True,
    "legend.fontsize": "x-small",
}

sns.set_theme(
    style="ticks",
    font="serif",
    rc=ozparams,  # font_scale=1,
)  # palette=sns.husl_palette(l=.4)

ozzy_color_wheel = list(tc.tol_cset("muted"))

# plt.rc('axes', prop_cycle=plt.cycler('color', list(tc.tol_cset('bright'))))

xr.set_options(
    cmap_divergent="cmc.vik", cmap_sequential="cmc.lipari"
)  # "RdBu_r", "iridescent"


def densplot(ds, ax=None, **kwargs):
    if ax is None:
        f, ax = plt.subplots()
    else:
        f = None

    im = ds.plot.imshow(ax=ax, **kwargs)
    ax.grid(None)
    # plt.gcf().set_size_inches(8, 4.8)

    return im, ax, f
