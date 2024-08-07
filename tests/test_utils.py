# TODO: unit tests for other modules

from hypothesis import given
from hypothesis import strategies as st

from src.ozzy.utils import force_str_to_list, tex_format


@given(st.text())
def test_tex_format_reverse(s):
    assert tex_format(s).strip("$") == s


@given(st.text())
def test_force_str_to_list(s):
    assert isinstance(force_str_to_list(s), list)
