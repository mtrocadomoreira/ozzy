import numpy as np
import pytest
import xarray as xr
from ozzy.backends.osiris_backend import read


@pytest.fixture
def mock_h5py_file(mocker):
    mock_file = mocker.Mock()
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None
    mock_file.attrs = {"TYPE": b"grid"}
    mock_file["/SIMULATION"].attrs = {"ndims": 2, "nx": [10, 10]}
    mock_file["/AXIS/AXIS1"].attrs = {
        "LONG_NAME": "X",
        "UNITS": "c/w_p",
        "TYPE": "linear",
    }
    mock_file["/AXIS/AXIS2"].attrs = {
        "LONG_NAME": "Y",
        "UNITS": "c/w_p",
        "TYPE": "linear",
    }
    return mock_file


@pytest.fixture
def mock_xarray_dataset():
    data = np.random.rand(10, 10)
    return xr.Dataset(
        {"var": (["phony_dim_0", "phony_dim_1"], data)},
        attrs={
            "type": "grid",
            "move c": [0, 0],
            "xmin": [0, 0],
            "xmax": [1, 1],
            "nx": [10, 10],
            "label": "Test Variable",
            "units": "a.u.",
            "time": 0.0,
            "iter": 0,
            "time units": "1/w_p",
        },
    )


def test_read_grid_data(mocker):
    mock_h5py = mocker.patch("h5py.File")
    mock_h5py.return_value.__enter__.return_value.attrs = {"TYPE": b"grid"}

    mock_open_mfdataset = mocker.patch("xarray.open_mfdataset")
    mock_open_mfdataset.return_value = xr.Dataset(attrs={"type": "grid"})

    result = read(["test_file.h5"])

    assert result.attrs["pic_data_type"] == "grid"
    mock_open_mfdataset.assert_called_once()


def test_read_particle_data(mocker):
    mock_h5py = mocker.patch("h5py.File")
    mock_h5py.return_value.__enter__.return_value.attrs = {"TYPE": b"particles"}

    mock_open_mfdataset = mocker.patch("xarray.open_mfdataset")
    mock_open_mfdataset.return_value = xr.Dataset(attrs={"type": "particles"})

    result = read(["test_file.h5"])

    assert result.attrs["pic_data_type"] == "part"
    mock_open_mfdataset.assert_called_once()


def test_read_unsupported_data_type(mocker):
    mock_h5py = mocker.patch("h5py.File")
    mock_h5py.return_value.__enter__.return_value.attrs = {"TYPE": b"unsupported"}

    mock_open_mfdataset = mocker.patch("xarray.open_mfdataset")
    mock_open_mfdataset.return_value = xr.Dataset(attrs={"type": "unsupported"})

    with pytest.raises(ValueError, match="Unrecognized OSIRIS data type"):
        read(["test_file.h5"])
