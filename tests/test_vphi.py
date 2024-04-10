import xarray as xr

import ozzy as oz
import ozzy.fields as flds

path = "/Volumes/Mariana/Simulations/LCODE/gap_position_scan/from_002400/10m_noramp/xi_Ez_concat.h5"
# path = "~/cernbox/Simulations/LCODE/gap_position_scan/from_002400/10m_noramp"
ds = oz.open("ozzy", path)
ds = oz.open("ozzy", "~/Documents/xi_Ez_concat.h5")

res = flds.ave_vphi_from_waterfall(ds["xi_Ez"], dcells=(11, 125))

res_ds = xr.Dataset(data_vars={"vphi": res}, coords=res.coords)

res_ds.ozzy.save("vphi_100.h5")
