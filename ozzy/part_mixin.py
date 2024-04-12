import os

import numpy as np
import xarray as xr
from flox.xarray import xarray_reduce

from .new_dataobj import new_dataset
from .statistics import parts_into_grid
from .utils import axis_from_extent, bins_from_axis


class PartMixin:
    def sample_particles(self, n):
        dvar = list(set(list(self)) - {"pid", "t", "q"})[0]

        if "t" in self._obj.dims:
            surviving = self._obj[dvar].isel(t=-1).notnull().compute()
            pool = self._obj.coords["pid"][surviving]
        else:
            pool = self._obj.coords["pid"]
        nparts = len(pool)

        if n > nparts:
            print(
                "WARNING: number of particles to be sampled is larger than total particles. Proceeding without any sampling."
            )
            newds = self._obj
        else:
            rng = np.random.default_rng()
            downsamp = rng.choice(pool["pid"], size=n, replace=False, shuffle=False)
            newds = self._obj.sel(pid=np.sort(downsamp))

        return newds

    def mean_std(
        self,
        vars: str | list[str],
        axes_ds,
        savepath=os.getcwd(),
        outfile=None,
        expand_time=True,
        axisym=False,
    ):
        # BUG: this will probably fail because axes_ds might be a DataArray
        if "grid" not in axes_ds.attrs["pic_data_type"]:
            raise ValueError("axes_ds must be grid data")

        if isinstance(axes_ds, xr.DataArray):
            axes_ds = new_dataset(axes_ds, pic_data_type="grid")

        if isinstance(vars, str):
            vars = [vars]

        # Prepare binning array

        bin_arr = []
        bin_vars = []
        bin_axes = []

        for var in axes_ds._obj.data_vars:
            axis = np.array(axes_ds._obj[var])
            bin_axes.append(axis)
            bin_arr.append(bins_from_axis(axis))
            bin_vars.append(var)

        # Prepare dataset for calculation

        ds = self._obj[bin_vars + vars + ["q"]]

        for dim in vars:
            ds[dim + "_sqw"] = (ds[dim] ** 2) * ds["q"]
            if axisym is False:
                ds[dim + "_w"] = ds[dim] * ds["q"]
                # TODO : check if this is correct for all codes or only for LCODE
        ds = ds.drop_vars(["q"] + vars)

        # Determine bin index for each particle (and for each binning variable)

        for i, bvar in enumerate(bin_vars):
            group_id = np.digitize(ds[bvar].isel(t=0), bin_arr[i])
            group_labels = [bin_axes[i][j] for j in group_id]
            ds = ds.assign_coords({bvar + "_bin": ("pid", group_labels)})

        # Perform mean along the dataset and get final variables

        print("\nCalculating mean and standard deviation...")

        by_dims = [ds[key] for key in ds.coords if "_bin" in key]

        result = ds
        for dim_da in by_dims:
            try:
                result = xarray_reduce(
                    result,
                    dim_da,
                    func="mean",
                    sort=True,
                    dim="pid",
                    keep_attrs=True,
                    fill_value=np.nan,
                )
            except Exception:
                print(
                    "This is probably a problem with the multiple binning axes. Have to look over this."
                )
                raise

        for dim in vars:
            if axisym is False:
                result[dim + "_std"] = np.sqrt(
                    result[dim + "_sqw"] - result[dim + "_w"] ** 2
                )
                result = result.rename({dim + "_w": dim + "_mean"})

                result[dim + "_mean"] = result[dim + "_mean"].assign_attrs(
                    long_name="mean(" + self[dim].attrs["long_name"] + ")",
                    units=self[dim].attrs["units"],
                )

            else:
                result[dim + "_std"] = np.sqrt(result[dim + "_sqw"])

            result[dim + "_std"] = result[dim + "_std"].assign_attrs(
                long_name="std(" + self[dim].attrs["long_name"] + ")",
                units=self[dim].attrs["units"],
            )
            result = result.drop_vars(dim + "_sqw")

        # Save data

        if outfile is None:
            prefix = [dim + "_" for dim in vars]
            outfile = prefix + "mean_std_raw.nc"

        filepath = os.path.join(savepath, outfile)
        print("\nSaving file " + filepath)

        result.ozzy.save(filepath)

        print("\nDone!")

        return

    def get_phase_space(
        self,
        vars: list[str],
        extents: dict[str, tuple[float, float]] | None = None,
        nbins: int | dict[str, int] = 200,
    ):
        if extents is None:
            extents = {}
            for v in vars:
                maxval = float(self._obj[v].max().compute().to_numpy())
                minval = float(self._obj[v].min().compute().to_numpy())
                if (minval < 0) & (maxval > 0):
                    extr = max([abs(minval), maxval])
                    lims = (-extr, extr)
                else:
                    lims = (minval, maxval)
                extents[v] = lims

        if isinstance(nbins, int):
            bins = {}
            for v in vars:
                bins[v] = nbins
        else:
            bins = nbins

        axes_ds = new_dataset(
            pic_data_type="grid", data_origin=self._obj.attrs["data_origin"]
        )
        for v in vars:
            ax = axis_from_extent(bins[v], extents[v])
            axes_ds = axes_ds.assign_coords({v: ax})
            axes_ds[v].attrs.update(self._obj[v].attrs)

        # Deposit quantities on phase space grid

        ps = parts_into_grid(self._obj, axes_ds)
        ps = ps.rename_vars({"nb": "Q"})
        ps["Q"] = ps["Q"].assign_attrs({"units": r"a.u.", "long_name": r"$Q$"})

        return ps
