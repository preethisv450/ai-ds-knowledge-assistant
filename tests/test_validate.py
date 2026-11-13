import copy
import json

import pytest

from src.data.validate import counts, validate_all, validate_coverage, validate_curriculum, validate_manifest
from tests.data_helpers import CURRICULUM, make_pdf


def errors(findings):
    return [f["message"] for f in findings if f["level"] == "error"]


def warnings(findings):
    return [f["message"] for f in findings if f["level"] == "warning"]


def test_a_good_curriculum_has_no_errors():
    assert errors(validate_curriculum(CURRICULUM)) == []


def test_duplicate_subject_code_is_an_error():
    c = copy.deepcopy(CURRICULUM)
    c["years"][0]["semesters"][0]["subjects"].append({"code": "AI201", "name": "Another", "modules": [
        {"id": "AI201-M9", "title": "X"}]})
    assert any("used twice" in m for m in errors(validate_curriculum(c)))


def test_module_id_must_match_its_subject():
    c = copy.deepcopy(CURRICULUM)
    c["years"][0]["semesters"][0]["subjects"][0]["modules"][0]["id"] = "CS101-M1"
    assert any("does not belong to subject AI201" in m for m in errors(validate_curriculum(c)))


def test_malformed_module_id_and_missing_title():
    c = copy.deepcopy(CURRICULUM)
    c["years"][0]["semesters"][0]["subjects"][0]["modules"][0] = {"id": "AI201M1", "title": ""}
    e = errors(validate_curriculum(c))
    assert any("should look like" in m for m in e) and any("no title" in m for m in e)


def test_subject_without_modules_and_without_name():
    c = copy.deepcopy(CURRICULUM)
    c["years"][0]["semesters"][0]["subjects"] = [{"code": "CS999", "name": "", "modules": []}]
    e = errors(validate_curriculum(c))
    assert any("no modules" in m for m in e) and any("no name" in m for m in e)


def test_credits_out_of_range():
    c = copy.deepcopy(CURRICULUM)
    c["years"][0]["semesters"][0]["subjects"][0]["credits"] = 99
    assert any("credits" in m for m in errors(validate_curriculum(c)))


def test_gaps_in_module_numbering_are_a_warning():
    c = copy.deepcopy(CURRICULUM)
    c["years"][0]["semesters"][0]["subjects"][0]["modules"][1]["id"] = "AI201-M5"
    assert any("expected 1..2" in m for m in warnings(validate_curriculum(c)))


def test_missing_topics_is_a_warning_not_an_error():
    c = copy.deepcopy(CURRICULUM)
    del c["years"][0]["semesters"][0]["subjects"][0]["modules"][0]["topics"]
    f = validate_curriculum(c)
    assert errors(f) == [] and any("no topics" in m for m in warnings(f))


# ---------------- manifest ----------------
@pytest.fixture
def pdfs(tmp_path):
    body = "Module 1: Introduction\nRational agents and PEAS descriptions for the environment."
    make_pdf(tmp_path / "AI201_syllabus.pdf", [body, "Module 2: Search\nA star and heuristics.", "More search notes."])
    make_pdf(tmp_path / "Academic_Regulations.pdf", ["Attendance rules for every student of the college."])
    return tmp_path


def manifest(entries):
    return {e["file"].lower(): e for e in entries}


def test_manifest_flags_a_missing_file(pdfs):
    m = manifest([{"file": "Nope.pdf", "doc_type": "syllabus"}])
    assert any("not found in data/pdfs" in x for x in errors(validate_manifest(m, CURRICULUM, pdfs)))


def test_page_range_beyond_the_end_of_the_file(pdfs):
    m = manifest([{"file": "AI201_syllabus.pdf", "doc_type": "syllabus", "subject_code": "AI201",
                   "modules": {"AI201-M1": [1, 99]}}])
    assert any("has 3 pages" in x for x in errors(validate_manifest(m, CURRICULUM, pdfs)))


def test_two_modules_claiming_the_same_page(pdfs):
    m = manifest([{"file": "AI201_syllabus.pdf", "doc_type": "syllabus", "subject_code": "AI201",
                   "modules": {"AI201-M1": [1, 2], "AI201-M2": [2, 3]}}])
    assert any("both claim page 2" in x for x in errors(validate_manifest(m, CURRICULUM, pdfs)))


def test_unknown_subject_or_module_against_the_curriculum(pdfs):
    m = manifest([{"file": "AI201_syllabus.pdf", "doc_type": "syllabus", "subject_code": "ZZ999",
                   "modules": {"ZZ999-M1": [1, 1]}}])
    e = errors(validate_manifest(m, CURRICULUM, pdfs))
    assert any("ZZ999 is not in curriculum.json" in x for x in e)


def test_pages_outside_every_module_are_a_warning(pdfs):
    m = manifest([{"file": "AI201_syllabus.pdf", "doc_type": "syllabus", "subject_code": "AI201",
                   "modules": {"AI201-M1": [1, 1], "AI201-M2": [2, 2]}}])
    f = validate_manifest(m, CURRICULUM, pdfs)
    assert errors(f) == [] and any("pages [3]" in x for x in warnings(f))


def test_coverage_reports_undocumented_subjects_and_a_missing_regulation():
    f = validate_coverage(CURRICULUM, manifest([{"file": "AI201_syllabus.pdf", "subject_code": "AI201",
                                                 "doc_type": "syllabus"}]))
    assert any("no regulation document listed" in m for m in errors(f))
    f2 = validate_coverage(CURRICULUM, manifest([{"file": "r.pdf", "doc_type": "regulation"}]))
    assert any("AI201" in m and "no syllabus PDF" in m for m in warnings(f2))


def test_validate_all_reads_the_files_and_counts(tmp_path, pdfs):
    cur = tmp_path / "curriculum.json"
    cur.write_text(json.dumps(CURRICULUM))
    man = tmp_path / "documents.json"
    man.write_text(json.dumps([
        {"file": "AI201_syllabus.pdf", "doc_type": "syllabus", "subject_code": "AI201",
         "modules": {"AI201-M1": [1, 1], "AI201-M2": [2, 3]}},
        {"file": "Academic_Regulations.pdf", "doc_type": "regulation"}]))
    findings = validate_all(cur, man, pdfs)
    assert counts(findings)["errors"] == 0


def test_validate_all_reports_a_missing_or_broken_file(tmp_path):
    assert any("not found" in m for m in errors(validate_all(tmp_path / "nope.json", tmp_path / "d.json", tmp_path)))
    bad = tmp_path / "curriculum.json"
    bad.write_text("{not json")
    assert any("not valid JSON" in m for m in errors(validate_all(bad, tmp_path / "d.json", tmp_path)))
