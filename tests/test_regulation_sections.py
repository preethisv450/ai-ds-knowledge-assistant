import json

from src.data.regulation_sections import (coverage, detect_heading, save, split_inline_heading,
                                          split_regulation, topic_for)
from tests.data_helpers import make_pdf

BODY = ("A student must have at least seventy five percent attendance in each subject to be "
        "allowed to appear in the end semester examination of that subject.")


def test_detect_heading_forms():
    assert detect_heading("4.2 Attendance Requirement") == ("4.2", "Attendance Requirement")
    assert detect_heading("CHAPTER III - EXAMINATIONS") == ("III", "EXAMINATIONS")
    assert detect_heading("ATTENDANCE AND CONDONATION") == (None, "Attendance And Condonation")
    assert detect_heading("A student must attend all classes regularly and on time.") is None
    assert detect_heading("") is None


def test_split_inline_heading_only_fires_on_a_real_paragraph():
    title, rest = split_inline_heading(f"Attendance. {BODY}")
    assert title == "Attendance" and rest.startswith("A student must")
    assert split_inline_heading("Attendance. Yes.") is None
    assert split_inline_heading("the rule. applies here always and forever more") is None


def test_sections_carry_their_page_numbers(tmp_path):
    pdf = make_pdf(tmp_path / "regs.pdf", [
        f"ACADEMIC REGULATIONS\n\n1. Attendance\n{BODY}",
        f"2. Examinations\nEach subject carries forty marks of internal assessment and sixty marks "
        f"of end semester examination for every student enrolled.",
        f"3. Grading\nMarks are converted to letter grades and the cumulative grade point average "
        f"is computed from the credits earned in each subject.",
    ])
    sections = split_regulation(pdf)
    titles = {s["title"]: (s["first_page"], s["last_page"]) for s in sections}
    assert titles["Attendance"] == (1, 1)
    assert titles["Examinations"] == (2, 2)
    assert titles["Grading"] == (3, 3)
    assert all(s["word_count"] > 0 for s in sections)


def test_topics_are_tagged_and_coverage_lists_what_is_missing(tmp_path):
    pdf = make_pdf(tmp_path / "regs.pdf", [f"1. Attendance\n{BODY}"])
    sections = split_regulation(pdf)
    assert sections[0]["topic"] == "attendance"
    c = coverage(sections)
    assert c["found"] == ["attendance"] and "malpractice" in c["missing"]
    assert topic_for("Grading and CGPA") == "grading"


def test_a_heading_with_nothing_under_it_folds_into_the_previous_section(tmp_path):
    pdf = make_pdf(tmp_path / "regs.pdf", [f"1. Attendance\n{BODY}\n2. Reserved\nTBD"])
    sections = split_regulation(pdf)
    assert [s["title"] for s in sections] == ["Attendance"]
    assert "Reserved" in sections[0]["text"]


def test_text_before_the_first_heading_is_kept_as_a_preamble(tmp_path):
    pdf = make_pdf(tmp_path / "regs.pdf", [
        "These regulations apply to all undergraduate programmes of the college from the "
        "academic year onwards and supersede all earlier versions of the document.\n"
        f"1. Attendance\n{BODY}"])
    sections = split_regulation(pdf)
    assert sections[0]["title"] == "Preamble" and "supersede all earlier" in sections[0]["text"]


def test_an_empty_pdf_gives_no_sections(tmp_path):
    assert split_regulation(make_pdf(tmp_path / "blank.pdf", [" "])) == []


def test_save_writes_the_source_file_name(tmp_path):
    pdf = make_pdf(tmp_path / "regs.pdf", [f"1. Attendance\n{BODY}"])
    out = save(split_regulation(pdf), tmp_path / "out" / "regulations.json", source_file="regs.pdf")
    data = json.loads(out.read_text())
    assert data["source_file"] == "regs.pdf" and len(data["sections"]) == 1
