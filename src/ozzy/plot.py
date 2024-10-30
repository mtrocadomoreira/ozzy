# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************

import os
from collections.abc import Callable, Iterable

import cmcrameri  # noqa
import hvplot.xarray
import matplotlib as mpl
import matplotlib.animation as manim
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns  # noqa
import xarray as xr
from IPython.display import HTML, display
from tqdm import tqdm

from . import tol_colors as tc
from .utils import print_file_item

# HACK: function to plot quiver plot between two time steps (particle data)
# HACK: function to plot lineout on top of imshow/pcolormesh; give position of line-out, give max and min axis range in the units of the imshow axis; have option to keep ticks or not; return new secondary axis and line object


def _cmap_exists(name):
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
    if _cmap_exists("cmc." + cmap + "O"):
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
    if not _cmap_exists(cm_name):
        mpl.colormaps.register(tc.tol_cmap(col), name=cm_name)
for col in list(tc.tol_cset()):
    cm_name = "tol." + col
    if not _cmap_exists(cm_name):
        cmap = mpl.colors.LinearSegmentedColormap.from_list(
            cm_name, tc.tol_cset(col), len(tc.tol_cset(col))
        )
        mpl.colormaps.register(cmap, name=cm_name)

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
    "savefig.bbox": "tight",
}

sns.set_theme(
    style="ticks",
    font="serif",
    rc=ozparams,
)

# Set default colormaps
xr.set_options(cmap_divergent="cmc.vik", cmap_sequential="cmc.lipari")

# Define module classes


class MutablePlotObj:
    def __init__(
        self,
        imo: mpl.artist.Artist,
        ax: mpl.axes.Axes,
        da: xr.DataArray,
        tvar: str,
        xlim: None | tuple[float, float],
        ylim: None | tuple[float, float],
        clim: None | tuple[float, float],
        plot_func: None | Callable,
    ):
        self.imo = imo
        self.da = da
        self.ax = ax
        self.tvar = tvar
        self.xlim = xlim
        self.ylim = ylim
        self.clim = clim
        self.pfunc = plot_func
        return

    def redraw(self, tval: float) -> None:
        # Clear the axes
        if hasattr(self.imo, "colorbar"):
            if hasattr(self.imo.colorbar, "remove"):
                self.imo.colorbar.remove()
        self.ax.clear()

        # Create new plot object

        da_it = self.da.sel({self.tvar: tval}, method="nearest")
        new_imo = da_it.plot(ax=self.ax)

        # Set axis limits
        if self.xlim is not None:
            self.ax.set_xlim(self.xlim)
        if self.ylim is not None:
            self.ax.set_ylim(self.ylim)
        if hasattr(new_imo, "set_clim") & (self.clim is not None):
            new_imo.set_clim(self.clim)

        # Run plot_func
        if self.pfunc is not None:
            tsel = da_it[self.tvar].to_numpy()
            self.pfunc(self.ax, new_imo, self.da, self.tvar, tsel)

        # Update plot object
        self.imo = new_imo

        return


# Define module functions


# Adapted from matplotlib
# https://matplotlib.org/stable/users/explain/colors/colormaps.html
def _plot_color_gradients(title, note, cmap_list):
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


def show_fonts(samples: bool = False, fontsize: float = 18) -> None:
    """
    Display a list of fonts bundled with ozzy and other fonts available on the system.

    Parameters
    ----------
    samples : bool, optional
        If `True`, display font samples in addition to the font names.

        !!! Warning

            The font samples are rendered as an HTML object (only works with Jupyter).

    fontsize : float, optional
        The font size to use for displaying font samples.

    Examples
    --------
    ???+ example "Show font names only"
        ```python
        import ozzy.plot as oplt
        oplt.show_fonts()
        ```

    ???+ example "Show font names and samples"
        ```python
        import ozzy.plot as oplt
        oplt.show_fonts(samples=True)
        ```
    """
    all_font_paths = fm.get_font_names()
    other_fonts = sorted(list(set(all_font_paths) - set(ozzy_fonts)))

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


def set_font(font: str) -> None:
    """
    Set the font family for all text in the plots.

    !!! note

        If you want all text in the plot to be rendered in LaTeX math font, as opposed to only the text surrounded by `$...$`, use the following commands:

        ```python
        import ozzy.plot as oplt
        oplt.plt.rcParams['text.usetex'] = True
        ```
        or
        ```python
        import ozzy.plot as oplt
        import matplotlib.pyplot as plt
        plt.rcParams["text.usetex"] = True
        ```

    Parameters
    ----------
    font : str
        The name of the font family to use. The font must be installed on the system and recognized by [`matplotlib.font_manager.get_font_names()`][matplotlib.font_manager.get_font_names].

    Raises
    ------
    ValueError
        If the specified `font` is not found in the list of available font names.

    Examples
    --------
    ???+ example "Set font to DejaVu Sans"
        ```python
        import ozzy.plot as oplt
        oplt.set_font('DejaVu Sans')
        ```

    ???+ example "Attempt to set an invalid font"
        ```python
        import ozzy.plot as oplt
        oplt.set_font('InvalidFontName')
        # ValueError: Couldn't find font
        ```
    """
    if font in fm.get_font_names():
        mpl.rc("font", family=font)
    else:
        raise ValueError("Couldn't find font")
    return


def show_cmaps(
    library: str | list[str] = "all", category: str | list[str] = "all"
) -> None:
    """
    Display available colormaps from different libraries and categories.

    Parameters
    ----------
    library : str | list[str], optional
        The library or libraries to display colormaps from. Options are `'mpl'` (Matplotlib), `'cmc'` ([Scientific colour maps](https://www.fabiocrameri.ch/colourmaps/) by F. Crameri), `'tol'` ([Paul Tol's colormaps](https://personal.sron.nl/~pault/)), and `'all'`.
    category : str | list[str], optional
        The category or categories of colormaps to display. Options are `'sequential'`, `'diverging'`, `'qualitative'`, `'cyclical'`, and `'all'`.

    Examples
    --------
    ???+ example "Show all available colormaps"
        ```python
        import ozzy.plot as oplt
        oplt.show_cmaps()
        ```

    ???+ example "Show sequential colormaps from Matplotlib"
        ```python
        import ozzy.plot as oplt
        oplt.show_cmaps(library='mpl', category='sequential')
        ```

    ???+ example "Show diverging colormaps from Paul Tol and Scientific colour maps"
        ```python
        import ozzy.plot as oplt
        oplt.show_cmaps(library=['tol', 'cmc'], category='diverging')
        ```
    """
    libraries_list = ["mpl", "cmc", "tol"]
    categories_list = ["sequential", "diverging", "qualitative", "cyclical"]

    if library == "all":
        lib = libraries_list
    elif isinstance(library, str):
        lib = [library]
    if category == "all":
        cat = categories_list
    elif isinstance(category, str):
        cat = [category]

    # Scientific colour maps
    if "cmc" in lib:
        for c in cat:
            for c2, cmaps in cmc_cmaps.items():
                if c in c2.lower():
                    cmaps = ["cmc." + name for name in cmaps]
                    _plot_color_gradients(
                        "Scientific colour maps (F. Crameri) - " + c2,
                        "append an integer number and/or '_r'\nto get a discrete and/or reversed version",
                        cmaps,
                    )

    # Paul Tol
    if "tol" in lib:
        for c in cat:
            for c2, cmaps in tol_cmaps.items():
                if c in c2.lower():
                    cmaps = ["tol." + name for name in cmaps]
                    _plot_color_gradients(
                        "Paul Tol - " + c2,
                        "",
                        cmaps,
                    )

    # Matplotlib
    if "mpl" in lib:
        for c in cat:
            for c2, cmaps in mpl_cmaps.items():
                if c in c2.lower():
                    _plot_color_gradients(
                        "Matplotlib - " + c2,
                        "",
                        cmaps,
                    )
    plt.show()

    pass


def set_cmap(
    general: None | str = None,
    qualitative: None | str = None,
    diverging: None | str = None,
    sequential: None | str = None,
) -> None:
    """
    Set the default colormaps for various types of plots.

    Parameters
    ----------
    general : str, optional
        The colormap to use for general plots.
    qualitative : str | list[str], optional
        The colormap or list of colors to use for qualitative plots (e.g., line plots).
    diverging : str, optional
        The colormap to use for diverging plots.
    sequential : str, optional
        The colormap to use for sequential plots.

    Examples
    --------
    ???+ example "Set general colormap to *viridis*"
        ```python
        import ozzy.plot as oplt
        oplt.set_cmap(general='viridis')
        ```

    ???+ example "Set diverging and sequential colormaps separately"
        ```python
        import ozzy.plot as oplt
        oplt.set_cmap(diverging='cmc.lisbon', sequential='tol.iridescent')
        ```

    ???+ example "Set qualitative colormap to Paul Tol's _Bright_ color scheme"
        ```python
        import ozzy.plot as oplt
        oplt.set_cmap(qualitative='tol.bright')
        ```
    """

    # Function to first verify existence of colormap and then set it with a given command
    def verify_and_set(cmap, set_command):
        if _cmap_exists(cmap):
            set_command()
        else:
            raise ValueError(f'Colormap "{general}" not found')
        return

    all_args = {**locals()}

    if all(item[1] is None for item in all_args.items()):
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
            if diverging is not None:
                verify_and_set(
                    diverging, lambda: xr.set_options(cmap_divergent=diverging)
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
                    if _cmap_exists(cset_name):
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


# HACK: quality seems to be shitty with ffmpeg, don't know how to improve. maybe set frames as default
def movie(
    fig: mpl.figure.Figure,
    plot_objs: dict[mpl.artist.Artist, tuple[xr.DataArray, str]]
    | dict[mpl.artist.Artist, xr.DataArray],
    filename: str,
    fps: int = 5,
    dpi: int = 300,
    t_range: None | tuple[float, float] = None,
    xlim: None | tuple[float, float] = None,
    ylim: None | tuple[float, float] = None,
    clim: None | tuple[float, float] = None,
    clim_fixed: bool = True,
    plot_func: Callable | dict[mpl.artist.Artist, Callable] | None = None,
    writer: str = "ffmpeg",
    **kwargs,
) -> None:
    """
    Create an animation from matplotlib figure objects.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The [matplotlib Figure][matplotlib.figure.Figure] object to animate.
    plot_objs : dict[matplotlib.artist.Artist, tuple[xarray.DataArray, str]] | dict[matplotlib.artist.Artist, xarray.DataArray]
        A dictionary mapping [matplotlib Artist][matplotlib.artist.Artist] objects to either tuples containing a DataArray and the name of its time coordinate, or to a DataArray (where the time coordinate is assumed to be `'t'`).
    filename : str
        The output file name or path for the animation. If the path doesn't exist, missing folders will be created.
    fps : int, optional
        Frames per second for the animation.
    dpi : int, optional
        Dots-per-inch resolution for the output.
    t_range : tuple[float, float] | None, optional
        The time range for the animation. If `None`, the full time range of the data will be used.
    xlim : tuple[float, float] | None | dict[matplotlib.artist.Artist, tuple[float,float]], optional
        The horizontal axis limits. Can be a tuple, `None`, or a dictionary mapping [Artists][matplotlib.artist.Artist] to their respective limits.
    ylim : tuple[float, float] | None | dict[matplotlib.artist.Artist, tuple[float,float]], optional
        The vertical axis limits. Can be a tuple, `None`, or a dictionary mapping [Artists][matplotlib.artist.Artist] to their respective limits.
    clim : tuple[float, float] | None | dict[matplotlib.artist.Artist, tuple[float,float]], optional
        The color scale limits. Can be a tuple, `None`, or a dictionary mapping [Artists][matplotlib.artist.Artist] to their respective limits.
    clim_fixed : bool, optional
        If `False`, color scale limits vary for each time step.
    plot_func : Callable | dict[matplotlib.artist.Artist, Callable] | None, optional
        A function or dictionary of functions to customize the plot at each time step. Each function must take 5 arguments in this order: `ax` (matplotlib Axes), `imo` (matplotlib Artist), `da` (DataArray), `tvar` (str), `tval` (float), and return None. The function overrides axis limits.

    writer : str, optional
        The [`matplotlib` animation writer](https://matplotlib.org/stable/api/animation_api.html#writer-classes) to use. Options are `'ffmpeg'`, `'pillow'`, `'html'`, `'imagemagick'`, and `'frames_png'`. When `'frames_png'` is selected, no writer is used and the animation frames are saved to a folder in PNG format.

        !!! info

            The [FFMpeg library](https://ffmpeg.org/) must be installed on the system in order to use [matplotlib's FFMpeg writer][matplotlib.animation.FFMpegWriter].

    **kwargs
        Additional keyword arguments to pass to the `matplotlib` animation writer.

        !!! note

            For `writer='ffmpeg'`, a [constant rate factor](https://trac.ffmpeg.org/wiki/Encode/H.264#crf) of 18 is set by default via `extra_args=['-crf', '18']`. See [FFMpegWriter][matplotlib.animation.FFMpegWriter].

    Returns
    -------
    None

    Examples
    --------
    ???+ example "Basic usage with a single plot object"
        ```python
        import matplotlib.pyplot as plt
        import numpy as np

        import ozzy as oz
        import ozzy.plot as oplt

        time = np.arange(0, 10, 0.1)
        x = np.arange(-20, 0, 0.2)
        X, T = np.meshgrid(x, time)
        data = np.sin(X - 0.5 * T)
        da = oz.DataArray(
            data, coords={"time": time, "x": x}, dims=["time", "x"], pic_data_type="grid"
        )

        # Create a figure and plot
        fig, ax = plt.subplots()
        line = da.isel(time=0).plot()

        # Create the movie
        oplt.movie(fig, {line[0]: (da, "time")}, "sine_wave.mp4")
        # This will create an animation of a sine wave in 'sine_wave.mp4'
        ```

    ???+ example "Using multiple plot objects and custom limits"
        ```python
        import matplotlib.pyplot as plt
        import numpy as np

        import ozzy as oz
        import ozzy.plot as oplt

        time = np.arange(0, 10, 0.1)
        x = np.arange(-20, 0, 0.2)
        X, T = np.meshgrid(x, time)
        data1 = np.sin(X - 0.5 * T)
        data2 = np.cos(X - 0.5 * T)
        da1 = oz.DataArray(
            data1, coords={"time": time, "x": x}, dims=["time", "x"], pic_data_type="grid"
        )
        da2 = oz.DataArray(
            data2, coords={"time": time, "x": x}, dims=["time", "x"], pic_data_type="grid"
        )

        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1)
        (line1,) = da1.isel(time=0).plot(ax=ax1)
        (line2,) = da2.isel(time=0).plot(ax=ax2)

        # Create the movie with custom limits
        oplt.movie(
            fig,
            {line1: (da1, "time"), line2: (da2, "time")},
            "trig_functions.mp4",
            xlim={line1: (-5, 0), line2: (-20, -5)},
            ylim=(-1.5, 1.5),
            fps=10,
        )
        # This will create an animation of sine and cosine waves
        # with different x-axis limits for each subplot
        ```
    """
    # Define default time variables
    for k, v in plot_objs.items():
        if not isinstance(v, tuple):
            plot_objs[k] = (v, "t")
        elif isinstance(v, tuple) & (len(v) < 2):
            plot_objs[k] = (v, "t")
        if plot_objs[k][1] not in plot_objs[k][0].coords:
            raise ValueError(
                f"Could not find '{v[1]}' variable in {v[0].name} DataArray. Please specify a valid time coordinate for this DataArray in the dictionary of the 'plot_objs' argument."
            )

    # Define video file's metadata
    metadata = {"artist": "ozzy"}

    # Process time range
    if t_range is None:
        t_range = (None, None)

    # Set tmin and tmax
    if t_range[0] is None:
        tmin = list(plot_objs.values())[0][0][list(plot_objs.values())[0][1]][0]
        for da, tvar in plot_objs.values():
            if da[tvar][0] < tmin:
                tmin = da[tvar][0]
    else:
        tmin = t_range[0]
    if t_range[1] is None:
        tmax = list(plot_objs.values())[0][0][list(plot_objs.values())[0][1]][-1]
        for da, tvar in plot_objs.values():
            if da[tvar][-1] > tmax:
                tmax = da[tvar][-1]
    else:
        tmax = t_range[1]

    # Choose time array with the most points
    da1 = list(plot_objs.values())[0][0]
    tvar1 = list(plot_objs.values())[0][1]
    t_arr = da1[tvar1].sel({tvar1: slice(tmin, tmax)})
    nt = t_arr.size
    for da, tvar in plot_objs.values():
        t_new = da[tvar].sel({tvar: slice(tmin, tmax)})
        nt_curr = t_new.size
        if nt_curr > nt:
            nt = nt_curr
            t_arr = t_new

    # Process axis limits

    def process_lims(arg):
        if not isinstance(arg, dict):
            lims_arr = arg
            lims_out = {}
            for k in plot_objs.keys():
                lims_out[k] = lims_arr
        else:
            lims_out = arg
        return lims_out

    def process_clims(arg):
        if not isinstance(arg, dict):
            lims_out = {}
            for k in plot_objs.keys():
                if (arg is None) & clim_fixed:
                    lims_out[k] = k.get_clim() if hasattr(k, "get_clim") else None
                else:
                    lims_out[k] = arg
        else:
            lims_out = arg
        return lims_out

    xlim = process_lims(xlim)
    ylim = process_lims(ylim)
    clim = process_clims(clim)

    # Process plot_func

    if not isinstance(plot_func, dict):
        new_plot_func = {}
        for k in plot_objs.keys():
            new_plot_func[k] = plot_func
        plot_func = new_plot_func

    # Create mutable plot objects

    mpos = []
    for k, v in plot_objs.items():
        mpos.append(
            MutablePlotObj(
                k, k.axes, v[0], v[1], xlim[k], ylim[k], clim[k], plot_func[k]
            )
        )

    # Create necessary directories

    folderpath = os.path.dirname(filename)
    if folderpath != "":
        os.makedirs(folderpath, exist_ok=True)

    # Select and initialize writer

    error_msg = {}
    match writer:
        case "ffmpeg":
            if "extra_args" in kwargs:
                if "-crf" in kwargs["extra_args"]:
                    f_kwargs = kwargs
                else:
                    kwargs["extra_args"].append("-crf")
                    kwargs["extra_args"].append("18")
                    f_kwargs = kwargs
            else:
                kwargs["extra_args"] = ["-crf", "18"]
                f_kwargs = kwargs
            mwriter = manim.FFMpegWriter(
                fps=fps,
                metadata=metadata,
                **f_kwargs,
            )
            error_msg["ffmpeg"] = (
                "The FFMpeg library must be installed to save movies. See: https://ffmpeg.org/"
            )
        case "pillow":
            mwriter = manim.PillowWriter(
                fps=fps,
                metadata=metadata,
            )
            error_msg["pillow"] = ""
        case "html":
            mwriter = manim.HTMLWriter(
                fps=fps,
                metadata=metadata,
            )
            error_msg["html"] = ""
        case "imagemagick":
            mwriter = manim.ImageMagickWriter(
                fps=fps,
                metadata=metadata,
            )
            error_msg["imagemagick"] = ""
        case "frames_png":
            mwriter = None
        case _:
            raise ValueError(
                "Unrecognised animation writer. Available options for 'writer' keyword are: 'ffmpeg' (default), 'pillow', 'html', 'imagemagick', and 'frames_png' (save image frames only). See https://matplotlib.org/stable/api/animation_api.html#writer-classes for more info."
            )

    if mwriter is None:
        # Save image frames only

        folderpath = os.path.abspath(os.path.expanduser(filename))
        os.makedirs(folderpath, exist_ok=True)

        i = 0
        for tval in tqdm(t_arr):
            for obj in mpos:
                obj.redraw(tval)
            fig.savefig(f"{folderpath}/frame_{i:04}.png")
            i += 1

        print(f"\nImage frames saved to folder {folderpath}")

    else:
        # Use matplotlib writer

        if not mwriter.isAvailable():
            raise Exception(
                f"{mwriter.__name__} is not available. " + error_msg[writer]
            )

        with mwriter.saving(fig, filename, dpi=dpi):
            for tval in tqdm(t_arr):
                for obj in mpos:
                    obj.redraw(tval)
                mwriter.grab_frame()

        print(f"\nMovie saved to file {filename}")

    return


def imovie(
    da: xr.DataArray,
    tvar: str = "t",
    clim: str | Iterable[float, float] | None = "first",
    colormap: str | None = None,
    widget_location: str = "bottom",
    **kwargs,
):
    """Creates an interactive movie/animation plot from a DataArray using HoloViews.

    Parameters
    ----------
    da : xarray.DataArray
        Input data array to animate.
    tvar : str, optional
        Name of the time coordinate in the DataArray.
    clim : str | tuple of float, optional
        Color limits specification. Can be:
        - `"first"`: Use min/max of first time step
        - `"global"`: Use global min/max across all time steps
        - `None`: Color scale changes at every time step
        - tuple of (min, max) values
    colormap : str, optional
        Name of colormap to use. If `None`, automatically selects:
        - `"cmc.lipari"` for single-signed data
        - `"cmc.vik"` for data crossing zero
    widget_location : str, optional
        Location of the time selection widget.
    **kwargs : dict
        Additional keyword arguments passed to [`hvplot`](https://hvplot.holoviz.org/user_guide/Gridded_Data.html).

    Returns
    -------
    holoviews.core.spaces.HoloMap
        Interactive HoloViews plot object.

    Raises
    ------
    ValueError
        If specified time variable is not found in coordinates.
        If `clim` is invalid type or wrong length.

    Examples
    --------
    ???+ example "Basic usage with default settings"
        ```python
        import ozzy as oz
        import ozzy.plot as oplt
        import numpy as np

        # Create sample data
        time = np.arange(10)
        data = np.random.rand(10, 20, 30)
        da = oz.DataArray(data, coords={'t': time, 'y': range(20), 'x': range(30)})

        # Create interactive plot
        oplt.imovie(da)
        ```

    ???+ example "Custom time coordinate and color limits"
        ```python
        ... # see example above

        # Create data with custom time coordinate
        da = oz.DataArray(data, coords={'time': time, 'y': range(20), 'x': range(30)})

        # Plot with custom settings
        oplt.imovie(da, tvar='time', clim=(-1, 1), colormap='cmc.lisbon')
        ```
    """

    hvplot.extension("matplotlib")

    # Check whether tvar is valid
    if tvar not in da.coords:
        raise ValueError(
            f"Could not find '{tvar}' variable in the DataArray. Please specify a valid time coordinate for this DataArray with the 'tvar' keyword argument."
        )

    # Get clims
    if isinstance(clim, str) | (clim is None):
        match clim:
            case "first":
                clims = (
                    da.isel({tvar: 0}).min().compute().to_numpy(),
                    da.isel({tvar: 0}).max().compute().to_numpy(),
                )
            case "global":
                clims = (
                    da.min().compute().to_numpy(),
                    da.max().compute().to_numpy(),
                )
            case None:
                clims = None
            case _:
                raise ValueError(
                    "Keyword argument 'clim' must be one of: None, 'first', 'global', or an iterable containing two elements."
                )
    else:
        if len(clim) != 2:
            raise ValueError(
                "Keyword argument 'clim' should be an iterable containing two numbers."
            )
        clims = clim

    # Choose colormap
    if colormap is None:
        glob_max = da.max()
        glob_min = da.min()

        signs = [np.sign(glob_max), np.sign(glob_min)]
        for i, sgn in enumerate(signs):
            if sgn == 0:
                signs[i] = signs[i - 1]

        if signs[0] == signs[1]:
            colormap = "cmc.lipari"
        else:
            colormap = "cmc.vik"
            if isinstance(clim, str):
                largest = max([abs(val) for val in clims])
                clims = (-largest, largest)

    # Override widget_type if it is in kwargs
    if "widget_type" in kwargs:
        hvobj = da.hvplot(
            groupby=tvar,
            clim=clims,
            widget_location=widget_location,
            colormap=colormap,
            **kwargs,
        )
    else:
        hvobj = da.hvplot(
            groupby=tvar,
            clim=clims,
            widget_type="scrubber",
            widget_location=widget_location,
            colormap=colormap,
            **kwargs,
        )

    return hvobj
