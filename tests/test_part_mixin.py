import numpy as np
import ozzy.core as oz
import pytest
import xarray as xr
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


@pytest.fixture
def sample_dataset():
    return oz.Dataset(
        {
            "x1": ("pid", np.random.rand(1000)),
            "x2": ("pid", np.random.rand(1000)),
            "p1": ("pid", np.random.rand(1000)),
            "p2": ("pid", np.random.rand(1000)),
            "q": ("pid", np.ones(1000)),
        },
        coords={"pid": np.arange(1000)},
        attrs={"pic_data_type": "part", "data_origin": "ozzy"},
    )

    # class TestPartMixin:
    #     @pytest.fixture
    #     def sample_dataset(self):
    #         return oz.Dataset(
    #             {
    #                 "x1": ("pid", np.random.rand(1000)),
    #                 "x2": ("pid", np.random.rand(1000)),
    #                 "p1": ("pid", np.random.rand(1000)),
    #                 "p2": ("pid", np.random.rand(1000)),
    #                 "q": ("pid", np.ones(1000)),
    #             },
    #             coords={"pid": np.arange(1000)},
    #             attrs={"pic_data_type": "part", "data_origin": "ozzy"},
    #         )


def test_sample_particles(sample_dataset):
    ds = sample_dataset
    result = ds.ozzy.sample_particles(500)
    assert len(result.pid) == 500
    assert set(result.data_vars) == set(sample_dataset.data_vars)


def test_sample_particles_more_than_available(sample_dataset):
    ds = sample_dataset
    result = ds.ozzy.sample_particles(2000)
    assert len(result.pid) == 1000


@pytest.mark.parametrize("vars", [["x2"], ["x2", "p2"]])
def test_mean_std(sample_dataset, vars):
    ds = sample_dataset
    axes_ds = xr.Dataset(
        coords={"x1": np.linspace(0, 1, 21)}, attrs={"pic_data_type": "grid"}
    )
    result = ds.ozzy.mean_std(vars, axes_ds)

    assert isinstance(result, xr.Dataset)
    assert result.attrs["pic_data_type"] == "grid"
    for var in vars:
        assert f"{var}_mean" in result.data_vars
        assert f"{var}_std" in result.data_vars


def test_mean_std_invalid_axes(sample_dataset):
    ds = sample_dataset
    invalid_axes = xr.Dataset(
        coords={"x1": np.linspace(0, 1, 21)}, attrs={"pic_data_type": "invalid"}
    )
    with pytest.raises(ValueError, match="axes_ds must be grid data"):
        ds.ozzy.mean_std(["x2"], invalid_axes)


@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,), deadline=500)
@given(st.integers(min_value=50, max_value=500))
def test_get_phase_space(sample_dataset, nbins):
    ds = sample_dataset
    result = ds.ozzy.get_phase_space(["p2", "x2"], nbins=nbins)

    assert isinstance(result, xr.Dataset)
    assert "Q" in result.data_vars
    assert set(result.coords) == {"p2", "x2"}
    assert result.p2.size == nbins
    assert result.x2.size == nbins


def test_get_phase_space_custom_extents(sample_dataset):
    ds = sample_dataset
    extents = {"p2": (-1, 1), "x2": (0, 2)}
    result = ds.ozzy.get_phase_space(["p2", "x2"], extents=extents, nbins=100)

    assert result.p2.min() >= -1 and result.p2.max() <= 1
    assert result.x2.min() >= 0 and result.x2.max() <= 2


def test_get_phase_space_custom_nbins(sample_dataset):
    ds = sample_dataset
    nbins = {"p2": 50, "x2": 75}
    result = ds.ozzy.get_phase_space(["p2", "x2"], nbins=nbins)

    assert result.p2.size == 50
    assert result.x2.size == 75
