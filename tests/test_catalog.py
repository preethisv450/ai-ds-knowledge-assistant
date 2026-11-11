import json

import pytest

from src.backend.catalog import classify, load_manifest, make_filter, scope_label


def test_classify_by_filename_convention():
    assert classify("AI201_syllabus.pdf", 1) == {"doc_type": "syllabus", "subject_code": "AI201", "module_id": None}
    assert classify("ds202-notes.pdf", 1)["subject_code"] == "DS202"
    assert classify("Academic_Regulations_2024.pdf", 3)["doc_type"] == "regulation"
    assert classify("Exam_Policy.pdf", 3)["doc_type"] == "regulation"
    assert classify("SNA_project.pdf", 1)["doc_type"] == "other"


def test_manifest_overrides_filename_and_maps_pages_to_modules():
    manifest = {"all_subjects.pdf": {"file": "all_subjects.pdf", "doc_type": "syllabus", "subject_code": "ai201",
                                     "modules": {"AI201-M1": [1, 4], "AI201-M2": [5, 8]}}}
    assert classify("All_Subjects.pdf", 2, manifest) == {"doc_type": "syllabus", "subject_code": "AI201", "module_id": "AI201-M1"}
    assert classify("all_subjects.pdf", 5, manifest)["module_id"] == "AI201-M2"
    assert classify("all_subjects.pdf", 99, manifest)["module_id"] is None  # outside every range


def test_load_manifest_missing_file_is_empty(tmp_path):
    assert load_manifest(tmp_path / "nope.json") == {}


def test_load_manifest_accepts_list_or_documents_key(tmp_path):
    entry = {"file": "A.pdf", "doc_type": "regulation"}
    for body in ([entry], {"documents": [entry]}):
        p = tmp_path / "m.json"
        p.write_text(json.dumps(body))
        assert "a.pdf" in load_manifest(p)


@pytest.mark.parametrize("body,msg", [
    ("not json", "not valid JSON"),
    ({"x": 1}, "must be a list"),
    ([{"doc_type": "syllabus"}], "needs a 'file'"),
    ([{"file": "a.pdf", "doc_type": "notes"}], "doc_type"),
    ([{"file": "a.pdf", "modules": {"M1": [5, 2]}}], "first_page, last_page"),
])
def test_load_manifest_rejects_bad_content_with_clear_errors(tmp_path, body, msg):
    p = tmp_path / "m.json"
    p.write_text(body if isinstance(body, str) else json.dumps(body))
    with pytest.raises(ValueError, match=msg):
        load_manifest(p)


def chunk(doc_type, code=None, module=None):
    return {"doc_type": doc_type, "subject_code": code, "module_id": module}


def test_regulation_filter_only_regulation_documents():
    f = make_filter("Regulation", {"subject_code": "AI201"})
    assert f(chunk("regulation")) and not f(chunk("syllabus", "AI201")) and not f(chunk("other"))


def test_syllabus_filter_scopes_to_subject_and_module():
    sel = {"subject_code": "AI201", "module_id": "AI201-M2"}
    f = make_filter("Syllabus", sel)
    assert f(chunk("syllabus", "AI201", "AI201-M2"))
    assert f(chunk("syllabus", "AI201", None))        # document not split into modules: any module of the subject
    assert not f(chunk("syllabus", "AI201", "AI201-M1"))
    assert not f(chunk("syllabus", "DS202", "AI201-M2"))
    assert not f(chunk("regulation")) and not f(chunk("other"))


def test_syllabus_filter_without_selection_allows_all_syllabus_documents():
    f = make_filter("Syllabus", None)
    assert f(chunk("syllabus", "AI201")) and f(chunk("syllabus", "DS202")) and not f(chunk("regulation"))


def test_scope_label():
    assert scope_label("Regulation") == "the academic regulations"
    assert scope_label("Syllabus", {"subject": "Machine Learning", "module": "Regression"}) == "Machine Learning — Regression"
    assert scope_label("Syllabus", None) == "the syllabus"
