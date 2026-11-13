import json

import pytest

from src.data.manifest import build, find_module_pages, guess_doc_type, merge, save
from tests.data_helpers import CURRICULUM, make_pdf


@pytest.fixture
def pdfs(tmp_path):
    make_pdf(tmp_path / "AI201_syllabus.pdf", [
        "AI201 Artificial Intelligence\n\nModule 1: Introduction to AI\nRational agents and PEAS.",
        "AI201 Artificial Intelligence\n\nModule 2: Search\nBreadth first search and A star.",
        "AI201 Artificial Intelligence\n\nMore on search: hill climbing and simulated annealing.",
    ])
    make_pdf(tmp_path / "Academic_Regulations.pdf", [
        "1. Attendance\nA student must have seventy five percent attendance in each subject.",
        "2. Examinations\nEach subject has internal assessment and a semester end examination."])
    return tmp_path


def test_doc_type_from_the_file_name(pdfs):
    assert guess_doc_type(pdfs / "AI201_syllabus.pdf") == "syllabus"
    assert guess_doc_type(pdfs / "Academic_Regulations.pdf") == "regulation"


def test_module_pages_are_found_and_the_last_module_runs_to_the_end(pdfs):
    ranges, notes = find_module_pages(pdfs / "AI201_syllabus.pdf", "AI201", None)
    assert ranges == {"AI201-M1": [1, 1], "AI201-M2": [2, 3]}
    assert notes == []


def test_build_produces_a_usable_manifest(pdfs):
    entries, notes = build(pdfs, CURRICULUM)
    by_file = {e["file"]: e for e in entries}
    assert by_file["AI201_syllabus.pdf"]["subject_code"] == "AI201"
    assert by_file["AI201_syllabus.pdf"]["modules"]["AI201-M1"] == [1, 1]
    assert by_file["Academic_Regulations.pdf"]["doc_type"] == "regulation"
    assert "modules" not in by_file["Academic_Regulations.pdf"]


def test_a_title_mismatch_against_the_curriculum_is_reported(pdfs):
    changed = json.loads(json.dumps(CURRICULUM))
    changed["years"][0]["semesters"][0]["subjects"][0]["modules"][1]["title"] = "Completely Different Topic"
    _, notes = build(pdfs, changed)
    assert any("check they are the same module" in n for n in notes)


def test_a_module_in_the_curriculum_that_is_not_in_the_pdf_is_reported(pdfs):
    changed = json.loads(json.dumps(CURRICULUM))
    changed["years"][0]["semesters"][0]["subjects"][0]["modules"].append(
        {"id": "AI201-M3", "title": "Knowledge Representation"})
    _, notes = build(pdfs, changed)
    assert any("not found in the PDF" in n for n in notes)


def test_an_unknown_subject_code_is_reported(pdfs, tmp_path):
    make_pdf(pdfs / "ZZ999_syllabus.pdf", ["ZZ999 Mystery\n\nModule 1: Something\nAnything at all."])
    _, notes = build(pdfs, CURRICULUM)
    assert any("ZZ999 is not in curriculum.json" in n for n in notes)


def test_a_pdf_with_no_module_headings_is_reported(pdfs):
    make_pdf(pdfs / "CS101_syllabus.pdf", ["CS101 Programming\nJust prose with no module headings anywhere."])
    _, notes = build(pdfs, CURRICULUM)
    assert any("no 'Module N'" in n for n in notes)


def test_merge_keeps_hand_edited_entries(pdfs):
    existing = [{"file": "AI201_syllabus.pdf", "doc_type": "syllabus", "subject_code": "AI201",
                 "modules": {"AI201-M1": [1, 3]}, "note": "fixed by hand"}]
    entries, _ = build(pdfs, CURRICULUM)
    merged = merge(existing, entries)
    kept = next(e for e in merged if e["file"] == "AI201_syllabus.pdf")
    assert kept["note"] == "fixed by hand" and kept["modules"] == {"AI201-M1": [1, 3]}
    assert any(e["file"] == "Academic_Regulations.pdf" for e in merged)
    assert len(merged) == len(entries)


def test_saved_manifest_loads_back_through_the_backend(pdfs, tmp_path):
    from src.backend.catalog import load_manifest
    entries, _ = build(pdfs, CURRICULUM)
    path = save(entries, tmp_path / "documents.json")
    loaded = load_manifest(path)
    assert "ai201_syllabus.pdf" in loaded
