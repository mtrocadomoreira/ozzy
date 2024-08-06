import os
import tempfile

import numpy as np
import pytest
import xarray as xr

from ozzy.backends.ozzy_backend import config_ozzy, read


@pytest.fixture
def mock_h5_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            ds = xr.Dataset(
                {"q": (["x", "y"], np.random.rand(10, 10))},
                coords={"x": range(10), "y": range(10), "t": [i]},
            )
            ds.to_netcdf(os.path.join(tmpdir, f"test_{i}.h5"), engine="h5netcdf")
        yield [os.path.join(tmpdir, f"test_{i}.h5") for i in range(3)]


def test_read_multiple_files(mock_h5_files):
    result = read(mock_h5_files)
    assert isinstance(result, xr.Dataset)
    assert "q" in result.data_vars
    assert result.sizes["t"] == 3
    assert "source" in result.attrs
    assert "files_prefix" in result.attrs


def test_read_single_file(mock_h5_files):
    result = read([mock_h5_files[0]])
    assert isinstance(result, xr.Dataset)
    assert "q" in result.data_vars
    assert result.sizes["t"] == 1


def test_read_empty_file_list():
    result = read([])
    assert isinstance(result, xr.Dataset)
    assert len(result.data_vars) == 0


def test_config_ozzy():
    ds = xr.Dataset(
        {"q": (["x", "y"], np.random.rand(10, 10))},
        coords={"x": range(10), "y": range(10), "t": [0]},
    )
    result = config_ozzy(ds)
    assert "t" in result.dims
    assert result.sizes["t"] == 1


def test_config_ozzy_no_t_coord():
    ds = xr.Dataset(
        {"q": (["x", "y"], np.random.rand(10, 10))},
        coords={"x": range(10), "y": range(10)},
    )
    result = config_ozzy(ds)
    assert result.equals(ds)
