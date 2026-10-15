import pytest
import xarray as xr

from ozzy.backend_interface import Backend


@pytest.fixture
def mock_backend():
    return Backend("ozzy")


@pytest.fixture
def mock_backend_osiris():
    return Backend("osiris")


def test_backend_initialization():
    backend = Backend("ozzy")
    assert backend.name == "ozzy"
    assert callable(backend.parse)
    assert hasattr(backend, "mixin")


def test_backend_initialization_invalid():
    with pytest.raises(ValueError):
        Backend("invalid_backend")


@pytest.mark.parametrize("file_type", ["osiris", "lcode", "ozzy"])
def test_backend_initialization_valid(file_type):
    backend = Backend(file_type)
    assert backend.name == file_type
    assert callable(backend.parse)
    assert hasattr(backend, "mixin")


def test_parse_data(mock_backend, tmp_path):
    file_path = tmp_path / "test_file.h5"
    file_path.touch()

    mock_backend.parse = lambda files, *args, **kwargs: xr.Dataset(
        attrs={"test_attr": "test_value"}
    )

    result = mock_backend.parse_data([str(file_path)])

    assert isinstance(result, xr.Dataset)
    assert result.attrs["file_backend"] == "ozzy"
    assert result.attrs["source"] == str(tmp_path / "test_file.h5")
    assert result.attrs["file_prefix"] == "test_file.h5"
    assert result.attrs["data_origin"] == "ozzy"
    assert result.attrs["test_attr"] == "test_value"


def test_parse_data_empty_files(mock_backend):
    result = mock_backend.parse_data([])
    assert isinstance(result, xr.Dataset)
    assert "file_backend" not in result.attrs


def test_parse_data_multiple_files(mock_backend, tmp_path):
    file1 = tmp_path / "file1.h5"
    file2 = tmp_path / "file2.h5"
    file1.touch()
    file2.touch()

    mock_backend.parse = lambda files, *args, **kwargs: xr.Dataset()

    result = mock_backend.parse_data([str(file1), str(file2)])

    assert isinstance(result, xr.Dataset)
    assert result.attrs["file_backend"] == "ozzy"
    assert result.attrs["source"] == str(tmp_path)
    assert result.attrs["file_prefix"] == "file"
    assert result.attrs["data_origin"] == "ozzy"
