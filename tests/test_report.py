from src.data.report import (PARTIAL_COVERAGE, compare, grade, grade_all, load_csv, meets_target,
                             report, save_csv)


def res(**kw):
    base = {"id": "1", "question": "q?", "answerable": True, "top_score": 0.4, "retrieval_hit": True,
            "answer": "an answer (A.pdf, p.1)", "coverage": 1.0, "cited_ok": True, "correct": True,
            "why": "", "error": False}
    base.update(kw)
    return base


def test_a_full_answer_with_the_right_citation_is_correct():
    assert grade(res()) == ("correct", "")


def test_right_content_but_the_wrong_page_is_partial():
    assert grade(res(cited_ok=False)) == ("partial", "wrong_citation")


def test_an_incomplete_answer_is_partial_and_a_mostly_missed_one_is_wrong():
    assert grade(res(coverage=0.4, correct=False, why="covers 40%")) == ("partial", "partial_coverage")
    assert grade(res(coverage=0.0, correct=False, why="covers 0%")) == ("wrong", "low_coverage")
    assert grade(res(coverage=PARTIAL_COVERAGE)) [0] == "partial"


def test_refusing_a_question_the_documents_answer_is_wrong_with_the_right_reason():
    missed = res(correct=False, why="said not found, but the answer is in the documents",
                 retrieval_hit=False, coverage=0.0)
    assert grade(missed) == ("wrong", "retrieval_miss")
    found_but_refused = dict(missed, retrieval_hit=True)
    assert grade(found_but_refused) == ("wrong", "refused_wrongly")


def test_unanswerable_questions_are_graded_on_refusal_alone():
    assert grade(res(answerable=False, correct=True, coverage=None, cited_ok=None)) == ("correct", "")
    assert grade(res(answerable=False, correct=False, coverage=None, cited_ok=None)) == \
        ("wrong", "answered_unanswerable")


def test_a_gemini_failure_is_not_scored():
    verdict, reason = grade(res(error=True))
    assert verdict == "error" and reason == "service_error"


def test_report_counts_accuracy_both_ways():
    rows = grade_all([
        res(id="1"), res(id="2"),
        res(id="3", cited_ok=False),                                   # partial
        res(id="4", coverage=0.0, correct=False, why="covers 0%"),     # wrong
        res(id="5", error=True),                                       # not scored
    ])
    s = report(rows)
    assert (s["correct"], s["partial"], s["wrong"], s["errors"]) == (2, 1, 1, 1)
    assert s["scored"] == 4
    assert s["accuracy"] == 0.5
    assert s["accuracy_lenient"] == 0.625
    assert s["retrieval_hit_rate"] == 1.0
    assert s["reasons"]["wrong_citation"] == 1


def test_meets_target():
    assert meets_target({"accuracy": 0.8}) is True
    assert meets_target({"accuracy": 0.79}) is False
    assert meets_target({"accuracy": None}) is None


def test_save_and_reload_a_run(tmp_path):
    rows = grade_all([res(id="1"), res(id="2", coverage=0.0, correct=False, why="covers 0%")])
    for r in rows:
        r["mode"] = "Syllabus"
    path = save_csv(rows, tmp_path / "run.csv")
    back = load_csv(path)
    assert [r["verdict"] for r in back] == ["correct", "wrong"]
    assert back[0]["mode"] == "Syllabus"


def test_compare_finds_fixes_regressions_and_what_is_still_failing(tmp_path):
    first = grade_all([
        res(id="1", coverage=0.0, correct=False, why="covers 0%"),   # wrong
        res(id="2"),                                                  # correct
        res(id="3", coverage=0.0, correct=False, why="covers 0%"),   # wrong
    ])
    path = save_csv(first, tmp_path / "first.csv")

    second = grade_all([
        res(id="1"),                                                  # fixed
        res(id="2", coverage=0.0, correct=False, why="covers 0%"),   # regressed
        res(id="3", coverage=0.0, correct=False, why="covers 0%"),   # still wrong
        res(id="4"),                                                  # new question
    ])
    c = compare(load_csv(path), second)
    assert [x[0] for x in c["fixed"]] == ["1"]
    assert [x[0] for x in c["broken"]] == ["2"]
    assert [x[0] for x in c["still_failing"]] == ["3"]
    assert c["new_questions"] == ["4"] and c["unchanged"] == 1


def test_partial_counts_as_an_improvement_over_wrong(tmp_path):
    first = save_csv(grade_all([res(id="1", coverage=0.0, correct=False, why="covers 0%")]), tmp_path / "a.csv")
    c = compare(load_csv(first), grade_all([res(id="1", cited_ok=False)]))
    assert [x[0] for x in c["fixed"]] == ["1"] and c["broken"] == []
