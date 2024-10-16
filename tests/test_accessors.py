import numpy as np
import xarray as xr
from hypothesis import given
from hypothesis import strategies as st
from ozzy.accessors import _fft


@given(
    x_size=st.integers(min_value=2, max_value=100),
    y_size=st.integers(min_value=2, max_value=100),
)
def test_fft_shape(x_size, y_size):
    da = xr.DataArray(
        np.random.rand(x_size, y_size),
        dims=["x", "y"],
        coords={"x": np.arange(x_size), "y": np.arange(y_size)},
    )
    result = _fft(da, dims=["x", "y"])
    assert result.shape == da.shape


def test_fft_coordinate_assignment():
    da = xr.DataArray(
        np.random.rand(10, 10),
        dims=["x", "y"],
        coords={"x": np.arange(10), "y": np.arange(10)},
    )
    result = _fft(da, dims=["x", "y"])
    assert "x" in result.coords
    assert "y" in result.coords


def test_fft_metadata_update():
    da = xr.DataArray(
        np.random.rand(10, 10),
        dims=["x", "y"],
        coords=[
            ("x", np.arange(10), {"long_name": r"$X$", "units": r"$\mathrm{m}$"}),
            ("y", np.arange(10), {"long_name": r"$Y$", "units": r"$\mathrm{s}$"}),
        ],
        attrs={
            "long_name": r"$L$",
            "units": r"$k_p^{-1}$",
        },
    )
    result = _fft(da, dims=["x", "y"])
    assert result.coords["x"].attrs["long_name"] == r"$k(X)$"
    assert result.coords["x"].attrs["units"] == r"$\left(\mathrm{m}\right)^{-1}$"
    assert result.coords["y"].attrs["long_name"] == r"$k(Y)$"
    assert result.coords["y"].attrs["units"] == r"$\left(\mathrm{s}\right)^{-1}$"


def test_fft_missing_dimension():
    da = xr.DataArray(
        np.random.rand(10, 10),
        dims=["x", "y"],
        coords={"x": np.arange(10), "y": np.arange(10)},
    )
    try:
        _fft(da, dims=["x", "z"])
    except ValueError as e:
        assert "not found in array dimensions" in str(e)


@given(st.integers(min_value=2, max_value=100))
def test_fft_output_type(size):
    da = xr.DataArray(
        np.random.rand(size, size),
        dims=["x", "y"],
        coords={"x": np.arange(size), "y": np.arange(size)},
    )
    result = _fft(da, dims=["x", "y"])
    assert isinstance(result, xr.DataArray)
    assert result.dtype == np.float64
