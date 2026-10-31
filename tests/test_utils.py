from src.utils import dedupe_preserve_order


def test_dedupe_preserve_order():
    items = ["a", "b", "a", "c", "b", "d"]
    assert dedupe_preserve_order(items) == ["a", "b", "c", "d"]


def test_dedupe_preserve_order_empty():
    assert dedupe_preserve_order([]) == []
