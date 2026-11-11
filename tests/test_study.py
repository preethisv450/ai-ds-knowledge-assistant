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
