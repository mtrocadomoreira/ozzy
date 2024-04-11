import ozzy as oz
import ozzy.fields as flds

# path = "/Volumes/Mariana/Simulations/LCODE/gap_position_scan/from_002400/10m_noramp/xi_Ez_concat.h5"
path = "~/cernbox/Simulations/LCODE/gap_position_scan/from_002400/10m_noramp/xi_Ez_concat.h5"
ds = oz.open("ozzy", path)

ds_small = ds["xi_Ez"].sel(x1=slice(-200.0, 0.0))

res = flds.ave_vphi_from_waterfall(ds_small, dcells=(37, 501))

# res_ds = xr.Dataset(data_vars={"vphi": res}, coords=res.coords)

res.ozzy.save("vphi_100.h5")
