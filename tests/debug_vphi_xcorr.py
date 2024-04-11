import matplotlib.pyplot as plt  # noqa

import ozzy as oz
import ozzy.fields as flds  # noqa
import ozzy.plot as oplot  # noqa

# import seaborn as sns

# sns.set_context('notebook')

# path = "/Volumes/Mariana/Simulations/LCODE/gap_position_scan/from_002400/10m_noramp/xi_Ez_concat.h5"
path = "~/cernbox/Simulations/LCODE/gap_position_scan/from_002400/10m_noramp/xi_Ez_concat.h5"
ds = oz.open("ozzy", path)
ds = ds["xi_Ez"].sel(x1=slice(-200.0, 0.0))

# ds_sample = ds.sel(x1=slice(-175, -150), t=slice(3000, 20000))
ds_sample = ds


ds_vphi = flds.vphi_from_xcorr(ds_sample, window_len=5.0)

ds_vphi["vphi"].plot()
plt.show()


print(ds_vphi)
