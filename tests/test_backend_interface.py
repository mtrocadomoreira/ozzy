import pytest
import xarray as xr
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

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


def test_find_quants(mock_backend_osiris, tmp_path):
    run1 = tmp_path / "run1"
    run1.mkdir(exist_ok=True)
    (run1 / "e1-000001.h5").touch()
    (run1 / "e2-000001.h5").touch()

    dirs_runs = {"run1": str(run1)}
    result = mock_backend_osiris.find_quants(
        str(tmp_path), dirs_runs, quants=["e1", "e2"]
    )

    assert "e1" in result
    assert "e2" in result
    assert len(result["e1"]) == 1
    assert len(result["e2"]) == 1


def test_find_quants_no_quants(mock_backend_osiris, tmp_path):
    run1 = tmp_path / "run1"
    run1.mkdir(exist_ok=True)
    (run1 / "e1-000001.h5").touch()
    (run1 / "e2-000001.h5").touch()

    dirs_runs = {"run1": str(run1)}
    result = mock_backend_osiris.find_quants(str(tmp_path), dirs_runs)

    assert "e1" in result
    assert "e2" in result


@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,))
@given(st.lists(st.sampled_from(["e1", "e2", "b1", "b2"]), min_size=1, max_size=4))
def test_find_quants_hypothesis(mock_backend_osiris, tmp_path, quants):
    run1 = tmp_path / "run1"
    run1.mkdir(exist_ok=True)
    for q in quants:
        (run1 / f"{q}-000001.h5").touch()

    dirs_runs = {"run1": str(run1)}
    result = mock_backend_osiris.find_quants(str(tmp_path), dirs_runs, quants=quants)

    assert set(result.keys()) == set(quants)
    assert all(len(result[q]) == 1 for q in quants)


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
