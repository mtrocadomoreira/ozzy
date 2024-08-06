import numpy as np
import pytest
import xarray as xr
from hypothesis import given
from hypothesis import strategies as st
from ozzy.new_dataobj import new_dataarray, new_dataset


@pytest.mark.parametrize(
    "pic_data_type,data_origin",
    [
        ("grid", "ozzy"),
        ("part", "osiris"),
        (["grid", "part"], ["ozzy", "osiris"]),
        (None, None),
    ],
)
def test_new_dataset_attributes(pic_data_type, data_origin):
    ds = new_dataset(pic_data_type=pic_data_type, data_origin=data_origin)
    assert isinstance(ds, xr.Dataset)
    assert ds.attrs.get("pic_data_type") == pic_data_type
    assert ds.attrs.get("data_origin") == data_origin


def test_new_dataset_with_existing_dataset():
    existing_ds = xr.Dataset(attrs={"existing_attr": "value"})
    ds = new_dataset(existing_ds, pic_data_type="grid", data_origin="ozzy")
    assert ds.attrs.get("existing_attr") == "value"
    assert ds.attrs.get("pic_data_type") == "grid"
    assert ds.attrs.get("data_origin") == "ozzy"


def test_new_dataset_remove_attributes_from_variables():
    data = {"var1": ("x", [1, 2, 3]), "var2": ("y", [4, 5, 6])}
    attrs = {"pic_data_type": "grid", "data_origin": "ozzy"}
    ds = new_dataset(data, attrs=attrs)
    for var in ds.data_vars:
        assert "pic_data_type" not in ds[var].attrs
        assert "data_origin" not in ds[var].attrs


@given(
    pic_data_type=st.sampled_from(["grid", "part", None]),
    data_origin=st.sampled_from(["ozzy", "osiris", "lcode", None]),
)
def test_new_dataarray_attributes(pic_data_type, data_origin):
    da = new_dataarray(
        np.random.rand(5, 5),
        dims=["x", "y"],
        pic_data_type=pic_data_type,
        data_origin=data_origin,
    )
    assert isinstance(da, xr.DataArray)
    assert da.attrs.get("pic_data_type") == pic_data_type
    assert da.attrs.get("data_origin") == data_origin


def test_new_dataarray_with_existing_dataarray():
    existing_da = xr.DataArray(
        np.random.rand(5, 5), dims=["x", "y"], attrs={"existing_attr": "value"}
    )
    da = new_dataarray(existing_da, pic_data_type="part", data_origin="lcode")
    assert da.attrs.get("existing_attr") == "value"
    assert da.attrs.get("pic_data_type") == "part"
    assert da.attrs.get("data_origin") == "lcode"


def test_new_dataset_with_data_variables():
    data = {
        "temp": (["x", "y"], np.random.rand(3, 3)),
        "pressure": (["x", "y"], np.random.rand(3, 3)),
    }
    coords = {"x": [1, 2, 3], "y": [4, 5, 6]}
    ds = new_dataset(data, coords=coords, pic_data_type="grid", data_origin="ozzy")
    assert "temp" in ds.data_vars
    assert "pressure" in ds.data_vars
    assert ds.sizes == {"x": 3, "y": 3}


def test_new_dataarray_with_coordinates():
    data = np.random.rand(4, 5)
    coords = {"x": [1, 2, 3, 4], "y": [5, 6, 7, 8, 9]}
    da = new_dataarray(
        data, coords=coords, dims=["x", "y"], pic_data_type="part", data_origin="osiris"
    )
    assert da.shape == (4, 5)
    assert list(da.coords) == ["x", "y"]
    assert list(da.x.values) == [1, 2, 3, 4]
    assert list(da.y.values) == [5, 6, 7, 8, 9]
