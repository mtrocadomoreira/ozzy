import numpy as np
import pandas as pd
import pytest
import xarray as xr
from hypothesis import given
from hypothesis import strategies as st

from ozzy.core import (
    DataArray,
    Dataset,
    available_backends,
    open,
    open_compare,
    open_series,
)


def test_dataset_creation():
    ds = Dataset(pic_data_type="grid", data_origin="ozzy")
    assert isinstance(ds, xr.Dataset)
    assert ds.attrs["pic_data_type"] == "grid"
    assert ds.attrs["data_origin"] == "ozzy"


def test_dataarray_creation():
    da = DataArray(
        np.random.rand(5, 5),
        dims=["x", "y"],
        pic_data_type="part",
        data_origin="osiris",
    )
    assert isinstance(da, xr.DataArray)
    assert da.attrs["pic_data_type"] == "part"
    assert da.attrs["data_origin"] == "osiris"


def test_available_backends():
    backends = available_backends()
    assert isinstance(backends, list)
    assert all(isinstance(b, str) for b in backends)
    assert set(backends).issubset({"osiris", "lcode", "ozzy"})


@given(st.sampled_from(["ozzy", "osiris", "lcode"]))
def test_open_with_invalid_path(file_type):
    with pytest.raises(FileNotFoundError):
        open(file_type, "non_existent_file.h5")


def test_open_series_with_empty_list():
    with pytest.raises(FileNotFoundError):
        open_series("ozzy", [])


def test_open_compare_with_invalid_file_type():
    with pytest.raises(ValueError):
        open_compare("invalid_type", path=".")


def test_open_compare_empty_result():
    df = open_compare("ozzy")
    assert isinstance(df, pd.DataFrame)
    assert df.empty


@given(st.lists(st.sampled_from(["ozzy", "osiris", "lcode"]), min_size=1, max_size=3))
def test_open_compare_multiple_file_types(file_types):
    df = open_compare(file_types, path=".", runs="*", quants="*")
    assert isinstance(df, pd.DataFrame)
    assert set(df.columns).issubset(set(["charge-electrons", "ez"]))


def test_dataset_with_data():
    data = np.random.rand(10, 10)
    coords = {"x": np.arange(10), "y": np.arange(10)}
    ds = Dataset(
        {"var": (["x", "y"], data)},
        coords=coords,
        pic_data_type="grid",
        data_origin="ozzy",
    )
    assert isinstance(ds, xr.Dataset)
    assert "var" in ds.data_vars
    assert ds.attrs["pic_data_type"] == "grid"
    assert ds.attrs["data_origin"] == "ozzy"


def test_dataarray_with_data():
    data = np.random.rand(10, 10)
    coords = {"x": np.arange(10), "y": np.arange(10)}
    da = DataArray(
        data, coords=coords, dims=["x", "y"], pic_data_type="part", data_origin="lcode"
    )
    assert isinstance(da, xr.DataArray)
    assert da.shape == (10, 10)
    assert da.attrs["pic_data_type"] == "part"
    assert da.attrs["data_origin"] == "lcode"


def test_open_series_with_nfiles():
    with pytest.raises(FileNotFoundError):
        open_series("ozzy", "dummy_*.h5", nfiles=3)


def test_open_compare_with_specific_runs_and_quants():
    df = open_compare("ozzy", path=".", runs=["run1", "run2"], quants=["e1", "e2"])
    assert isinstance(df, pd.DataFrame)
    assert set(df.index).issubset({"run1", "run2"})
    assert set(df.columns).issubset({"e1", "e2"})
