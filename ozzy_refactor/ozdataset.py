import xarray as xr


class OzDataset(xr.Dataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
