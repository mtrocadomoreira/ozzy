import numpy as np
import pytest
import xarray as xr
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import ozzy.core as oz


@pytest.fixture
def sample_dataset():
    return oz.Dataset(
        {
            "x1": ("pid", np.random.rand(1000), {"long_name": "$x_1$"}),
            "x2": ("pid", np.random.rand(1000), {"long_name": "$x_2$"}),
            "p1": ("pid", np.random.rand(1000)),
            "p2": ("pid", np.random.rand(1000)),
            "q": ("pid", np.ones(1000)),
        },
        coords={"pid": np.arange(1000)},
        attrs={"pic_data_type": "part", "data_origin": "ozzy"},
    )


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


@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,), deadline=None)
@given(st.integers(min_value=50, max_value=500))
def test_get_phase_space(sample_dataset, nbins):
    ds = sample_dataset
    result = ds.ozzy.get_phase_space(["p2", "x2"], nbins=nbins)

    assert isinstance(result, xr.Dataset)
    assert "rho" in result.data_vars
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


def test_get_emittance_basic(sample_dataset):
    ds = sample_dataset
    result = ds.ozzy.get_emittance()
    assert isinstance(result, xr.Dataset)
    assert "emit_norm" in result.data_vars
    assert "counts" in result.data_vars
    assert result.attrs["pic_data_type"] == "grid"


def test_get_emittance_geometric(sample_dataset):
    ds = sample_dataset
    result = ds.ozzy.get_emittance(norm_emit=False)
    assert "emit" in result.data_vars
    assert "emit_norm" not in result.data_vars


def test_get_emittance_axisym(sample_dataset):
    ds = sample_dataset
    result = ds.ozzy.get_emittance(axisym=True)
    result_normal = ds.ozzy.get_emittance(axisym=False)
    assert (result.emit_norm == 4 * result_normal.emit_norm).all()


def test_get_emittance_invalid_var(sample_dataset):
    ds = sample_dataset
    with pytest.raises(KeyError, match="Cannot find 'invalid_var' variable in Dataset"):
        ds.ozzy.get_emittance(xvar="invalid_var")


def test_get_slice_emittance_basic(sample_dataset):
    ds = sample_dataset
    axis_ds = xr.Dataset(
        coords={"x1": np.linspace(0, 1, 10)}, attrs={"pic_data_type": "grid"}
    )
    result = ds.ozzy.get_slice_emittance(axis_ds=axis_ds, slice_var="x1")
    assert isinstance(result, xr.Dataset)
    assert "slice_emit_norm" in result.data_vars
    assert "counts" in result.data_vars


def test_get_slice_emittance_nbins(sample_dataset):
    ds = sample_dataset
    result = ds.ozzy.get_slice_emittance(nbins=20, slice_var="x1")
    assert len(result.x1_bins) == 20


def test_get_slice_emittance_min_count(sample_dataset):
    ds = sample_dataset
    result = ds.ozzy.get_slice_emittance(nbins=10, min_count=50, slice_var="x1")
    assert not np.any(result.counts < 50)


def test_get_slice_emittance_missing_params(sample_dataset):
    ds = sample_dataset
    with pytest.raises(ValueError, match="Either axis_ds or nbins must be provided"):
        ds.ozzy.get_slice_emittance(slice_var="x1")


def test_get_slice_emittance_invalid_axis(sample_dataset):
    ds = sample_dataset
    axis_ds = xr.Dataset(
        coords={"wrong_var": np.linspace(0, 1, 10)}, attrs={"pic_data_type": "grid"}
    )
    with pytest.raises(KeyError):
        ds.ozzy.get_slice_emittance(axis_ds=axis_ds, slice_var="x1")


def test_get_slice_emittance_geometric(sample_dataset):
    ds = sample_dataset
    result = ds.ozzy.get_slice_emittance(nbins=10, norm_emit=False, slice_var="x1")
    assert "slice_emit" in result.data_vars
    assert "slice_emit_norm" not in result.data_vars
