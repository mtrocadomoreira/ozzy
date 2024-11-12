# *********************************************************
# Copyright (C) 2024 Mariana Moreira - All Rights Reserved
# You may use, distribute and modify this code under the
# terms of the MIT License.

# You should have received a copy of the MIT License with
# this file. If not, please write to:
# mtrocadomoreira@gmail.com
# *********************************************************


import re

import numpy as np
import xarray as xr
from flox.xarray import xarray_reduce

from .new_dataobj import new_dataset
from .utils import axis_from_extent, bins_from_axis, get_attr_if_exists, stopwatch


class PartMixin:
    """Mixin class for operations on particle-like data objects.

    The methods in this class are accessible to a data object when `<data_obj>.attrs['pic_data_type'] == 'part'`.

    """

    @staticmethod
    def _define_q_units(raw_sdims, rvar_attrs: dict | None):
        if all("units" in raw_sdims[each].attrs for each in raw_sdims.data_vars):
            ustrings = [
                raw_sdims[each].attrs["units"].strip("$")
                for each in raw_sdims.data_vars
            ]
            extra = ""
            for ustr in ustrings:
                extra += rf"/ {ustr}"
            if rvar_attrs is not None:
                extra += rf"/ {rvar_attrs["units"].strip("$")}"
            units_str = rf"$Q_w {extra}$"
        else:
            units_str = "a.u."
        return units_str

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

                newlname = get_attr_if_exists(
                    self._obj[dim], "long_name", lambda x: f"mean({x})", "mean"
                )
                result[dim + "_mean"].attrs["long_name"] = newlname

                newunits = get_attr_if_exists(self._obj[dim], "units")
                if newunits is not None:
                    result[dim + "_mean"].attrs["units"] = newunits

            else:
                result[dim + "_std"] = np.sqrt(result[dim + "_sqw"])

            result[dim + "_std"].attrs["long_name"] = get_attr_if_exists(
                self._obj[dim], "long_name", lambda x: f"std({x})", "std"
            )

            newunits = get_attr_if_exists(self._obj[dim], "units")
            if newunits is not None:
                result[dim + "_std"].attrs["units"] = newunits

            result = result.drop_vars(dim + "_sqw")

        result.attrs["pic_data_type"] = "grid"

        print("\nDone!")

        return result

    # BUG: debug units
    @stopwatch
    def bin_into_grid(
        self,
        axes_ds: xr.Dataset,
        time_dim: str = "t",
        weight_var: str = "q",
        r_var: str | None = None,
    ):
        r"""
        Bin particle data into a grid (density distribution).

        Parameters
        ----------
        axes_ds : Dataset
            Dataset containing grid axes information.

            ??? tip
                The axis information can be easily obtained from a grid Dataset (for example field data) with
                ```python
                axes_ds = fields_ds.coords
                ```

            ??? note "Note about axis attributes"

                By default, the `long_name` and `units` attributes of the resulting grid axes are taken from the original particle Dataset. But these attributes are overriden if they are passed along with the `axes_ds` Dataset.

        time_dim : str, optional
            Name of the time dimension in the input datasets.
        weight_var : str, optional
            Name of the variable representing particle weights or particle charge.
        r_var : str | None, optional
            Name of the variable representing particle radial positions. If provided, the particle weights are divided by this variable.

        Returns
        -------
        parts : xarray.Dataset
            Dataset containing the charge density distribution on the grid.

        Raises
        ------
        KeyError
            If no spatial dimensions are found in the input `axes_ds`.
        ValueError
            If the `axes_ds` argument does not contain grid data.

        Notes
        -----
        The binned density data is multiplied by a factor that ensures that the total volume integral of the density corresponds to the sum of all particle weights $Q_w$. If $w$ is each particle's weight variable and $N_p$ is the total number of particles, then $Q_w$ is defined as:

        \[
        Q_w = \sum_i^{N_p} w_i
        \]

        Note that different simulation codes have different conventions in terms of what $Q_w$ corresponds to.

        Examples
        --------

        ???+ example "Usage"

            ```python
            import ozzy as oz
            import numpy as np

            # Create a sample particle dataset
            particles = oz.Dataset(
                {
                    "x1": ("pid", np.random.uniform(0, 10, 10000)),
                    "x2": ("pid", np.random.uniform(0, 5, 10000)),
                    "q": ("pid", np.ones(10000)),
                },
                coords={"pid": np.arange(10000)},
                attrs={"pic_data_type": "part"}
            )

            # Create axes for binning
            axes = oz.Dataset(
                coords={
                    "x1": np.linspace(0, 10, 101),
                    "x2": np.linspace(0, 5, 51),
                },
                attrs={"pic_data_type": "grid"}
            )

            # Bin particles into grid (Cartesian geometry)
            grid_data = particles.ozzy.bin_into_grid(axes)

            # Example 2: Using a different weight variable
            particles["w"] = ("pid", np.random.uniform(0.5, 1.5, 10000))
            grid_data_weighted = particles.ozzy.bin_into_grid(axes, weight_var="w")

            # Example 3: Axisymmetric geometry
            grid_data_axisym = particles.ozzy.bin_into_grid(axes, r_var="x2")

            # Example 4: Time-dependent data
            time_dependent_particles = particles.expand_dims(dim={"t": [0, 1, 2]})
            time_dependent_grid = time_dependent_particles.ozzy.bin_into_grid(axes)

            ```
        """

        # Check grid dataset
        if "grid" not in axes_ds.attrs["pic_data_type"]:
            raise ValueError(
                "Axes Dataset must contain grid data (pic_data_type attribute must contain 'grid')"
            )

        # Check spatial dims
        spatial_dims = axes_ds.ozzy.get_space_dims(time_dim)
        if len(spatial_dims) == 0:
            raise KeyError("Did not find any non-time dimensions in input axes dataset")

        # Get bin edges
        bin_edges = axes_ds.ozzy.get_bin_edges(time_dim)

        q_binned = []
        raw_ds = self._obj

        # Multiply weight by radius, if r_var is specified

        def integrate_cart(da):
            dx_factor = 1
            for dim in spatial_dims:
                dx = axes_ds[dim][1] - axes_ds[dim][0]
                dx_factor = dx_factor * dx
            return dx_factor * da.sum(dim=spatial_dims)

        def integrate_cyl(da):
            dx_factor = 1
            for dim in spatial_dims:
                dx = axes_ds[dim][1] - axes_ds[dim][0]
                dx_factor = dx_factor * dx
            return dx_factor * (da[r_var] * da).sum(dim=spatial_dims)

        total_w = raw_ds[weight_var].sum()

        print("\nBinning particles into grid...")
        if r_var is None:
            wvar = weight_var
            integrate = integrate_cart
            print("\n   - assuming Cartesian geometry")
        else:
            raw_ds["w"] = raw_ds[weight_var] / raw_ds[r_var]
            wvar = "w"
            if r_var in axes_ds:
                integrate = integrate_cyl
            else:
                integrate = integrate_cart
            print("\n   - assuming axisymmetric geometry")

        def get_dist(ds):
            part_coords = [ds[var] for var in spatial_dims]
            dist, edges = np.histogramdd(part_coords, bins=bin_edges, weights=ds[wvar])
            return dist

        # Loop along time

        if "t" in raw_ds.dims:
            for i in np.arange(0, len(raw_ds[time_dim])):
                ds_i = raw_ds.isel({time_dim: i})
                dist = get_dist(ds_i)

                newcoords = {var: axes_ds[var] for var in spatial_dims}
                newcoords[time_dim] = ds_i[time_dim]
                qds_i = new_dataset(
                    data_vars={"rho": (spatial_dims, dist)},
                    coords=newcoords,
                    pic_data_type="grid",
                    data_origin=raw_ds.attrs["data_origin"],
                )
                q_binned.append(qds_i)

            parts = xr.concat(q_binned, time_dim)

        else:
            dist = get_dist(raw_ds)
            newcoords = {var: axes_ds[var] for var in spatial_dims}
            parts = new_dataset(
                data_vars={"rho": (spatial_dims, dist)},
                coords=newcoords,
                pic_data_type="grid",
                data_origin=raw_ds.attrs["data_origin"],
            )

        # TODO: improve the formatting of the resulting units
        if r_var is None:
            rvar_attrs = None
        else:
            rvar_attrs = raw_ds[r_var].attrs
        units_str = self._define_q_units(raw_ds[spatial_dims], rvar_attrs)

        # Multiply by factor to ensure that integral of density matches sum of particle weights
        factor = total_w / integrate(parts["rho"])
        parts["rho"] = factor * parts["rho"]

        parts["rho"] = parts["rho"].assign_attrs(
            {"long_name": r"$\rho$", "units": units_str}
        )

        # Assign variable attributes
        for var in parts.coords:
            parts.coords[var] = parts.coords[var].assign_attrs(raw_ds[var].attrs)

            if var in spatial_dims:
                for attr_override in ["long_name", "units"]:
                    label = get_attr_if_exists(axes_ds[var], attr_override)
                    if label is not None:
                        parts.coords[var].attrs[attr_override] = label

        # Reorder and rechunk dimensions (e.g. x2,x1,t)

        dims_3d = ["x3", "x1", "x2"]
        dims_2d = ["x2", "x1"]
        dims_3d_box = ["x3", "x1_box", "x2"]
        dims_2d_box = ["x2", "x1_box"]

        for option in [dims_2d, dims_2d_box, dims_3d, dims_3d_box]:
            if all([var in parts.dims for var in option]):
                new_coords = option + ["t"] if "t" in parts.dims else option
                parts = parts.transpose(*new_coords).compute()
                parts = parts.chunk()

        return parts

    def get_phase_space(
        self,
        vars: list[str],
        extents: dict[str, tuple[float, float]] | None = None,
        nbins: int | dict[str, int] = 200,
        axisym: bool = False,
        r_var: str = "x2",
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
        axisym : bool, optional
            Whether geometry is 2D cylindrical (axisymmetric), in which case the particle weights are divided by the radial coordinate (`r_var`).
        r_var : str, optional
            Name of the radial coordinate. This argument is ignored if `axisym = False`.

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

                if minval == maxval:
                    minval = minval - 0.05 * abs(minval)
                    maxval = maxval + 0.05 * abs(maxval)

                if (minval < 0) & (maxval > 0):
                    extr = max([abs(minval), maxval])
                    lims = (-extr, extr)
                else:
                    lims = (minval, maxval)
                if lims[0] == lims[1]:
                    lims = (lims[0] - 0.5, lims[0] + 0.5)
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

        if axisym:
            r_arg = r_var
        else:
            r_arg = None

        ps = self.bin_into_grid(axes_ds, r_var=r_arg)
        ps["rho"].attrs["units"] = r"a.u."

        return ps

    # TODO: assumes that momentum variables follow the pattern "p?"
    # TODO: add unit tests
    def get_emittance(
        self,
        xvar: str = "x2",
        pvar: str = "p2",
        wvar: str = "q",
        p_longit: str = "p1",
        axisym: bool = False,
    ) -> xr.DataArray:
        r"""Calculate normalized RMS beam emittance.

        Computes the normalized RMS emittance based on particle positions and momenta.
        For axisymmetric beams, returns the emittance (see _Notes_ below).

        Parameters
        ----------
        xvar : str
            Variable name for position coordinate in Dataset
        pvar : str
            Variable name for momentum coordinate in Dataset
        wvar : str
            Variable name for particle weights in Dataset
        p_longit : str
            Variable name for longitudinal momentum in Dataset
        axisym : bool
            If `True`, calculate Lapostolle emittance for axisymmetric beams

        Returns
        -------
        xarray.DataArray
            Normalized emittance with attributes containing units and label information

        Notes
        -----
        The normalized RMS emittance along a given transverse dimension $i$ is calculated according to:

        $\varepsilon_{N,i} = \gamma \sqrt{\left<x_i^2\right> \left<{x'_i}^2\right> - \left(x_i x'_i\right)^2}$

        where $\gamma$ is the average Lorentz factor, $x_i$ is the particle position, and $x'_i \approx p_i / p_\parallel$ is the trace for relativistic particles with longitudinal momentum $p_\parallel$ and transverse momentum $p_i \ll p_\parallel$.

        For a 2D cylindrical, axisymmetric geometry this function returns the Lapostolle emittance[^1]<sup>,</sup>[^2], i.e.:

        $\varepsilon_N = 4 \ \varepsilon_{N,i}$


        [^1]: [J. D. Lawson, P. M. Lapostolle, and R. L. Gluckstern, Particle Accelerators **5**, 61–65 (1973)](https://inspirehep.net/literature/87013),
        [^2]: [P. M. Lapostolle, IEEE Transactions on Nuclear Science **18**, 1101–1104 (1971)](https://ieeexplore-ieee-org.ezproxy.cern.ch/document/4326292)




        Examples
        --------
        ???+ example "Calculate normalized emittance in 2D cyl. geometry"
            ```python
            import ozzy as oz
            import numpy as np

            # Create a sample particle dataset
            particles = oz.Dataset(
                {
                    "x": ("pid", np.random.uniform(0, 10, 10000)),
                    "r": ("pid", np.random.uniform(0, 5, 10000)),
                    "px": ("pid", np.random.uniform(99, 101, 10000)),
                    "pr": ("pid", np.random.uniform(-2e-4, 2e-4, 10000)),
                    "q": ("pid", np.ones(10000)),
                },
                coords={"pid": np.arange(10000)},
                attrs={"pic_data_type": "part"}
            )

            emittance = particles.ozzy.get_emittance(xvar="r", pvar="pr", p_longit="px", axisym=True)
            # Returns DataArray with normalized emittance in k_p^(-1) rad
            ```
        """

        ds = self._obj

        # Process xvar and pvar arguments
        for ivar in [xvar, pvar]:
            if ivar not in ds.data_vars:
                raise KeyError(f"Cannot find '{ivar}' variable in Dataset")

        # Calculate geometric emittance

        # - get trace
        x_prime = ds[pvar] / ds[p_longit]

        # - calculate geometric emittance
        x_sq = (ds[wvar] * ds[xvar] ** 2).sum(dim="pid") / ds[wvar].sum(dim="pid")
        x_prime_sq = (ds[wvar] * x_prime**2).sum(dim="pid") / ds[wvar].sum(dim="pid")
        x_x_prime = (ds[wvar] * ds[xvar] * x_prime).sum(dim="pid") / ds[wvar].sum(
            dim="pid"
        )
        emit = np.sqrt(x_sq * x_prime_sq - x_x_prime**2)

        # Get energy

        # - find all momentum variables
        p_vars = []
        matches = [re.fullmatch("p[A-Za-z0-9]", var) for var in list(ds.data_vars)]
        for item in matches:
            if item is not None:
                p_vars.append(item.group(0))

        # - calculate average Lorentz factor
        p_abs_sqr = 0
        for p_var in p_vars:
            p_abs_sqr += ds[p_var] ** 2

        gamma_parts = np.sqrt(1 + p_abs_sqr)
        gamma = (ds[wvar] * gamma_parts).sum(dim="pid") / ds[wvar].sum(dim="pid")

        # Get normalized emittance

        if axisym:
            # Lapostolle emittance
            emit_norm = 4 * gamma * emit
        else:
            emit_norm = gamma * emit

        # Set units and label

        emit_norm = emit_norm.rename("emit_norm")
        emit_norm.attrs["units"] = r"$k_p^{-1} \ \mathrm{rad}$"
        if axisym:
            emit_norm.attrs["long_name"] = r"$\varepsilon_N$"
        else:
            emit_norm.attrs["long_name"] = r"$\varepsilon_{N," + str(pvar[1]) + "}$"

        return emit_norm

    # TODO: slice emittance
    # - maybe use groupby to bin and perform operation
