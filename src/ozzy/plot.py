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
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns  # noqa
import xarray as xr
from IPython.display import HTML, display

from . import tol_colors as tc
from .utils import print_file_item

# TODO: write documentation


def cmap_exists(name):
    try:
        mpl.colormaps[name]
        return True
    except KeyError:
        pass
    return False


# Define sets of colormaps and color schemes
mpl_cmaps = {
    "Perceptually Uniform Sequential": [
        "viridis",
        "plasma",
        "inferno",
        "magma",
        "cividis",
    ],
    "Sequential": [
        "Greys",
        "Purples",
        "Blues",
        "Greens",
        "Oranges",
        "Reds",
        "YlOrBr",
        "YlOrRd",
        "OrRd",
        "PuRd",
        "RdPu",
        "BuPu",
        "GnBu",
        "PuBu",
        "YlGnBu",
        "PuBuGn",
        "BuGn",
        "YlGn",
    ],
    "Sequential (2)": [
        "binary",
        "gist_yarg",
        "gist_gray",
        "gray",
        "bone",
        "pink",
        "spring",
        "summer",
        "autumn",
        "winter",
        "cool",
        "Wistia",
        "hot",
        "afmhot",
        "gist_heat",
        "copper",
    ],
    "Diverging": [
        "PiYG",
        "PRGn",
        "BrBG",
        "PuOr",
        "RdGy",
        "RdBu",
        "RdYlBu",
        "RdYlGn",
        "Spectral",
        "coolwarm",
        "bwr",
        "seismic",
    ],
    "Cyclic": ["twilight", "twilight_shifted", "hsv"],
}
tol_cmaps = {
    "Diverging": ["sunset", "nightfall", "BuRd", "PRGn"],
    "Sequential": [
        "YlOrBr",
        "iridescent",
        "rainbow_PuRd",
        "rainbow_PuBr",
        "rainbow_WhRd",
        "rainbow_WhBr",
    ],
    "Qualitative": list(tc.tol_cset()),
}
cmc_cmaps = {
    "Sequential": [
        "batlow",
        "batlowW",
        "batlowK",
        "glasgow",
        "lipari",
        "navia",
        "hawaii",
        "buda",
        "imola",
        "oslo",
        "grayC",
        "nuuk",
        "devon",
        "lajolla",
        "bamako",
        "davos",
        "bilbao",
        "lapaz",
        "acton",
        "turku",
        "tokyo",
    ],
    "Diverging": [
        "broc",
        "cork",
        "vik",
        "lisbon",
        "tofino",
        "berlin",
        "bam",
        "roma",
        "vanimo",
        "managua",
    ],
    "Multi-sequential": ["oleron", "bukavu", "fes"],
}
cmc_cmaps["Qualitative"] = [cmap + "S" for cmap in cmc_cmaps["Sequential"]]
cmc_cmaps["Cyclical"] = []
for cmap in cmc_cmaps["Sequential"] + cmc_cmaps["Diverging"]:
    if cmap_exists("cmc." + cmap + "O"):
        cmc_cmaps["Cyclical"].append(cmap + "O")


# Import fonts
ozzy_fonts = []
font_dirs = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fonts")
font_files = fm.findSystemFonts(fontpaths=font_dirs)
for font_file in font_files:
    fm.fontManager.addfont(font_file)
    font_props = fm.FontProperties(fname=font_file)
    font_name = font_props.get_name()
    if font_name not in ozzy_fonts:
        ozzy_fonts.append(font_name)
ozzy_fonts.sort()

# Import all Paul Tol colormaps
for col in list(tc.tol_cmap()):
    cm_name = "tol." + col
    if not cmap_exists(cm_name):
        plt.cm.register_cmap(cm_name, tc.tol_cmap(col))
for col in list(tc.tol_cset()):
    cm_name = "tol." + col
    if not cmap_exists(cm_name):
        cmap = mpl.colors.LinearSegmentedColormap.from_list(
            cm_name, tc.tol_cset(col), len(tc.tol_cset(col))
        )
        plt.cm.register_cmap(cm_name, cmap)

# Define the default color cycler for curves
color_wheel = list(tc.tol_cset("muted"))

# Define the default rc parameters
ozparams = {
    "mathtext.fontset": "cm",
    "font.serif": ["Noto Serif", "Source Serif 4", "serif"],
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
    "savefig.format": "pdf",
    "savefig.transparent": True,
    "savefig.dpi": "300",
    # "legend.fontsize": "x-small",
}

sns.set_theme(
    style="ticks",
    rc=ozparams,
)

# Set default colormaps
xr.set_options(cmap_divergent="cmc.vik", cmap_sequential="cmc.lipari")


# Define module functions


# Adapted from matplotlib
# https://matplotlib.org/stable/users/explain/colors/colormaps.html
def plot_color_gradients(title, note, cmap_list):
    gradient = np.linspace(0, 1, 256)
    gradient = np.vstack((gradient, gradient))
    # Create figure and adjust figure height to number of colormaps
    nrows = len(cmap_list)
    figh = 0.35 + 0.25 + (nrows + (nrows - 1) * 0.1) * 0.25
    fig, axs = plt.subplots(nrows=nrows + 1, figsize=(4.8, figh))
    fig.subplots_adjust(
        top=1 - 0.35 / figh, bottom=0.25 / figh, left=0.3, right=0.95, hspace=0.3
    )
    axs[0].set_title(f"{title}", fontsize=12)

    for ax, name in zip(axs, cmap_list):
        ax.imshow(gradient, aspect="auto", cmap=mpl.colormaps[name])
        ax.text(
            -0.01,
            0.5,
            name,
            va="center",
            ha="right",
            fontsize=10,
            transform=ax.transAxes,
        )
    # Turn off *all* ticks & spines, not just the ones with colormaps.
    for ax in axs:
        ax.set_axis_off()
    axs[-1].text(
        0.5,
        -1,
        note,
        va="bottom",
        ha="center",
        fontsize=10,
        transform=ax.transAxes,
    )


def show_fonts(samples=False, fontsize=18):
    all_font_paths = fm.get_font_names()
    # other_font_paths = list(set(all_font_paths) - set(ozzy_font_paths))
    other_fonts = sorted(list(set(all_font_paths) - set(ozzy_fonts)))
    # other_fonts = [fm.get_font_(item).family_name for item in other_font_paths]

    if not samples:
        print("Fonts bundled with ozzy:")
        for item in ozzy_fonts:
            print_file_item(item)

        print("\nOther fonts available on your system:")
        for item in other_fonts:
            print_file_item(item)

    else:
        print("Warning: some font samples may not display correctly.")

        def make_row(font):
            return f'<tr> <td style="width: 40%; text-align: left;">{font}</td> <td style="width: 60%; text-align: left;"><span style="font-family:{font}; font-size: {fontsize}px;">{font}</span></td>   </tr>'

        def make_table(font_list):
            rows = ""
            for font in font_list:
                rows = rows + make_row(font)
            body = f"""
                <table style="width: 100%;">
                    <tr>
                        <th style="text-align: center;"><strong>Name</strong></th>
                        <th style="text-align: center;"><strong>Sample</strong></th>
                    </tr>
                {rows}
                </table>
            """
            return body

        structure = f"""
            <h2>Fonts bundled with ozzy:</h2>
            {make_table(ozzy_fonts)}
            <br>
            <h2>Other fonts available on your system:</h2>
            {make_table(other_fonts)}
            """

        display(HTML(structure))

    return


def show_cmaps(
    libraries: str | list[str] = "all", categories: str | list[str] = "all"
) -> None:
    libraries_list = ["mpl", "cmc", "tol"]
    categories_list = ["sequential", "diverging", "qualitative", "cyclical"]

    if libraries == "all":
        libraries = libraries_list
    elif isinstance(libraries, str):
        libraries = [libraries]
    if categories == "all":
        categories = categories_list
    elif isinstance(categories, str):
        categories = [categories]

    # Scientific colour maps
    if "cmc" in libraries:
        for cat in categories:
            for category, cmaps in cmc_cmaps.items():
                if cat in category.lower():
                    cmaps = ["cmc." + name for name in cmaps]
                    plot_color_gradients(
                        "Scientific colour maps (F. Crameri) - " + category,
                        "append an integer number and/or '_r'\nto get a discrete and/or reversed version",
                        cmaps,
                    )

    # Paul Tol
    if "tol" in libraries:
        for cat in categories:
            for category, cmaps in tol_cmaps.items():
                if cat in category.lower():
                    cmaps = ["tol." + name for name in cmaps]
                    plot_color_gradients(
                        "Paul Tol - " + category,
                        "",
                        cmaps,
                    )

    # Matplotlib
    if "mpl" in libraries:
        for cat in categories:
            for category, cmaps in mpl_cmaps.items():
                if cat in category.lower():
                    plot_color_gradients(
                        "Matplotlib - " + category,
                        "",
                        cmaps,
                    )

    plt.show()

    pass


def set_cmap(
    general: None | str = None,
    qualitative: None | str = None,
    divergent: None | str = None,
    sequential: None | str = None,
) -> None:
    # Function to first verify existence of colormap and then set it with a given command
    def verify_and_set(cmap, set_command):
        if cmap_exists(cmap):
            set_command()
        else:
            raise ValueError(f'Colormap "{general}" not found')
        return

    all_args = {**locals()}

    if all(item[1] is None for item in dict.items()):
        print(
            "Not sure which colormap to choose?\nRun 'ozzy.plot.show_cmaps()' to see available colormaps."
        )
        pass
        # if no arguments are given, show all available palettes
    else:
        # Set a general colormap
        if general is not None:
            verify_and_set(general, lambda: mpl.rc("image", cmap=general))
        # Set diverging and/or sequential colormaps separately
        else:
            if divergent is not None:
                verify_and_set(
                    divergent, lambda: xr.set_options(cmap_divergent=divergent)
                )
            if sequential is not None:
                verify_and_set(
                    sequential, lambda: xr.set_options(cmap_sequential=sequential)
                )
        # Set qualitative color map (color cycler for curves)
        if qualitative is not None:
            if isinstance(qualitative, list):
                collist = qualitative
            elif isinstance(qualitative, str):
                # Paul Tol color set
                if qualitative.startswith("tol."):
                    cset_name = qualitative.replace("tol.", "")
                    if cset_name not in list(tc.tol_cset()):
                        raise ValueError(
                            f'Could not find the Paul Tol colorset "{qualitative}". Available options are: {["tol." + cset for cset in list(tc.tol_cset())]}'
                        )
                    else:
                        collist = list(tc.tol_cset(cset_name))
                # Scientific colour maps (categorical variant of a colormap)
                elif qualitative.startswith("cmc."):
                    cset_name = (
                        qualitative if qualitative.endswith("S") else qualitative + "S"
                    )
                    if cmap_exists(cset_name):
                        lcm = mpl.colormaps[cset_name]
                        collist = lcm.colors
                    else:
                        raise ValueError(
                            f'Could not find Scientific color map "{qualitative}".'
                        )
                else:
                    raise ValueError(
                        "Name of qualitative color maps must start either with 'tc.' (Paul Tol's color sets) or 'cmc.' (Scientific colour maps)"
                    )
            else:
                raise ValueError(
                    'Keyword argument for "qualitative" should either be a list or a string'
                )

            mpl.rc("axes", prop_cycle=plt.cycler("color", collist))

            pass
    pass
