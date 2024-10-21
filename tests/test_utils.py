import numpy as np
import pytest
import xarray as xr

from ozzy.utils import (
    axis_from_extent,
    bins_from_axis,
    force_str_to_list,
    get_regex_snippet,
    get_user_methods,
    path_list_to_pars,
    prep_file_input,
    recursive_search_for_file,
    tex_format,
    get_attr_if_exists,
    set_attr_if_exists,
)


def test_tex_format():
    assert tex_format("k_p^2") == "$k_p^2$"
    assert tex_format("") == ""
    assert tex_format("x + y") == "$x + y$"


def test_get_regex_snippet():
    assert get_regex_snippet(r"[a-z]+", "ABC123def") == "def"
    with pytest.raises(AttributeError):
        get_regex_snippet(r"\d+", "no_numbers_here")


class TestClass:
    def method1(self):
        pass

    def method2(self):
        pass

    def __private_method__(self):
        pass


def test_get_user_methods():
    methods = get_user_methods(TestClass)
    assert set(methods) == {"method1", "method2"}
    assert "__private_method__" not in methods


def test_prep_file_input(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.touch()
    file2.touch()

    result = prep_file_input(str(tmp_path / "*.txt"))
    assert len(result) == 2
    assert all(path.endswith(".txt") for path in result)

    with pytest.raises(FileNotFoundError):
        prep_file_input(str(tmp_path / "nonexistent*.txt"))


def test_force_str_to_list():
    assert force_str_to_list("hello") == ["hello"]
    assert force_str_to_list(["a", "b", "c"]) == ["a", "b", "c"]
    assert force_str_to_list(123) == 123


def test_recursive_search_for_file(tmp_path):
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").touch()
    (tmp_path / "dir2").mkdir()
    (tmp_path / "dir2" / "file2.txt").touch()

    result = recursive_search_for_file("*.txt", tmp_path)
    assert len(result) == 2
    assert set(result) == {"dir1/file1.txt", "dir2/file2.txt"}


def test_path_list_to_pars():
    paths = [
        "/path/to/run1/data1.h5",
        "/path/to/run1/data2.h5",
        "/path/to/run2/data1.h5",
    ]
    common_dir, dirs_runs, quants = path_list_to_pars(paths)

    assert common_dir == "/path/to"
    assert dirs_runs == {"run1": "/path/to/run1", "run2": "/path/to/run2"}
    assert set(quants) == {"data1.h5", "data2.h5"}


def test_axis_from_extent():
    axis = axis_from_extent(5, (0, 1))
    np.testing.assert_allclose(axis, [0.1, 0.3, 0.5, 0.7, 0.9])

    with pytest.raises(ZeroDivisionError):
        axis_from_extent(0, (0, 1))

    with pytest.raises(TypeError):
        axis_from_extent(5, (1, 0))


def test_bins_from_axis():
    axis = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
    bins = bins_from_axis(axis)
    np.testing.assert_allclose(bins, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0], atol=1e-14)


@pytest.fixture
def data_with_attrs():
    return xr.DataArray(np.random.rand(3, 3), attrs={'units': 'meters'})

def test_set_attr_if_exists_str(data_with_attrs):
    da = data_with_attrs
    # Test with string
    result = set_attr_if_exists(da, 'units', 'kilometers')
    assert result.attrs['units'] == 'kilometers'
    
def test_set_attr_if_exists_iter(data_with_attrs):
    da = data_with_attrs
    # Test with iterable
    result = set_attr_if_exists(da, 'units', ['Unit: ', ' (SI)'])
    assert result.attrs['units'] == 'Unit: meters (SI)'
    
def test_set_attr_if_exists_call(data_with_attrs):
    da = data_with_attrs
    # Test with callable
    result = set_attr_if_exists(da, 'units', lambda x: x.upper())
    assert result.attrs['units'] == 'METERS'
    
def test_set_attr_if_exists_nonexist(data_with_attrs):
    da = data_with_attrs
    # Test non-existing attribute
    result = set_attr_if_exists(da, 'description', 'New description', 'Default description')
    assert result.attrs['description'] == 'Default description'

def test_set_attr_if_exists_nonexist_nodefault(data_with_attrs):
    da = data_with_attrs
    # Test non-existing attribute without default
    result = set_attr_if_exists(da, 'category', 'New category')
    assert 'category' not in result.attrs

def test_set_attr_if_exists_warning(capsys):
    da = xr.DataArray(np.random.rand(3, 3), attrs={'units': 'meters'})
    set_attr_if_exists(da, 'units', ['Prefix: ', ' Middle: ', ' Suffix'])
    captured = capsys.readouterr()
    assert "WARNING: str_exists argument in set_attr_if_exists has more than two elements" in captured.out

def test_get_attr_if_exists_str(data_with_attrs):
    da = data_with_attrs
    # Test with string
    result = get_attr_if_exists(da, 'units', 'kilometers', 'No unit')
    assert result == 'kilometers'
    
def test_get_attr_if_exists_iter(data_with_attrs):
    da = data_with_attrs
    # Test with iterable
    result = get_attr_if_exists(da, 'units', ['Unit: ', ' (SI)'], 'No unit')
    assert result == 'Unit: meters (SI)'
    
def test_get_attr_if_exists_call(data_with_attrs):
    da = data_with_attrs
    # Test with callable
    result = get_attr_if_exists(da, 'units', lambda x: x.upper(), 'No unit')
    assert result == 'METERS'

def test_get_attr_if_exists_nonexist(data_with_attrs):
    da = data_with_attrs
    # Test non-existing attribute
    result = get_attr_if_exists(da, 'description', 'Exists', 'Does not exist')
    assert result == 'Does not exist'

def test_get_attr_if_exists_nonexist_nodefault(data_with_attrs):
    da = data_with_attrs
    # Test non-existing attribute without default
    result = get_attr_if_exists(da, 'category', 'Exists')
    assert result is None

def test_get_attr_if_exists_warning(capsys):
    da = xr.DataArray(np.random.rand(3, 3), attrs={'units': 'meters'})
    get_attr_if_exists(da, 'units', ['Prefix: ', ' Middle: ', ' Suffix'], 'No unit')
    captured = capsys.readouterr()
    assert "WARNING: str_exists argument in set_attr_if_exists has more than two elements" in captured.out
