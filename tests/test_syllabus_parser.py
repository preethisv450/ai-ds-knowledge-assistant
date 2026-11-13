import pytest

from src.data.syllabus_parser import module_pages, parse_syllabus, to_curriculum_entry
from tests.data_helpers import make_pdf

SYLLABUS = [
    "AI201 Artificial Intelligence\nCredits: 4\n\nModule 1: Introduction to AI\n"
    "Rational agents, PEAS description, agent types, task environments, Turing test.",
    "AI201 Artificial Intelligence\n\nModule 2 - Problem Solving and Search\n"
    "Breadth first search, depth first search, A star search, admissible heuristics, hill climbing.",
    "AI201 Artificial Intelligence\n\nMODULE 3 : Knowledge Representation\n"
    "Propositional logic, first order logic, resolution, forward chaining, semantic networks.",
]


@pytest.fixture
def syllabus(tmp_path):
    return make_pdf(tmp_path / "AI201_syllabus.pdf", SYLLABUS)


def test_code_name_credits_and_modules(syllabus):
    d = parse_syllabus(syllabus)
    assert d["code"] == "AI201"
    assert d["name"] == "Artificial Intelligence"
    assert d["credits"] == 4
    assert [m["id"] for m in d["modules"]] == ["AI201-M1", "AI201-M2", "AI201-M3"]
    assert [m["title"] for m in d["modules"]] == [
        "Introduction to AI", "Problem Solving and Search", "Knowledge Representation"]


def test_module_pages_do_not_overlap(syllabus):
    pages = module_pages(parse_syllabus(syllabus))
    assert pages == {"AI201-M1": [1, 1], "AI201-M2": [2, 2], "AI201-M3": [3, 3]}


def test_topics_are_split_from_the_module_body(syllabus):
    d = parse_syllabus(syllabus)
    topics = [t.lower() for t in d["modules"][1]["topics"]]
    assert "a star search" in topics and "admissible heuristics" in topics
    assert all(2 <= len(t.split()) <= 8 for t in topics)


def test_ltpc_credits_are_read_from_the_last_number(tmp_path):
    pdf = make_pdf(tmp_path / "CS101_syllabus.pdf",
                   ["CS101 Programming in C\nL-T-P-C 3-0-2-4\n\nModule 1: Basics\nVariables, loops, functions."])
    assert parse_syllabus(pdf)["credits"] == 4


def test_roman_unit_headings_are_understood(tmp_path):
    pdf = make_pdf(tmp_path / "DS202_syllabus.pdf",
                   ["DS202 Machine Learning\n\nUNIT I - Supervised Learning\nRegression, classification, overfitting.",
                    "DS202 Machine Learning\n\nUNIT II : Unsupervised Learning\nClustering, k means, dendrogram."])
    d = parse_syllabus(pdf)
    assert [m["id"] for m in d["modules"]] == ["DS202-M1", "DS202-M2"]
    assert d["modules"][1]["title"] == "Unsupervised Learning"


def test_an_unreadable_pdf_is_reported_not_crashed(tmp_path):
    blank = make_pdf(tmp_path / "ZZ999_syllabus.pdf", [" "])
    d = parse_syllabus(blank)
    assert d["modules"] == [] and any("scanned" in r or "OCR" in r for r in d["_review"])


def test_missing_pieces_are_listed_for_review(tmp_path):
    pdf = make_pdf(tmp_path / "unknown.pdf", ["Some notes with no code, no credits and no modules at all."])
    d = parse_syllabus(pdf)
    assert d["code"] is None
    joined = " ".join(d["_review"])
    assert "code" in joined and "credits" in joined and "Module" in joined


def test_subject_code_can_be_given_explicitly(tmp_path):
    pdf = make_pdf(tmp_path / "scan_of_syllabus.pdf", ["Operating Systems\n\nModule 1: Processes\nScheduling, threads."])
    d = parse_syllabus(pdf, subject_code="CS305")
    assert d["code"] == "CS305" and d["modules"][0]["id"] == "CS305-M1"


def test_curriculum_entry_drops_draft_only_fields(syllabus):
    entry = to_curriculum_entry(parse_syllabus(syllabus))
    assert set(entry) == {"code", "name", "credits", "source_file", "modules"}
    assert all(set(m) <= {"id", "title", "topics"} for m in entry["modules"])
