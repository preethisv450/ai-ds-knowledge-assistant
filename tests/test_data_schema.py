import pytest

from src.data import schema
from tests.data_helpers import CURRICULUM


def test_module_id_round_trip():
    assert schema.module_id_for("ai201", 3) == "AI201-M3"
    assert schema.subject_of_module("AI201-M3") == "AI201"
    assert schema.subject_of_module("ai201-m3") == "AI201"
    for bad in ("AI201M3", "AI201-3", "", None, "M3"):
        assert schema.subject_of_module(bad) is None


def test_patterns_accept_real_codes_and_reject_junk():
    for good in ("CS101", "AI201", "DS402A", "MATH101"):
        assert schema.SUBJECT_CODE.match(good), good
    for bad in ("cs101", "C101", "CS10", "CS1011A1"):
        assert not schema.SUBJECT_CODE.match(bad), bad


def test_iterators_and_lookup():
    assert [s["code"] for _, _, s in schema.iter_subjects(CURRICULUM)] == ["AI201"]
    mods = [m["id"] for _, _, _, m in schema.iter_modules(CURRICULUM)]
    assert mods == ["AI201-M1", "AI201-M2"]
    subject, module = schema.find_module(CURRICULUM, "ai201-m2")
    assert subject["code"] == "AI201" and module["title"] == "Search"
    assert schema.find_module(CURRICULUM, "ZZ999-M1") == (None, None)


def test_iterators_tolerate_an_empty_tree():
    assert list(schema.iter_subjects({})) == [] and list(schema.iter_modules({})) == []
