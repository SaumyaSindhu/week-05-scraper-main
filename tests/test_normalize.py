import pytest

from src.normalize import normalize_price


def test_normalize_price_simple():
    assert normalize_price("£51.77") == 51.77


def test_normalize_price_whole_number():
    assert normalize_price("£10") == 10.0


def test_normalize_price_no_number_raises():
    with pytest.raises(ValueError):
        normalize_price("no price here")
