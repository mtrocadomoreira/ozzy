from unittest.mock import patch

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
        pic_data_type="part",
        data_origin="ozzy",
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
        ds.ozzy.get_emittance(x_var="invalid_var")


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
            nbins=5, ene_var="alt_ene", w_var="alt_q"
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
            self.ds.ozzy.get_energy_spectrum(nbins=5, ene_var="nonexistent")

        with pytest.raises(
            KeyError, match="Cannot find 'nonexistent' variable in Dataset"
        ):
            self.ds.ozzy.get_energy_spectrum(nbins=5, w_var="nonexistent")

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


class TestGetWeightedMedian:
    @pytest.fixture
    def sample_dataset(self):
        """Create a simple particle dataset for testing."""
        rng = np.random.default_rng(seed=42)
        ds = oz.Dataset(
            {
                "energy": ("pid", rng.normal(100, 20, size=1000)),
                "q": ("pid", rng.random(1000)),
            },
            coords={"pid": np.arange(1000)},
            pic_data_type="part",
            data_origin="ozzy",
        )
        return ds

    @pytest.fixture
    def time_dependent_dataset(self):
        """Create a time-dependent particle dataset for testing."""
        rng = np.random.default_rng(seed=42)
        times = np.linspace(0, 10, 5)
        energies = np.zeros((5, 100))

        # Create time-dependent energies
        for i, t in enumerate(times):
            energies[i] = rng.normal(100 + t * 10, 20, size=100)

        ds = oz.Dataset(
            {
                "energy": (["t", "pid"], energies),
                "q": (["t", "pid"], rng.random((5, 100))),
            },
            coords={"t": times, "pid": np.arange(100)},
            pic_data_type="part",
            data_origin="ozzy",
        )
        return ds

    def test_get_weighted_median_basic(self, sample_dataset):
        """Test basic functionality of get_weighted_median."""
        # Mock the _contains_datavars method to avoid dependency issues
        with patch.object(sample_dataset.ozzy, "_contains_datavars"):
            median_energy = sample_dataset.ozzy.get_weighted_median(var="energy")

            # Check return type
            assert isinstance(median_energy, xr.DataArray)

            # Check the result is a scalar (no dimensions)
            assert len(median_energy.dims) == 0

            # Check value is reasonable (should be near 100 given our normal distribution)
            assert 80 <= float(median_energy) <= 120

    def test_get_weighted_median_time_dependent(self, time_dependent_dataset):
        """Test get_weighted_median with time-dependent data."""
        # Mock the _contains_datavars method
        with patch.object(time_dependent_dataset.ozzy, "_contains_datavars"):
            # Test with default time variable
            median_energy = time_dependent_dataset.ozzy.get_weighted_median(
                var="energy"
            )

            # Check return type and dimensions
            assert isinstance(median_energy, xr.DataArray)
            assert "t" in median_energy.dims
            assert len(median_energy.dims) == 1
            assert median_energy.sizes["t"] == 5

            # Values should increase with time since we added t*10 to the means
            assert np.all(np.diff(median_energy.values) > 0)

    def test_get_weighted_median_custom_weight(self, sample_dataset):
        """Test get_weighted_median with a custom weight variable."""
        # Add another weight variable
        sample_dataset["weight"] = ("pid", np.random.random(1000))

        # Mock the _contains_datavars method
        with patch.object(sample_dataset.ozzy, "_contains_datavars"):
            median_energy = sample_dataset.ozzy.get_weighted_median(
                var="energy", w_var="weight"
            )

            # Check return type
            assert isinstance(median_energy, xr.DataArray)

            # Result should be different from using default weights
            with patch.object(sample_dataset.ozzy, "_contains_datavars"):
                default_median = sample_dataset.ozzy.get_weighted_median(var="energy")
                # Not exactly equal due to floating point, but likely different
                assert abs(float(median_energy) - float(default_median)) > 1e-10

    def test_get_weighted_median_custom_time_var(self, time_dependent_dataset):
        """Test get_weighted_median with a custom time variable."""
        # Rename t to time
        renamed_ds = time_dependent_dataset.rename({"t": "time"})

        # Mock the _contains_datavars method
        with patch.object(renamed_ds.ozzy, "_contains_datavars"):
            median_energy = renamed_ds.ozzy.get_weighted_median(
                var="energy", t_var="time"
            )

            # Check return type and dimensions
            assert isinstance(median_energy, xr.DataArray)
            assert "time" in median_energy.dims
            assert len(median_energy.dims) == 1
            assert median_energy.sizes["time"] == 5

    def test_get_weighted_median_even_odd_observations(self):
        """Test get_weighted_median with even and odd numbers of observations."""
        # Create datasets with even and odd number of observations
        ds_even = oz.Dataset(
            {
                "energy": ("pid", [1, 2, 3, 4]),
                "q": ("pid", [1, 1, 1, 1]),  # Equal weights
            },
            coords={"pid": np.arange(4)},
            attrs={"pic_data_type": "part"},
        )

        ds_odd = oz.Dataset(
            {
                "energy": ("pid", [1, 2, 3, 4, 5]),
                "q": ("pid", [1, 1, 1, 1, 1]),  # Equal weights
            },
            coords={"pid": np.arange(5)},
            attrs={"pic_data_type": "part"},
        )

        # Mock the _contains_datavars method
        with patch.object(ds_even.ozzy, "_contains_datavars"):
            median_even = ds_even.ozzy.get_weighted_median(var="energy")
            # For even number with equal weights, should be average of middle values
            assert float(median_even) == 2.5

        with patch.object(ds_odd.ozzy, "_contains_datavars"):
            median_odd = ds_odd.ozzy.get_weighted_median(var="energy")
            # For odd number with equal weights, should be middle value
            assert float(median_odd) == 3

    def test_get_weighted_median_with_labels(self, sample_dataset):
        """Test the long_name attribute handling in get_weighted_median."""
        # Add long_name attribute to energy
        sample_dataset["energy"].attrs["long_name"] = "Energy"

        # Mock the _contains_datavars method
        with patch.object(sample_dataset.ozzy, "_contains_datavars"):
            median_energy = sample_dataset.ozzy.get_weighted_median(var="energy")
            assert median_energy.attrs["long_name"] == "med(Energy)"

        # Test with math notation
        sample_dataset["energy"].attrs["long_name"] = "$E$"

        with patch.object(sample_dataset.ozzy, "_contains_datavars"):
            median_energy = sample_dataset.ozzy.get_weighted_median(var="energy")
            assert median_energy.attrs["long_name"] == r"$\mathrm{med}\left(E\right) $"

    def test_get_weighted_median_missing_variables(self, sample_dataset):
        """Test error handling when variables are missing."""
        # The real _contains_datavars method should raise KeyError for missing variables
        with pytest.raises(Exception):  # Could be KeyError or custom exception
            sample_dataset.ozzy.get_weighted_median(var="nonexistent_var")

        with pytest.raises(Exception):
            sample_dataset.ozzy.get_weighted_median(
                var="energy", w_var="nonexistent_weight"
            )

    def test_get_weighted_median_with_negative_weights(self, sample_dataset):
        """Test that absolute values of weights are used."""
        # Add a weight variable with negative values
        sample_dataset["neg_weight"] = ("pid", -1 * sample_dataset["q"].values)

        # Mock the _contains_datavars method
        with patch.object(sample_dataset.ozzy, "_contains_datavars"):
            # Both should give the same result since abs() is used
            median_1 = sample_dataset.ozzy.get_weighted_median(var="energy", w_var="q")
            median_2 = sample_dataset.ozzy.get_weighted_median(
                var="energy", w_var="neg_weight"
            )

            # Should be exactly equal
            np.testing.assert_almost_equal(float(median_1), float(median_2))
