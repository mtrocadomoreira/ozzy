
<!-- import ozzy.plot as oplt

oplt.show_cmaps(libraries=["tol", "cmc"], categories=["sequential", "qualitative"]) -->

<!-- # Plot with ozzy fonts
fonts = oplt.ozzy_fonts
nfonts = len(fonts)

axs = []
for i, font in enumerate(fonts):

    plt.rcParams["font.family"] = font
    fig, axtmp = plt.subplots()
    axs.append(axtmp)
    
    ds['np'].plot(x='t_offs_m', ax=axs[i])
    plt.ylim((0.97, 1.05))
    plt.xlim((0.0, 10.5))
    plt.grid()
    plt.title(r'Plasma density profile - ' + font)

    fig.set_figheight(2) -->

<!-- 
mention resolution: even if it looks shit, output is 300 dpi
set figure.dpi for less shitty look -->