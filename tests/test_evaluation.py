import pytest

from src.backend import evaluation as ev
from src.backend.prompts import NOT_FOUND

CSV = """id,question,mode,subject_code,module_id,expected_keywords,expected_doc,expected_page,answerable
1,What is a perceptron?,Syllabus,AI201,AI201-M1,neuron|weights,AI.pdf,4,yes
2,Capital of Peru?,syllabus,,,,,,no
3,Attendance rule?,Regulation,,,75%,Regs.pdf,3,yes
"""


@pytest.fixture
def csv_path(tmp_path):
    p = tmp_path / "q.csv"
    p.write_text(CSV)
    return p


def test_load_questions_parses_and_normalises(csv_path):
    rows = ev.load_questions(csv_path)
    assert len(rows) == 3
    r = rows[0]
    assert r["selection"] == {"subject_code": "AI201", "module_id": "AI201-M1"}
    assert r["keywords"] == ["neuron", "weights"] and r["expected_page"] == 4 and r["answerable"] is True
    assert rows[1]["mode"] == "Syllabus" and rows[1]["answerable"] is False and rows[1]["selection"] is None
    assert rows[2]["mode"] == "Regulation"


@pytest.mark.parametrize("text,msg", [
    ("id,mode\n1,Syllabus\n", "'question' column"),
    ("question,mode\nx,Other\n", "mode must be"),
    ("question,answerable\nx,maybe\n", "answerable must be"),
    ("question,expected_page\nx,abc\n", "expected_page"),
    ("question\n\n", "no questions"),
])
def test_load_questions_clear_errors(tmp_path, text, msg):
    p = tmp_path / "bad.csv"
    p.write_text(text)
    with pytest.raises(ValueError, match=msg):
        ev.load_questions(p)


def test_keyword_coverage():
    assert ev.keyword_coverage("It uses retries and a timeout.", ["retries", "timeout", "logging"]) == pytest.approx(2 / 3)
    assert ev.keyword_coverage("RETRIES", ["retries"]) == 1.0
    assert ev.keyword_coverage("anything", []) == 1.0 and ev.keyword_coverage(None, ["x"]) == 0.0


def _ret(scores_by_q):
    def f(q, k=5, where=None):
        return [{"document": "AI.pdf", "page": 4, "score": s} for s in scores_by_q[q]]
    return f


def test_run_eval_judges_answerable_and_unanswerable(csv_path):
    rows = ev.load_questions(csv_path)
    ret = _ret({"What is a perceptron?": [0.6], "Capital of Peru?": [0.05], "Attendance rule?": [0.4]})

    def ans(q, mode, sel):
        if q == "What is a perceptron?":
            return {"answer": "A neuron with weights (AI.pdf, p.4)", "sources": [{"document": "AI.pdf", "page": 4, "snippet": ""}]}
        if q == "Capital of Peru?":
            return {"answer": NOT_FOUND + " Try rephrasing.", "sources": []}
        return {"answer": NOT_FOUND, "sources": []}  # wrongly says not found

    res = ev.run_eval(rows, ret, ans)
    assert [r["correct"] for r in res] == [True, True, False]
    assert res[0]["retrieval_hit"] is True and res[0]["cited_ok"] is True
    assert "not found" in res[2]["why"]


def test_unanswerable_question_that_gets_an_answer_is_a_failure(csv_path):
    rows = ev.load_questions(csv_path)[1:2]
    res = ev.run_eval(rows, _ret({"Capital of Peru?": [0.3]}), lambda q, m, s: {"answer": "Lima", "sources": []})
    assert res[0]["correct"] is False and "cannot answer" in res[0]["why"]


def test_low_keyword_coverage_fails(csv_path):
    rows = ev.load_questions(csv_path)[:1]
    res = ev.run_eval(rows, _ret({"What is a perceptron?": [0.6]}),
                      lambda q, m, s: {"answer": "Something unrelated", "sources": [{"document": "AI.pdf", "page": 4, "snippet": ""}]})
    assert res[0]["correct"] is False and res[0]["coverage"] == 0.0


def test_retrieval_only_makes_no_answer_calls(csv_path):
    rows = ev.load_questions(csv_path)
    ret = _ret({"What is a perceptron?": [0.6], "Capital of Peru?": [0.05], "Attendance rule?": [0.4]})
    res = ev.run_eval(rows, ret, answer_fn=None)
    assert all(r["answer"] is None and r["correct"] is None for r in res)
    assert res[0]["retrieval_hit"] is True and res[1]["retrieval_hit"] is None


def test_sweep_threshold_finds_separating_value():
    results = [{"top_score": s, "answerable": a} for s, a in
               [(0.50, True), (0.31, True), (0.24, True), (0.09, False), (0.07, False), (0.12, False)]]
    best = ev.sweep_threshold(results)
    assert best[0][1] == 1.0 and 0.13 <= best[0][0] <= 0.24
    assert dict(best)[0.45] < 1.0  # too strict loses answerable questions


def test_summarize():
    results = [
        {"answerable": True, "top_score": 0.5, "retrieval_hit": True, "correct": True, "cited_ok": True},
        {"answerable": True, "top_score": 0.3, "retrieval_hit": False, "correct": False, "cited_ok": False},
        {"answerable": False, "top_score": 0.08, "retrieval_hit": None, "correct": True, "cited_ok": None},
    ]
    s = ev.summarize(results)
    assert s["retrieval_hit_rate"] == 0.5 and s["accuracy"] == pytest.approx(2 / 3) and s["citation_rate"] == 0.5
    assert s["answerable_top_score_min"] == 0.3 and s["unanswerable_top_score_max"] == 0.08


def test_gemini_service_errors_are_not_scored(csv_path):
    from src.backend.gemini_client import _MESSAGES
    rows = ev.load_questions(csv_path)[:2]
    ret = _ret({"What is a perceptron?": [0.6], "Capital of Peru?": [0.3]})
    busy = {"answer": _MESSAGES["rate_limit"], "sources": []}
    res = ev.run_eval(rows, ret, lambda q, m, s: busy)
    assert all(r["error"] and r["correct"] is None for r in res)
    s = ev.summarize(res)
    assert s["errors"] == 2 and s["accuracy"] is None


def test_errors_do_not_dilute_accuracy_of_scored_questions(csv_path):
    from src.backend.gemini_client import _MESSAGES
    rows = ev.load_questions(csv_path)[:2]
    ret = _ret({"What is a perceptron?": [0.6], "Capital of Peru?": [0.05]})

    def ans(q, m, s):
        if q == "What is a perceptron?":
            return {"answer": _MESSAGES["timeout"], "sources": []}
        return {"answer": NOT_FOUND, "sources": []}

    s = ev.summarize(ev.run_eval(rows, ret, ans))
    assert s["errors"] == 1 and s["accuracy"] == 1.0
