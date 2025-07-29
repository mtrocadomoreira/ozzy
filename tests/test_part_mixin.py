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
            "p3": ("pid", np.random.rand(1000)),
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
    assert len(result.x1) == 20


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


class TestGetEnergySpectrum:
    def setup_method(self):
        """Set up test data for each test method"""
        # Create a simple particle dataset with known values
        rng = np.random.default_rng(42)  # Fixed seed for reproducibility
        self.ene_values = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 3.0, 2.0, 1.0, 5.0, 4.0])
        self.q_values = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

        self.ds = oz.Dataset(
            {
                "ene": ("pid", self.ene_values),
                "q": ("pid", self.q_values),
                "alt_ene": ("pid", self.ene_values * 10),  # Alternative energy variable
                "alt_q": ("pid", -self.q_values),  # Negative charge for testing abs()
            },
            coords={"pid": np.arange(10)},
            attrs={"pic_data_type": "part"},
        )

        # Create a custom energy axis
        self.energy_axis = np.array([0.5, 1.5, 2.5, 3.5, 4.5, 5.5])
        self.axis_ds = oz.Dataset(
            coords={"ene": self.energy_axis}, attrs={"pic_data_type": "grid"}
        )
        self.axis_ds["ene"].attrs["long_name"] = "Energy"
        self.axis_ds["ene"].attrs["units"] = "eV"

    def test_basic_functionality_with_nbins(self):
        """Test basic functionality using nbins parameter"""
        spectrum = self.ds.ozzy.get_energy_spectrum(nbins=5)

        # Check return type
        assert isinstance(spectrum, xr.Dataset)

        # Check returned variables
        assert "q" in spectrum
        assert "counts" in spectrum
        assert "ene" in spectrum

        # Check that we have the right number of bins
        assert len(spectrum["ene"]) == 5

        # Check that the counts sum to the total number of particles
        assert spectrum["counts"].sum() == len(self.ene_values)

        # Check that the charge sum is correct (should be sum of all charges)
        np.testing.assert_allclose(spectrum["q"].sum(), np.sum(self.q_values))

    def test_with_axis_ds(self):
        """Test using a custom energy axis"""
        spectrum = self.ds.ozzy.get_energy_spectrum(axis_ds=self.axis_ds)

        # Check that we have the right number of bins
        assert len(spectrum["ene"]) == len(self.energy_axis)

        # Check that bins are properly centered
        expected_centers = self.energy_axis
        np.testing.assert_allclose(spectrum["ene"].values, expected_centers)

        # Check that attributes are transferred
        assert spectrum["ene"].attrs["long_name"] == "Energy"
        assert spectrum["ene"].attrs["units"] == "eV"

    def test_custom_variable_names(self):
        """Test using custom variable names for energy and charge"""
        spectrum = self.ds.ozzy.get_energy_spectrum(
            nbins=5, enevar="alt_ene", wvar="alt_q"
        )

        # Check that the correct variables are used
        assert "alt_q" in spectrum

    def test_error_when_no_axis_or_nbins(self):
        """Test error is raised when neither axis_ds nor nbins is provided"""
        with pytest.raises(
            ValueError, match="Either axis_ds or nbins must be provided"
        ):
            self.ds.ozzy.get_energy_spectrum(axis_ds=None, nbins=None)

    def test_error_when_variable_not_found(self):
        """Test error is raised when requested variable doesn't exist"""
        with pytest.raises(
            KeyError, match="Cannot find 'nonexistent' variable in Dataset"
        ):
            self.ds.ozzy.get_energy_spectrum(nbins=5, enevar="nonexistent")

        with pytest.raises(
            KeyError, match="Cannot find 'nonexistent' variable in Dataset"
        ):
            self.ds.ozzy.get_energy_spectrum(nbins=5, wvar="nonexistent")

    def test_error_when_enevar_not_in_axis_ds(self):
        """Test error when energy variable is not in provided axis_ds"""
        # Create axis dataset with different variable name
        wrong_axis_ds = oz.Dataset(
            coords={"wrong_name": self.energy_axis}, attrs={"pic_data_type": "grid"}
        )

        with pytest.raises(
            KeyError, match="Cannot find 'ene' variable in provided axis_ds"
        ):
            self.ds.ozzy.get_energy_spectrum(axis_ds=wrong_axis_ds)

    def test_label_modification(self):
        """Test that labels are properly modified with |...|"""
        # Add a long_name attribute to the q variable
        self.ds["q"].attrs["long_name"] = "Charge"

        spectrum1 = self.ds.ozzy.get_energy_spectrum(nbins=5)

        self.ds["q"].attrs["long_name"] = "$Q$"

        spectrum2 = self.ds.ozzy.get_energy_spectrum(nbins=5)

        # Check that the label has been modified with | |
        assert spectrum1["q"].attrs["long_name"] == "|Charge|"
        assert spectrum2["q"].attrs["long_name"] == "$|Q|$"
