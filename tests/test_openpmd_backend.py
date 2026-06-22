from types import SimpleNamespace

import h5py
import numpy as np
import pytest
import xarray as xr

from ozzy.backends import openpmd_backend as opb


def test_backend_constants_match_openpmd_file_contract():
    assert opb.general_file_endings == ["h5", "bp"]
    assert opb.quants_ignore is None
    assert opb.re.fullmatch(opb.general_regex_pattern, "fields000001.h5")
    assert opb.re.fullmatch(opb.general_regex_pattern, "rho00000042.bp")
    assert opb.re.fullmatch(opb.general_regex_pattern, "rho000042.txt") is None


@pytest.mark.parametrize(
    "record,component,mode,include_mode,expected",
    [
        ("ux", None, None, False, r"$p_x$"),
        ("rho_electrons", None, None, False, r"$\\rho_\\mathrm{electrons}$"),
        ("ExmBy", None, None, False, r"$E_x-B_y$"),
        ("E", "t", 1, True, r"$E_{\vartheta,m=1}$"),
        ("rho", "", 2, True, r"$\rho_{m=2}$"),
    ],
)
def test_get_tex_label_formats_openpmd_and_hipace_names(
    record, component, mode, include_mode, expected
):
    assert opb.get_tex_label(record, component, mode, include_mode) == expected


def test_exponents_to_unit_rejects_wrong_number_of_dimensions():
    with pytest.raises(ValueError, match="seven exponents"):
        opb._exponents_to_unit([1.0, 0.0])


def test_get_tex_units_uses_si_derived_units():
    factor, units = opb.get_tex_units([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0], 1.0)

    assert factor == 1
    assert units == r"$\mathrm{C}$"


def test_set_sensible_units_compacts_data_and_sets_tex_unit_label():
    da = xr.DataArray(np.array([0.0, 2000.0]), dims="x")

    result = opb.set_sensible_units(da, unit_init="m")

    np.testing.assert_allclose(result.values, [0.0, 2.0])
    assert result.attrs["units"] == r"$\mathrm{km}$"


def test_set_sensible_units_returns_original_array_without_unit_info(capsys):
    da = xr.DataArray(np.array([1.0, 2.0]), dims="x")

    result = opb.set_sensible_units(da)

    assert result is da
    assert result.attrs == {}
    assert "Did not receive any unit information" in capsys.readouterr().out


def test_openpmd_concat_time_sorts_and_outer_joins_time_coordinates():
    later = xr.Dataset(
        {"q": (["t", "x"], [[2.0, 3.0]])},
        coords={"t": [2.0], "x": [0.0, 1.0]},
        attrs={"shared": "later", "conflicting": "drop"},
    )
    earlier = xr.Dataset(
        {"q": (["t", "x"], [[1.0]])},
        coords={"t": [1.0], "x": [0.0]},
        attrs={"shared": "later", "conflicting": "different"},
    )

    result = opb.openpmd_concat_time([later, earlier])

    np.testing.assert_allclose(result["t"].values, [1.0, 2.0])
    np.testing.assert_allclose(result["x"].values, [0.0, 1.0])
    np.testing.assert_allclose(result["q"].sel(t=1.0).values, [1.0, np.nan])
    assert result.attrs == {"shared": "later"}


class FakeFieldMetadata:
    axes = ["z", "x"]
    z = np.array([0.0, 1.0])
    x = np.array([0.0, 2.0, 4.0])
    component_attrs = {"unitSI": 2.0}
    field_attrs = {
        "timeOffset": 0.0,
        "unitDimension": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "gridUnitSIPerDimension": [1.0, 0.5],
    }


class FakeFieldOpenPMDTimeSeries:
    avail_fields = ["E"]
    iterations = np.array([1, 2])
    t = np.array([0.0, 1.0])
    fields_metadata = {
        "E": {
            "avail_components": ["x"],
            "geometry": "thetaMode",
            "avail_circ_modes": ["all", "0", "1"],
            "type": "field",
            "geometryParameters": "m=0,1",
            "fieldSmoothing": "none",
            "gridGlobalOffset": [0.0, 0.0],
        }
    }

    def __init__(self):
        self.calls = []

    def get_field(self, record, coord, iteration, m):
        self.calls.append((record, coord, iteration, m))
        mode_offset = 10 * int(m) if m != "all" else 0
        data = np.full((2, 3), iteration + mode_offset, dtype=float)
        return data, FakeFieldMetadata()


def test_read_fields_preserves_modes_axes_scaling_and_ozzy_metadata():
    op_obj = FakeFieldOpenPMDTimeSeries()

    result = opb.read_fields(op_obj, ["E"], separate_theta_modes=True)

    assert result.attrs["pic_data_type"] == "grid"
    assert result.attrs["data_origin"] == "openpmd"
    assert set(result.data_vars) == {"Ex_m0", "Ex_m1"}
    assert set(op_obj.calls) == {
        ("E", "x", 1, 0),
        ("E", "x", 2, 0),
        ("E", "x", 1, 1),
        ("E", "x", 2, 1),
    }
    np.testing.assert_allclose(result["x"].values, [0.0, 1.0, 2.0])
    np.testing.assert_allclose(result["z"].values, [0.0, 1.0])
    np.testing.assert_allclose(result["Ex_m0"].sel(t=0.0).compute().values, 2.0)
    np.testing.assert_allclose(result["Ex_m1"].sel(t=1.0).compute().values, 24.0)
    assert result["Ex_m1"].attrs["theta_mode"] == 1
    assert result["Ex_m1"].attrs["long_name"] == r"$E_{x,m=1}$"
    assert result["iter"].attrs["long_name"] == "Iteration"
    np.testing.assert_array_equal(result["iter"].values, [1, 2])


class FakeParticleOpenPMDTimeSeries:
    iterations = np.array([5, 6])
    t = np.array([0.0, 1.0])
    avail_record_components = {
        "electrons": ["x", "ux", "w", "charge", "mass"],
    }

    def get_particle(self, quantities, iteration):
        assert quantities == self.avail_record_components["electrons"]
        return [
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),
            np.array([10.0, 20.0, 30.0]),
            np.array([-1.0, -1.0, -1.0]),
            np.array([1.0, 1.0, 1.0]),
        ]


def _particle_attrs():
    dimensionless = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    return {
        "x": {
            "macroWeighted": 0,
            "weightingPower": 1,
            "unitSI": 0.5,
            "unitDimension": np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        },
        "ux": {
            "macroWeighted": 0,
            "weightingPower": 99,
            "unitSI": 2.0,
            "unitDimension": np.array([1.0, 1.0, -1.0, 0.0, 0.0, 0.0, 0.0]),
        },
        "w": {
            "macroWeighted": 0,
            "weightingPower": 0,
            "unitSI": 1.0,
            "unitDimension": dimensionless,
        },
        "charge": {
            "macroWeighted": 1,
            "weightingPower": 0,
            "unitSI": 1.0,
            "unitDimension": np.array([0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0]),
        },
        "mass": {
            "macroWeighted": 1,
            "weightingPower": 0,
            "unitSI": 1.0,
            "value": 1.0,
            "unitDimension": np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        },
        "electrons": {"species_name": "electrons"},
    }


def test_read_species_applies_weighting_units_and_particle_metadata():
    result = opb.read_species(
        FakeParticleOpenPMDTimeSeries(), "electrons", _particle_attrs()
    )

    assert result.attrs["pic_data_type"] == "part"
    assert result.attrs["data_origin"] == "openpmd"
    assert result.attrs["species_name"] == "electrons"
    assert result.attrs["unique_pids"] is False
    np.testing.assert_array_equal(result["pid"].values, [0, 1, 2])
    np.testing.assert_array_equal(result["iter"].values, [5, 6])
    np.testing.assert_allclose(
        result["x"].sel(t=0.0).compute().values, [5.0, 20.0, 45.0]
    )
    np.testing.assert_allclose(
        result["ux"].sel(t=1.0).compute().values, [2.0, 4.0, 6.0]
    )
    assert result["ux"].attrs["units"] == r"$m_\mathrm{sp} c$"
    assert result["x"].attrs["long_name"] == r"$x$"


class FakeReadOpenPMDTimeSeries:
    avail_fields = ["E", "rho"]
    avail_species = ["electrons", "ions"]

    def __init__(self, path, check_all_files):
        self.path = path
        self.check_all_files = check_all_files


@pytest.mark.parametrize(
    "records,expected_fields,expected_species",
    [
        ("fields", ["all"], None),
        ("grid", ["all"], None),
        ("E", ["E"], None),
        (["E", "rho"], ["E", "rho"], None),
        ("electrons", None, "electrons"),
    ],
)
def test_read_routes_valid_records_to_read_sort(
    monkeypatch, records, expected_fields, expected_species
):
    calls = []

    def fake_read_sort(
        files, separate_theta_modes, fields=None, species=None, *args, **kwargs
    ):
        calls.append(
            {
                "files": files,
                "separate_theta_modes": separate_theta_modes,
                "fields": fields,
                "species": species,
            }
        )
        return xr.Dataset(attrs={"from_read_sort": True})

    monkeypatch.setattr(opb, "OpenPMDTimeSeries", FakeReadOpenPMDTimeSeries)
    monkeypatch.setattr(opb, "read_sort", fake_read_sort)

    files = ["/tmp/openpmd/fields000001.h5"]
    result = opb.read(files, records=records, separate_theta_modes=True)

    assert result.attrs["from_read_sort"] is True
    assert calls == [
        {
            "files": files,
            "separate_theta_modes": True,
            "fields": expected_fields,
            "species": expected_species,
        }
    ]


@pytest.mark.parametrize(
    "records,error_match",
    [
        (None, "Please choose which variables to read"),
        ("missing", "Can't find record 'missing'"),
        ("particles", "one particle species at a time"),
        (["electrons", "ions"], "Please choose one particle species"),
        (["E", "electrons"], "Provided 'records' list is invalid"),
    ],
)
def test_read_rejects_ambiguous_or_unavailable_records(
    monkeypatch, records, error_match
):
    monkeypatch.setattr(opb, "OpenPMDTimeSeries", FakeReadOpenPMDTimeSeries)

    with pytest.raises(ValueError, match=error_match):
        opb.read(["/tmp/openpmd/fields000001.h5"], records=records)


def test_read_rejects_adios2_files_before_constructing_openpmd_reader(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("OpenPMDTimeSeries should not be constructed for bp files")

    monkeypatch.setattr(opb, "OpenPMDTimeSeries", fail_if_called)

    with pytest.raises(NotImplementedError, match="ADIOS2 format"):
        opb.read(["/tmp/openpmd/fields000001.bp"], records="fields")


def test_read_returns_empty_dataset_for_empty_file_list():
    result = opb.read([], records="fields")

    assert isinstance(result, xr.Dataset)
    assert len(result.data_vars) == 0
    assert result.attrs["pic_data_type"] is None
    assert result.attrs["data_origin"] is None


def test_read_sort_reads_hdf5_metadata_and_applies_time_units(tmp_path, monkeypatch):
    path = tmp_path / "fields000001.h5"
    with h5py.File(path, "w") as h5f:
        h5f.attrs["meshesPath"] = np.array([b"meshes"])
        h5f.attrs["particlesPath"] = np.array([b"particles/"])
        h5f.attrs["openPMD"] = np.array([b"2.0.0"])
        step = h5f.create_group("/data/000001")
        step.attrs["timeUnitSI"] = 2.0
        meshes = step.create_group("meshes")
        meshes.attrs["geometry"] = np.array([b"cartesian"])
        meshes.attrs["gridSpacing"] = np.array([0.1, 0.2])

    fake_op_obj = SimpleNamespace(name="fake-reader")
    seen = {}

    def fake_openpmd_time_series(path_arg, check_all_files):
        seen["openpmd_args"] = (path_arg, check_all_files)
        return fake_op_obj

    def fake_read_fields(op_obj, fields, separate_theta_modes):
        seen["read_fields_args"] = (op_obj, fields, separate_theta_modes)
        return xr.Dataset(
            {"E": ("t", [1.0])},
            coords={"t": [3.0]},
            attrs={"pic_data_type": "grid", "data_origin": "openpmd"},
        )

    monkeypatch.setattr(opb, "OpenPMDTimeSeries", fake_openpmd_time_series)
    monkeypatch.setattr(opb, "read_fields", fake_read_fields)

    result = opb.read_sort([str(path)], separate_theta_modes=True, fields=["E"])

    assert seen["openpmd_args"] == (str(path), True)
    assert seen["read_fields_args"] == (fake_op_obj, ["E"], True)
    assert result.attrs["pic_data_type"] == "grid"
    assert result.attrs["data_origin"] == "openpmd"
    assert result.attrs["openPMD"] == "2.0.0"
    assert result.attrs["geometry"] == "cartesian"
    np.testing.assert_allclose(result.attrs["gridSpacing"], [0.1, 0.2])
    np.testing.assert_allclose(result["t"].values, [6.0])
    assert result["t"].attrs["long_name"] == r"$t$"
    assert result["t"].attrs["units"] == r"$\mathrm{s}$"
