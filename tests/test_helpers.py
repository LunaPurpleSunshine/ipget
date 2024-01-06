import datetime
import os
from pathlib import Path

import pytest
from hypothesis import assume, example, given
from hypothesis import strategies as st

from ipget.helpers import custom_namer


@pytest.fixture
def mock_datetime_now(monkeypatch):
    """
    Mocks the current datetime to a fixed value for testing purposes.

    Args:
        monkeypatch: The monkeypatch fixture provided by pytest.

    Returns:
        None
    """

    class MockDatetime(datetime.datetime):
        @classmethod
        def now(cls):
            """
            Returns a fixed datetime representing 1963-11-23 17:16:00.
            """
            return datetime.datetime(1963, 11, 23, 17, 16, 0)

    monkeypatch.setattr(datetime, "datetime", MockDatetime)


class TestCustomNamer:
    def test_actual(self, mock_datetime_now):
        default_log_file_name = "/app/logs/ipget.log"
        new_file_name = custom_namer(default_log_file_name)
        if os.name == "nt":
            assert new_file_name == "C:\\app\\logs\\ipget.1963-11-23.log"
        else:
            assert new_file_name == "/app/logs/ipget.1963-11-23.log"

    @given(
        stem=st.text(min_size=1, alphabet=st.characters(categories=["L", "N", "S"])),
        suffix=st.text(
            min_size=1, max_size=10, alphabet=st.characters(categories=["L", "N", "S"])
        ),
    )
    @example(stem="ipget", suffix="log")
    def test_expected_input(self, stem: str, suffix: str):
        assume(all([stem, suffix]))

        input_name = f"{stem}.{suffix}"
        expected_output = f"{stem}.{datetime.datetime.now().date()}.log"

        result = custom_namer(input_name)

        assert Path(result).name == expected_output

    @given(
        stem=st.text(
            min_size=1,
            alphabet=st.characters(categories=["L", "N", "S"]),
        ),
        suffix=st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(categories=["L", "N", "S"]),
        ),
    )
    def test_multiple_suffixes(self, stem, suffix):
        assume(all([stem, suffix]))

        input_name = f"{stem}.{suffix}.{suffix}"
        expected_output = f"{stem}.{suffix}.{datetime.datetime.now().date()}.log"

        result = custom_namer(input_name)

        assert Path(result).name == expected_output

    @given(name=st.integers() | st.booleans())
    def test_not_str(self, name):
        with pytest.raises(TypeError):
            custom_namer(name)

    @given(
        suffix=st.text(
            min_size=1, max_size=10, alphabet=st.characters(categories=["L", "N"])
        )
    )
    def test_invalid_input_stem(self, suffix):
        name = f".{suffix}"
        with pytest.raises(ValueError):
            custom_namer(name)

    @given(stem=st.text(min_size=1, alphabet=st.characters(categories=["L", "N"])))
    def test_invalid_input_suffix(self, stem):
        name = f"{stem}"
        with pytest.raises(ValueError):
            custom_namer(name)

    @given(name=st.text(min_size=1))
    def test_invalid_input(self, name):
        assume("." not in name)
        with pytest.raises(ValueError):
            custom_namer(name)
