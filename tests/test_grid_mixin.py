import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from ozzy.core import DataArray, Dataset


@pytest.fixture
def grid_data():
    return DataArray(np.zeros((4, 3)), dims=["x", "y"], pic_data_type="grid")


def test_coords_from_extent(grid_data):
    mapping = {"x": (0, 1), "y": (-1, 2)}
    result = grid_data.ozzy.coords_from_extent(mapping)
    assert "x" in result.coords
    assert "y" in result.coords


@given(
    x_size=st.integers(min_value=2, max_value=100),
    y_size=st.integers(min_value=2, max_value=100),
)
def test_coords_from_extent_property(x_size, y_size):
    data = DataArray(np.zeros((x_size, y_size)), dims=["x", "y"], pic_data_type="grid")
    mapping = {"x": (-1, 1), "y": (0, 5)}
    result = data.ozzy.coords_from_extent(mapping)
    assert result.sizes["x"] == x_size
    assert result.sizes["y"] == y_size


def test_get_space_dims():
    ds = Dataset(
        {"var": (["t", "x", "y"], np.random.rand(5, 10, 10))}, pic_data_type="grid"
    )
    space_dims = ds.ozzy.get_space_dims("t")
    assert set(space_dims) == {"x", "y"}


def test_get_space_dims_custom_time():
    ds = Dataset(
        {"var": (["time", "x", "y"], np.random.rand(5, 10, 10))}, pic_data_type="grid"
    )
    space_dims = ds.ozzy.get_space_dims("time")
    assert set(space_dims) == {"x", "y"}


def test_get_bin_edges():
    ds = Dataset(
        {"var": (["t", "x", "y"], np.random.rand(5, 10, 10))},
        coords={
            "t": np.arange(5),
            "x": np.linspace(0, 1, 10),
            "y": np.linspace(-1, 1, 10),
        },
        pic_data_type="grid",
    )
    bin_edges = ds.ozzy.get_bin_edges("t")
    assert len(bin_edges) == 2
    assert len(bin_edges[0]) == 11  # x-axis
    assert len(bin_edges[1]) == 11  # y-axis


@pytest.mark.parametrize("time_dim", ["t", "time", "T"])
def test_get_bin_edges_different_time_dims(time_dim):
    ds = Dataset(
        {"var": ([time_dim, "x", "y"], np.random.rand(5, 10, 10))},
        coords={
            time_dim: np.arange(5),
            "x": np.linspace(0, 1, 10),
            "y": np.linspace(-1, 1, 10),
        },
        pic_data_type="grid",
    )
    bin_edges = ds.ozzy.get_bin_edges(time_dim)
    assert len(bin_edges) == 2
    assert all(len(edge) == 11 for edge in bin_edges)


def test_coords_from_extent_invalid_dim():
    da = DataArray(np.zeros((4, 3)), dims=["x", "y"], pic_data_type="grid")
    mapping = {"x": (0, 1), "z": (-1, 2)}
    with pytest.raises(KeyError):
        da.ozzy.coords_from_extent(mapping)


def test_get_space_dims_no_time_dim():
    ds = Dataset({"var": (["x", "y"], np.random.rand(10, 10))}, pic_data_type="grid")
    space_dims = ds.ozzy.get_space_dims("t")
    assert set(space_dims) == {"x", "y"}


def test_get_bin_edges_single_dim():
    ds = Dataset(
        {"var": (["x"], np.random.rand(10))},
        coords={"x": np.linspace(0, 1, 10)},
        pic_data_type="grid",
    )
    bin_edges = ds.ozzy.get_bin_edges()
    assert len(bin_edges) == 1
    assert len(bin_edges[0]) == 11
