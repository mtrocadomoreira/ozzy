import numpy as np
import pytest
import xarray as xr

from ozzy.backends.lcode_backend import (
    lcode_append_time,
    lcode_append_time_from_fname,
    lcode_concat_time,
    read,
    read_grid_single,
    read_lineout_single,
    read_parts_single,
    set_quant_metadata,
)


@pytest.fixture
def sample_dataset():
    return xr.Dataset(
        {"var": (["x", "y"], np.random.rand(5, 5))},
        coords={"x": range(5), "y": range(5)},
    )


def test_lcode_append_time():
    ds = xr.Dataset({"var": (["x"], [1, 2, 3])})
    result = lcode_append_time(ds, 10.0)
    assert "t" in result.coords
    assert result.coords["t"].values == [10.0]
    assert result.coords["t"].attrs["long_name"] == r"$t$"
    assert result.coords["t"].attrs["units"] == r"$\omega_p^{-1}$"


def test_lcode_append_time_from_fname():
    ds = xr.Dataset({"var": (["x"], [1, 2, 3])})
    result = lcode_append_time_from_fname(ds, "file_000100.dat")
    assert "t" in result.coords
    assert result.coords["t"].values == [100.0]


def test_lcode_concat_time():
    ds1 = xr.Dataset({"var": (["x", "t"], [[1, 2], [3, 4]])}, coords={"t": [0, 1]})
    ds2 = xr.Dataset({"var": (["x", "t"], [[5, 6], [7, 8]])}, coords={"t": [2, 3]})
    result = lcode_concat_time([ds1, ds2])
    assert result.sizes["t"] == 4
    assert np.all(result.coords["t"].values == [0, 1, 2, 3])


def test_set_quant_metadata():
    ds = xr.Dataset({"x1": (["pid"], [1, 2, 3])})
    result = set_quant_metadata(ds, "parts")
    assert result["x1"].attrs["long_name"] == r"$\xi$"
    assert result["x1"].attrs["units"] == r"$k_p^{-1}$"


@pytest.mark.parametrize("file_type", ["parts", "grid", "extrema", "lineout"])
def test_set_quant_metadata_different_types(file_type):
    ds = xr.Dataset({"var": (["x"], [1, 2, 3])})
    result = set_quant_metadata(ds, file_type)
    assert "long_name" in result["var"].attrs


@pytest.fixture
def mock_parts_file(tmp_path):
    file = tmp_path / "test_parts.swp"
    data = np.array([[1, 2, 3, 4, 5, 6, 7, 8]] * 10, dtype=float)
    data.tofile(file)
    return str(file)


def test_read_parts_single(mock_parts_file):
    result = read_parts_single(mock_parts_file)
    assert isinstance(result, xr.Dataset)
    assert set(result.data_vars) == {"x1", "x2", "p1", "p2", "L", "abs_rqm", "q"}
    assert "pid" in result.coords


@pytest.fixture
def mock_lineout_file(tmp_path):
    file = tmp_path / "test_lineout.swp"
    data = np.array([1, 2, 3, 4, 5])
    np.savetxt(file, data)
    return str(file)


def test_read_lineout_single(mock_lineout_file):
    result = read_lineout_single(mock_lineout_file, "test_quant")
    assert isinstance(result, xr.Dataset)
    assert "test_quant" in result.data_vars
    assert result.sizes["x1"] == 5


@pytest.fixture
def mock_grid_file(tmp_path):
    file = tmp_path / "test_grid.swp"
    data = np.random.rand(5, 5)
    np.savetxt(file, data)
    return str(file)


def test_read_grid_single(mock_grid_file):
    result = read_grid_single(
        mock_grid_file, "test_quant", {"x1": (0, 1), "x2": (0, 1)}
    )
    assert isinstance(result, xr.Dataset)
    assert "test_quant" in result.data_vars
    assert set(result.dims) == {"x1", "x2", "t"}


def test_read_empty_file_list():
    result = read([])
    assert isinstance(result, xr.Dataset)
    assert len(result.data_vars) == 0


@pytest.mark.parametrize(
    "dxi,n0,expected_units",
    [
        (0.01, None, "$e$"),
        (0.01, 2e14, "$e$"),
    ],
)
def test_convert_q(sample_dataset, dxi, n0, expected_units):
    sample_dataset = sample_dataset.assign(q=("x", np.random.rand(5)))
    sample_dataset.attrs["data_origin"] = "lcode"
    sample_dataset.ozzy.convert_q(dxi=dxi, n0=n0)
    assert sample_dataset["q"].attrs["units"] == expected_units
