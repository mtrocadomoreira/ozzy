import seaborn as sns
import os

import matplotlib.font_manager as fm
font_dirs = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')
font_files = fm.findSystemFonts(fontpaths=font_dirs)
for font_file in font_files:
    fm.fontManager.addfont(font_file)

ozparams = {
    'mathtext.fontset': 'cm',
    'font.serif': ['Noto Serif', 'serif'],
    'font.sans-serif': ['Arial', 'Helvetica', 'sans'],
    'text.usetex': False,
    'axes.grid': True,
    'grid.color': '.9',
    'axes.linewidth': '0.75',
    'xtick.major.width': '0.75',
    'ytick.major.width': '0.75',
    'lines.linewidth': '0.5',
    'figure.figsize': ('8.0','4.8'),
    'figure.dpi': '300',
    'image.cmap': 'magma',
    'savefig.format': 'pdf',
    'savefig.transparent': True,
    'legend.fontsize': 'x-small',
}

sns.set_theme(style='ticks', palette='husl', font='serif', font_scale=1.1, rc=ozparams)