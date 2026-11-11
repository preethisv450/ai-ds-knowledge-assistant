from src.backend import rag
from src.backend.gemini_client import GeminiError

RESULTS = [
    {"document": "AI.pdf", "page": 4, "snippet": "A perceptron...", "score": 0.6, "chunk_id": "a", "text": "A perceptron computes y."},
    {"document": "AI.pdf", "page": 5, "snippet": "Backprop...", "score": 0.4, "chunk_id": "b", "text": "Backpropagation uses the chain rule."},
]


def fake_retrieve(q, k=5):
    return RESULTS[:k]


def test_answer_returns_ui_contract_shape():
    r = rag.answer("What is a perceptron?", "Syllabus", None, retrieve_fn=fake_retrieve, generate_fn=lambda p, system=None: "It computes y. (AI.pdf, p.4)")
    assert set(r) == {"answer", "sources"}
    assert r["answer"].startswith("It computes y")
    assert [s["page"] for s in r["sources"]] == [4, 5]
    assert all(set(s) == {"document", "page", "snippet"} for s in r["sources"])


def test_prompt_given_to_gemini_contains_question_and_retrieved_text():
    seen = {}

    def gen(prompt, system=None):
        seen["prompt"], seen["system"] = prompt, system
        return "ok"

    rag.answer("What is a perceptron?", "Regulation", None, retrieve_fn=fake_retrieve, generate_fn=gen)
    assert "What is a perceptron?" in seen["prompt"] and "A perceptron computes y." in seen["prompt"]
    assert "AI.pdf, page 4" in seen["prompt"] and "regulations" in seen["system"]


def test_k_is_passed_to_retrieval():
    got = {}

    def ret(q, k=5):
        got["k"] = k
        return RESULTS

    rag.answer("q", k=2, retrieve_fn=ret, generate_fn=lambda p, system=None: "ok")
    assert got["k"] == 2


def test_gemini_failure_becomes_friendly_answer_not_exception():
    def boom(p, system=None):
        raise GeminiError("rate_limit", "The AI service is busy right now.")

    r = rag.answer("q", retrieve_fn=fake_retrieve, generate_fn=boom)
    assert r == {"answer": "The AI service is busy right now.", "sources": []}


def test_missing_index_becomes_friendly_answer():
    def no_index(q, k=5):
        raise FileNotFoundError("No index")

    r = rag.answer("q", retrieve_fn=no_index, generate_fn=lambda p, system=None: "x")
    assert "build_index" in r["answer"] and r["sources"] == []


def test_empty_question_does_not_call_anything():
    def fail(*a, **k):
        raise AssertionError("should not be called")

    for q in ("", "   ", None):
        assert rag.answer(q, retrieve_fn=fail, generate_fn=fail)["sources"] == []


def test_ui_get_answer_delegates_to_backend(monkeypatch):
    from src.ui import answer_service
    monkeypatch.setattr(rag, "answer", lambda q, m, s: {"answer": f"{q}|{m}|{s}", "sources": []})
    assert answer_service.get_answer("hi", "Syllabus", {"x": 1})["answer"] == "hi|Syllabus|{'x': 1}"
