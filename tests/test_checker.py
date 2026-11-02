import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("checker", Path(__file__).parents[1] / "checker.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_normalize_size():
    assert checker.normalize_size(" m ") == "M"


def test_find_medium_by_option1():
    product = {
        "variants": [
            {"id": 1, "title": "S", "option1": "S", "available": False},
            {"id": 2, "title": "M", "option1": "M", "available": True},
            {"id": 3, "title": "L", "option1": "L", "available": False},
        ]
    }
    variant = checker.find_variant(product, "M")
    assert variant["id"] == 2
    assert variant["available"] is True


def test_find_medium_by_title():
    product = {"variants": [{"id": 7, "title": "M", "available": False}]}
    variant = checker.find_variant(product, "M")
    assert variant["id"] == 7
