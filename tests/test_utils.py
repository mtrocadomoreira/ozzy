import hypothesis.extra.numpy as npst
from hypothesis import given
from hypothesis import strategies as st

from src.ozzy.utils import axis_from_extent, force_str_to_list, tex_format, unpack_str


@given(st.text())
def test_unpack_str_with_string(s):
    assert unpack_str(s) == s


@given(
    npst.arrays(
        dtype=str,
        shape=st.sampled_from([tuple(), (1, 1), (1,)]),
        elements=st.text(),
    )
)
def test_unpack_str_with_ndarray(s):
    assert isinstance(unpack_str(s), str)


@given(st.text())
def test_tex_format_reverse(s):
    assert tex_format(s).strip("$") == s


@given(st.text())
def test_force_str_to_list(s):
    assert isinstance(force_str_to_list(s), list)


@given(st.builds(axis_from_extent, st.integers(1)))
def test_axis_from_extent(s):
    axis = axis_from_extent(s)
    assert axis.size == s.nx
