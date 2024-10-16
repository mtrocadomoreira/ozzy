import matplotlib as mpl
import pytest
from hypothesis import given
from hypothesis import strategies as st

from ozzy.plot import _cmap_exists, set_cmap, set_font


def test_set_font_valid():
    set_font("Arial")
    assert mpl.rcParams["font.family"] == ["Arial"]


def test_set_font_invalid():
    with pytest.raises(ValueError):
        set_font("NonexistentFont")


def test_set_cmap_general():
    set_cmap(general="viridis")
    assert mpl.rcParams["image.cmap"] == "viridis"


def test_set_cmap_diverging():
    set_cmap(diverging="cmc.vik")
    import xarray as xr

    assert xr.get_options()["cmap_divergent"] == "cmc.vik"


def test_set_cmap_sequential():
    set_cmap(sequential="cmc.lipari")
    import xarray as xr

    assert xr.get_options()["cmap_sequential"] == "cmc.lipari"


def test_set_cmap_qualitative_tol():
    set_cmap(qualitative="tol.bright")
    assert "color" in mpl.rcParams["axes.prop_cycle"]
    assert len(mpl.rcParams["axes.prop_cycle"].by_key()["color"]) > 0


def test_set_cmap_qualitative_cmc():
    set_cmap(qualitative="cmc.batlow")
    assert "color" in mpl.rcParams["axes.prop_cycle"]
    assert len(mpl.rcParams["axes.prop_cycle"].by_key()["color"]) > 0


def test_set_cmap_qualitative_custom():
    custom_colors = ["#FF0000", "#00FF00", "#0000FF"]
    set_cmap(qualitative=custom_colors)
    assert mpl.rcParams["axes.prop_cycle"].by_key()["color"] == custom_colors


def test_set_cmap_invalid_qualitative():
    with pytest.raises(ValueError):
        set_cmap(qualitative="invalid_cmap")


def test_cmap_exists():
    assert _cmap_exists("viridis")
    assert not _cmap_exists("nonexistent_cmap")


@given(st.sampled_from(["viridis", "plasma", "inferno", "magma"]))
def test_set_cmap_general_hypothesis(cmap):
    set_cmap(general=cmap)
    assert mpl.rcParams["image.cmap"] == cmap


def test_set_cmap_multiple():
    set_cmap(diverging="cmc.vik", sequential="cmc.lipari", qualitative="tol.bright")
    import xarray as xr

    assert xr.get_options()["cmap_divergent"] == "cmc.vik"
    assert xr.get_options()["cmap_sequential"] == "cmc.lipari"
    assert "color" in mpl.rcParams["axes.prop_cycle"]
    assert len(mpl.rcParams["axes.prop_cycle"].by_key()["color"]) > 0
