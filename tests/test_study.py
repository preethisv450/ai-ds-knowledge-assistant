from src.backend import study
from src.backend.gemini_client import GeminiError

SEL = {"subject": "AI", "subject_code": "AI201", "module": "Neural Nets", "module_id": "AI201-M1"}
R = [
    {"document": "AI.pdf", "page": 4, "snippet": "s", "score": 0.5, "chunk_id": "a", "text": "A perceptron computes y."},
    {"document": "AI.pdf", "page": 6, "snippet": "s", "score": 0.4, "chunk_id": "b", "text": "Backprop uses the chain rule."},
    {"document": "AI.pdf", "page": 9, "snippet": "s", "score": 0.05, "chunk_id": "c", "text": "unrelated"},
]


def ret(q, k=5, where=None):
    ret.q = q
    return R[:k]


def test_summary_has_text_and_cited_sources_only():
    r = study.generate_summary(SEL, retrieve_fn=ret, generate_fn=lambda p, system=None: "- Perceptron computes y [S1]\n- Chain rule [S2]")
    assert set(r) == {"summary", "sources"}
    assert "(AI.pdf, p.4)" in r["summary"] and "[S" not in r["summary"]
    assert [s["page"] for s in r["sources"]] == [4, 6]
    assert ret.q == "AI Neural Nets"


def test_weak_chunks_are_not_sent_to_gemini():
    seen = {}

    def gen(p, system=None):
        seen["p"] = p
        return "- ok [S1]"

    study.generate_summary(SEL, retrieve_fn=ret, generate_fn=gen)
    assert "unrelated" not in seen["p"] and "A perceptron computes y." in seen["p"]


def test_needs_a_module():
    r = study.generate_summary({"subject": "AI"}, retrieve_fn=ret, generate_fn=lambda *a, **k: "x")
    assert r["summary"] == study.NEED_MODULE_MSG and r["sources"] == []


def test_nothing_relevant_skips_gemini():
    def boom(*a, **k):
        raise AssertionError("must not call Gemini")
    low = lambda q, k=5, where=None: [dict(R[0], score=0.01)]
    assert study.generate_summary(SEL, retrieve_fn=low, generate_fn=boom)["summary"] == study.NOT_FOUND_MSG


def test_empty_scope_and_missing_index():
    assert "No documents" in study.generate_summary(SEL, retrieve_fn=lambda q, k=5, where=None: [], generate_fn=None)["summary"]

    def missing(q, k=5, where=None):
        raise FileNotFoundError
    assert "not been built" in study.generate_summary(SEL, retrieve_fn=missing)["summary"]


def test_model_not_found_and_gemini_error_become_messages():
    nf = study.generate_summary(SEL, retrieve_fn=ret, generate_fn=lambda p, system=None: "I could not find this in the documents.")
    assert nf["summary"] == study.NOT_FOUND_MSG and nf["sources"] == []

    def bad(p, system=None):
        raise GeminiError("busy", "Gemini is busy, try again.")
    e = study.generate_summary(SEL, retrieve_fn=ret, generate_fn=bad)
    assert e == {"summary": "Gemini is busy, try again.", "sources": []}


# ---- D12: practice questions ----
def _gj(items):
    return lambda prompt, system=None, validate=None, **kw: (validate(items), items)[1]


GOOD = [{"question": "What is a perceptron?", "model_answer": "A unit that computes y."},
        {"question": "State the chain rule.", "model_answer": "d/dx f(g(x))."}]


def test_questions_shape_and_n_limit():
    r = study.generate_questions(SEL, "Short answer", 1, retrieve_fn=ret, generate_json_fn=_gj(GOOD))
    assert set(r) == {"questions", "message", "sources"} and r["message"] == ""
    assert r["questions"] == [GOOD[0]]
    assert {s["page"] for s in r["sources"]} == {4, 6}


def test_qtype_and_n_reach_the_prompt_and_n_is_clamped():
    seen = {}

    def gj(prompt, system=None, validate=None, **kw):
        seen["p"] = prompt
        return GOOD

    study.generate_questions(SEL, "Long answer", 99, retrieve_fn=ret, generate_json_fn=gj)
    assert "Write 20 long-answer" in seen["p"]
    study.generate_questions(SEL, "Short answer", "abc", retrieve_fn=ret, generate_json_fn=gj)
    assert "Write 5 short-answer" in seen["p"]
    assert study.normalize_qtype("Long answer") == "long" and study.normalize_qtype(None) == "short"


def test_questions_problems_become_messages_not_errors():
    assert study.generate_questions({"subject": "AI"}, retrieve_fn=ret)["message"] == study.NEED_MODULE_MSG

    def bad(prompt, system=None, validate=None, **kw):
        raise GeminiError("empty", "Gemini returned nothing, try again.")
    r = study.generate_questions(SEL, retrieve_fn=ret, generate_json_fn=bad)
    assert r == {"questions": [], "message": "Gemini returned nothing, try again.", "sources": []}

    low = lambda q, k=5, where=None: [dict(R[0], score=0.01)]
    assert study.generate_questions(SEL, retrieve_fn=low)["questions"] == []


def test_malformed_model_json_is_rejected_by_validator():
    import pytest
    from src.backend.prompts import validate_questions
    with pytest.raises(ValueError):
        validate_questions([{"question": "Q"}])
