import pytest

from src.backend.evaluation import load_questions
from src.data.questions import HEADER, TARGET_TOTAL, balance, check, write_template
from tests.data_helpers import CURRICULUM, make_pdf

ROW = "{id},{q},{mode},{code},{mid},{kw},{doc},{page},{ans},"


def write_set(tmp_path, rows):
    p = tmp_path / "test_questions.csv"
    p.write_text(",".join(HEADER) + "\n" + "\n".join(rows) + "\n")
    return p


@pytest.fixture
def pdfs(tmp_path):
    d = tmp_path / "pdfs"
    d.mkdir()
    make_pdf(d / "AI201_syllabus.pdf", ["Module 1: Introduction\nRational agents and PEAS descriptions.",
                                        "Module 2: Search\nA star search and admissible heuristics."])
    return d


def test_template_has_the_right_shape(tmp_path):
    p = write_template(tmp_path / "t.csv")
    lines = p.read_text().strip().splitlines()
    assert lines[0] == ",".join(HEADER)
    assert len(lines) - 1 == TARGET_TOTAL
    assert sum("Regulation" in l for l in lines[1:]) == 15
    assert sum(",no," in l for l in lines[1:]) == 4   # two unanswerable per mode


def test_a_well_formed_set_has_no_problems(tmp_path, pdfs):
    p = write_set(tmp_path, [
        ROW.format(id=1, q="What does PEAS stand for?", mode="Syllabus", code="AI201", mid="AI201-M1",
                   kw="Performance|Environment", doc="AI201_syllabus.pdf", page=1, ans="yes"),
        ROW.format(id=2, q="Who is the vice chancellor?", mode="Regulation", code="", mid="",
                   kw="", doc="", page="", ans="no"),
    ])
    assert check(load_questions(p), pdfs, CURRICULUM) == []


def test_missing_keywords_doc_or_page_are_reported(tmp_path, pdfs):
    p = write_set(tmp_path, [ROW.format(id=1, q="What does PEAS stand for?", mode="Syllabus", code="AI201",
                                        mid="AI201-M1", kw="", doc="", page="", ans="yes")])
    problems = " ".join(check(load_questions(p), pdfs, CURRICULUM))
    assert "no expected_keywords" in problems and "no expected_doc" in problems and "no expected_page" in problems


def test_a_page_number_past_the_end_of_the_file_is_caught(tmp_path, pdfs):
    p = write_set(tmp_path, [ROW.format(id=1, q="What is A star search?", mode="Syllabus", code="AI201",
                                        mid="AI201-M2", kw="heuristic", doc="AI201_syllabus.pdf",
                                        page=9, ans="yes")])
    assert any("has 2 pages" in x for x in check(load_questions(p), pdfs, CURRICULUM))


def test_unknown_subject_module_and_a_scoped_regulation_question(tmp_path, pdfs):
    p = write_set(tmp_path, [
        ROW.format(id=1, q="What is this about?", mode="Syllabus", code="ZZ999", mid="ZZ999-M1",
                   kw="x", doc="AI201_syllabus.pdf", page=1, ans="yes"),
        ROW.format(id=2, q="What is the attendance rule?", mode="Regulation", code="AI201", mid="",
                   kw="75", doc="AI201_syllabus.pdf", page=1, ans="yes"),
    ])
    problems = " ".join(check(load_questions(p), pdfs, CURRICULUM))
    assert "subject ZZ999 is not in curriculum.json" in problems
    assert "module ZZ999-M1 is not in curriculum.json" in problems
    assert "should not set subject_code" in problems


def test_duplicates_and_a_too_short_question(tmp_path, pdfs):
    p = write_set(tmp_path, [
        ROW.format(id=1, q="What does PEAS stand for?", mode="Syllabus", code="AI201", mid="AI201-M1",
                   kw="Performance", doc="AI201_syllabus.pdf", page=1, ans="yes"),
        ROW.format(id=1, q="what does peas   stand for?", mode="Syllabus", code="AI201", mid="AI201-M1",
                   kw="Performance", doc="AI201_syllabus.pdf", page=1, ans="yes"),
        ROW.format(id=3, q="PEAS?", mode="Syllabus", code="AI201", mid="AI201-M1",
                   kw="Performance", doc="AI201_syllabus.pdf", page=1, ans="yes"),
    ])
    problems = " ".join(check(load_questions(p), pdfs, CURRICULUM))
    assert "id used twice" in problems and "same question" in problems and "too short" in problems


def test_an_unanswerable_question_must_not_carry_an_expected_answer(tmp_path, pdfs):
    p = write_set(tmp_path, [ROW.format(id=1, q="Who is the vice chancellor of the university?",
                                        mode="Regulation", code="", mid="", kw="someone",
                                        doc="AI201_syllabus.pdf", page=1, ans="no")])
    assert any("marked unanswerable but has an expected answer" in x
               for x in check(load_questions(p), pdfs, CURRICULUM))


def test_balance_reports_what_is_missing_against_the_plan(tmp_path, pdfs):
    p = write_set(tmp_path, [ROW.format(id=1, q="What does PEAS stand for?", mode="Syllabus", code="AI201",
                                        mid="AI201-M1", kw="Performance", doc="AI201_syllabus.pdf",
                                        page=1, ans="yes")])
    b = balance(load_questions(p))
    assert b["total"] == 1 and b["by_mode"] == {"Syllabus": 1}
    joined = " ".join(b["notes"])
    assert "the plan asks for 30" in joined and "0 Regulation questions" in joined
    assert "unanswerable" in joined
    assert b["modules_covered"] == ["AI201-M1"]
