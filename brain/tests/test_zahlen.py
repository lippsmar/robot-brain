"""Tests for German number notation."""

import pytest

from brain.zahlen import zahl


@pytest.mark.parametrize(
    ("value", "digits", "expected"),
    [(21.5, None, "21,5"), (64.0, None, "64"), (54.6, 0, "55"), (22.94, 1, "22,9"), (-3.25, None, "-3,25")],
)
def test_german_notation(value, digits, expected):
    assert zahl(value, digits) == expected
