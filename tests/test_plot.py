import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
import xarray as xr
from hypothesis import given, HealthCheck, settings
from hypothesis import strategies as st

from ozzy.plot import _cmap_exists, movie, set_cmap, set_font


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

@pytest.fixture
def sample_data():
    time = np.arange(0, 10, 1.0)
    x = np.arange(-20, 0, 0.2)
    X, T = np.meshgrid(x, time)
    data = np.sin(X - 0.5 * T)
    return xr.DataArray(data, coords={"time": time, "x": x}, dims=["time", "x"])


def test_movie_basic(tmp_path, sample_data):
    fig, ax = plt.subplots()
    line = sample_data.isel(time=0).plot(ax=ax)
    output_file = tmp_path / "test_movie.mp4"
    movie(fig, {line[0]: (sample_data, "time")}, str(output_file))
    assert output_file.exists()


def test_movie_multiple_plots(tmp_path, sample_data):
    fig, (ax1, ax2) = plt.subplots(2, 1)
    line1 = sample_data.isel(time=0).plot(ax=ax1)
    line2 = sample_data.isel(time=0).plot(ax=ax2)
    output_file = tmp_path / "test_movie_multiple.mp4"
    movie(
        fig,
        {line1[0]: (sample_data, "time"), line2[0]: (sample_data, "time")},
        str(output_file),
    )
    assert output_file.exists()


def test_movie_custom_limits(tmp_path, sample_data):
    fig, ax = plt.subplots()
    line = sample_data.isel(time=0).plot(ax=ax)
    output_file = tmp_path / "test_movie_limits.mp4"
    movie(
        fig,
        {line[0]: (sample_data, "time")},
        str(output_file),
        xlim=(-10, 0),
        ylim=(-1, 1),
        clim=(-0.5, 0.5),
    )
    assert output_file.exists()


def test_movie_invalid_time_variable():
    fig, ax = plt.subplots()
    invalid_data = xr.DataArray(np.random.rand(10, 10), dims=["x", "y"])
    im = invalid_data.plot(ax=ax)
    with pytest.raises(ValueError):
        movie(fig, {im: (invalid_data, "time")}, "invalid.mp4")


@pytest.fixture(scope="session")
def tmp_path_fixt(tmp_path_factory):
    return tmp_path_factory.mktemp("data")

def test_movie_writer_options(tmp_path, sample_data):
    writers = ["pillow", "html", "frames_png"]
    formats = [".gif", ".html", ""]
    for writer, fileformat in zip(writers,formats):
        fig, ax = plt.subplots()
        line = sample_data.isel(time=0).plot(ax=ax)
        output_file = tmp_path / f"test_movie_{writer}{fileformat}"
        movie(fig, {line[0]: (sample_data, "time")}, str(output_file), writer=writer)
        if writer == "frames_png":
            assert (tmp_path / "frame_0000.png").exists()
        else:
            assert output_file.exists()


def test_movie_invalid_writer(sample_data):
    fig, ax = plt.subplots()
    line = sample_data.isel(time=0).plot(ax=ax)
    with pytest.raises(ValueError):
        movie(fig, {line[0]: (sample_data, "time")}, "invalid.mp4", writer="invalid_writer")
