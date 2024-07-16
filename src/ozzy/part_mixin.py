# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************


import numpy as np
import xarray as xr
from flox.xarray import xarray_reduce

from .new_dataobj import new_dataset
from .statistics import parts_into_grid
from .utils import axis_from_extent, bins_from_axis


class PartMixin:
    """Mixin class for operations on particle-like data objects.

    The methods in this class are accessible to a data object when `<data_obj>.attrs['pic_data_type'] == 'part'`.

    """

    def sample_particles(self, n: int) -> xr.Dataset:
        """Downsample a particle Dataset by randomly choosing particles.

        Parameters
        ----------
        n : int
            Number of particles to sample.

        Returns
        -------
        xarray.Dataset
            Dataset with sampled particles.

        Examples
        --------

        ???+ example "Sample 1000 particles"
            ```python
            import ozzy as oz
            import numpy as np


            # Create a sample particle dataset
            ds = oz.Dataset(
                {
                    "x1": ("pid", np.random.rand(10000)),
                    "x2": ("pid", np.random.rand(10000)),
                    "p1": ("pid", np.random.rand(10000)),
                    "p2": ("pid", np.random.rand(10000)),
                    "q": ("pid", np.ones(10000)),
                },
                coords={"pid": np.arange(10000)},
                pic_data_type="part",
                data_origin="ozzy",
            )

            # Sample 1000 particles
            ds_small = ds.ozzy.sample_particles(1000)
            print(len(ds_small.pid))
            # 1000

            # Try to sample more particles than available
            ds_all = ds.ozzy.sample_particles(20000)
            # WARNING: number of particles to be sampled is larger than total particles. Proceeding without any sampling.
            print(len(ds_all.pid))
            # 10000
            ```
        """

        dvar = list(set(list(self._obj)) - {"pid", "t", "q"})[0]

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
        axes_ds: xr.DataArray | xr.Dataset | xr.Coordinates,
        expand_time: bool = True,
        axisym: bool = False,
    ) -> xr.Dataset:
        """Calculate mean and standard deviation of variables.

        Bins the particle data onto the grid specified by `axes_ds`
        and calculates the mean and standard deviation for each bin.

        Parameters
        ----------
        vars : str | list[str]
            The variable(s) for which to calculate statistics.
        axes_ds : xarray.Dataset | xarray.DataArray | xarray.Coordinates
            Data object containing the axes to use for the calculation (as [xarray coordinates](https://docs.xarray.dev/en/v2024.06.0/user-guide/data-structures.html#coordinates)).

            !!! tip
                The axes object can be taken from an existing Dataset or DataArray via `axes_ds = <data_obj>.coords`.

        expand_time : bool, optional
            If `True`, statistics are calculated separately for each timestep.
        axisym : bool, optional
            If `True`, azimuthal symmetry is assumed.

        Returns
        -------
        xarray.Dataset
            Dataset containing the calculated mean and standard deviation of the particle variables.

        Examples
        --------

        ???+ example "Get mean and std of `'x2'` and `'p2'`"
            ```python
            import ozzy as oz
            import numpy as np

            # Create a sample particle dataset
            ds = oz.Dataset(
                {
                    "x1": ("pid", np.random.rand(10000)),
                    "x2": ("pid", np.random.rand(10000)),
                    "p1": ("pid", np.random.rand(10000)),
                    "p2": ("pid", np.random.rand(10000)),
                    "q": ("pid", np.ones(10000)),
                },
                coords={"pid": np.arange(10000)},
                pic_data_type="part",
                data_origin="ozzy",
            )

            # Create axes for binning
            axes_ds = oz.Dataset(
                coords={
                    "x1": np.linspace(0, 1, 21),
                },
                pic_data_type="grid",
                data_origin="ozzy",
            )

            # Calculate mean and standard deviation
            ds_mean_std = ds.ozzy.mean_std(["x2", "p2"], axes_ds)
            ```
        """
        if "grid" not in axes_ds.attrs["pic_data_type"]:
            raise ValueError("axes_ds must be grid data")

        if isinstance(axes_ds, xr.DataArray):
            axes_ds = new_dataset(axes_ds, pic_data_type="grid")
        elif isinstance(axes_ds, xr.Coordinates):
            axes_ds = new_dataset(coords=axes_ds, pic_data_type="grid")

        if isinstance(vars, str):
            vars = [vars]

        # Prepare binning array

        bin_arr = []
        bin_vars = []
        bin_axes = []

        for var in axes_ds.data_vars:
            axis = np.array(axes_ds[var])
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

                if "long_name" in self._obj[dim].attrs:
                    newlname = "mean(" + self._obj[dim].attrs["long_name"] + ")"
                else:
                    newlname = "mean"
                result[dim + "_mean"].attrs["long_name"] = newlname

                if "units" in self._obj[dim].attrs:
                    result[dim + "_mean"].attrs["units"] = self._obj[dim].attrs["units"]

            else:
                result[dim + "_std"] = np.sqrt(result[dim + "_sqw"])

            # TODO: make function to use long_name and units if existing, otherwise replace with something

            if "long_name" in self._obj[dim].attrs:
                newlname = "std(" + self._obj[dim].attrs["long_name"] + ")"
            else:
                newlname = "std"
            result[dim + "_std"].attrs["long_name"] = newlname

            if "units" in self._obj[dim].attrs:
                result[dim + "_std"].attrs["units"] = self._obj[dim].attrs["units"]

            result = result.drop_vars(dim + "_sqw")

        result.attrs["pic_data_type"] = "grid"

        print("\nDone!")

        return result

    def get_phase_space(
        self,
        vars: list[str],
        extents: dict[str, tuple[float, float]] | None = None,
        nbins: int | dict[str, int] = 200,
    ):
        """Generate a phase space grid from particle data.

        Creates a gridded dataset by depositing particle quantities onto
        a 2D phase space.

        Parameters
        ----------
        vars : list[str]
            Variables to deposit onto phase space.
        extents : dict[str, tuple[float,float]], optional
            Minimum and maximum extent for each variable. If not specified, extents are calculated from the data.
        nbins : int | dict[str, int], optional
            Number of bins for each variable. If `int`, the same number of bins is used for all variables.

        Returns
        -------
        xarray.Dataset
            Dataset with phase space data.

        Examples
        --------

        ???+ example "Transverse phase space"
            ```python

            import ozzy as oz
            import numpy as np

            # Create a sample particle dataset
            ds = oz.Dataset(
                {
                    "x1": ("pid", np.random.rand(10000)),
                    "x2": ("pid", np.random.rand(10000)),
                    "p1": ("pid", np.random.rand(10000)),
                    "p2": ("pid", np.random.rand(10000)),
                    "q": ("pid", np.ones(10000)),
                },
                coords={"pid": np.arange(10000)},
                pic_data_type="part",
                data_origin="ozzy",
            )

            ds_ps = ds.ozzy.get_phase_space(['p2', 'x2'], nbins=100)
            ```
        """
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
