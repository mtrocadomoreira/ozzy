import numpy as np
import xarray as xr


class OzDataset(xr.Dataset):
    __slots__ = "data_type"

    def __init__(self, type: str | list[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_type = type

    @staticmethod
    def axis_from_extent(nx: int, lims: tuple[float, float]):
        if nx == 0:
            raise ZeroDivisionError("Number of cells in axis cannot be zero.")
        dx = (lims[1] - lims[0]) / nx
        ax = np.linspace(lims[0], lims[1] - dx, num=nx) + 0.5 * dx
        return ax

    def coords_from_extent(self, mapping: dict[str, tuple[float, float]]):
        for k, v in mapping.items():
            nx = self.sizes[k]
            ax = self.axis_from_extent(nx, v)
        return self.assign_coords({k: ax})

    def coord_to_physical_distance(self, coord: str, n0: float, units: str = "m"):
        # HACK: make this function pint-compatible
        if not any([units == opt for opt in ["m", "cm"]]):
            raise KeyError('Error: "units" keyword must be either "m" or "cm"')

        # Assumes n0 is in cm^(-3), returns skin depth in meters
        skdepth = 3e8 / 5.64e4 / np.sqrt(n0)
        if units == "cm":
            skdepth = skdepth * 100.0

        if coord not in self.coords:
            print(
                "\nWARNING: Could not find coordinate in dataset. No changes made to dataset."
            )
            newds = self
        else:
            newcoord = coord + "_" + units
            newds = self.assign_coords({newcoord: skdepth * self.coords[coord]})
            newds[newcoord] = newds[newcoord].assign_attrs(
                long_name="$" + coord + "$", units=r"$\mathrm{" + units + "}$"
            )

        return newds

    def sample_particles(self, n):
        if "part" not in self.data_type:
            raise TypeError(
                "Dataset must contain particle data for this method to be used"
            )

        dvar = list(set(list(self)) - {"pid", "t", "q"})[0]

        if "t" in self.dims:
            surviving = self[dvar].isel(t=-1).notnull().compute()
            pool = self.coords["pid"][surviving]
        else:
            pool = self.coords["pid"]
        nparts = len(pool)

        if n > nparts:
            print(
                "WARNING: number of particles to be sampled is larger than total particles. Proceeding without any sampling."
            )
            newds = self
        else:
            rng = np.random.default_rng()
            downsamp = rng.choice(pool["pid"], size=n, replace=False, shuffle=False)
            newds = self.sel(pid=np.sort(downsamp))

        return newds
