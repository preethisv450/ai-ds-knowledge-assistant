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
    assert [s["page"] for s in r["sources"]] == [4]  # D7: only the page the answer cites
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


# ---- D7: citations and not-found fallback ----
from src.backend.rag import NOT_FOUND_MSG, parse_citations, select_sources


def _r(doc, page, score):
    return {"document": doc, "page": page, "snippet": "s", "score": score, "chunk_id": f"{doc}{page}", "text": f"text {doc} {page}"}


def test_low_top_score_returns_not_found_without_calling_gemini():
    def fail(*a, **k):
        raise AssertionError("Gemini must not be called")

    r = rag.answer("capital of Peru?", retrieve_fn=lambda q, k=5: [_r("A.pdf", 1, 0.05)], generate_fn=fail)
    assert r == {"answer": NOT_FOUND_MSG, "sources": []}


def test_weak_chunks_are_dropped_from_the_prompt():
    seen = {}

    def gen(prompt, system=None):
        seen["prompt"] = prompt
        return "ok (A.pdf, p.1)"

    rag.answer("q", retrieve_fn=lambda q, k=5: [_r("A.pdf", 1, 0.5), _r("B.pdf", 2, 0.05)], generate_fn=gen)
    assert "A.pdf, page 1" in seen["prompt"] and "B.pdf" not in seen["prompt"]


def test_threshold_is_inclusive_and_overridable():
    res = lambda q, k=5: [_r("A.pdf", 1, 0.20)]
    assert rag.answer("q", retrieve_fn=res, generate_fn=lambda p, system=None: "yes (A.pdf, p.1)")["answer"].startswith("yes")
    assert rag.answer("q", min_score=0.5, retrieve_fn=res, generate_fn=lambda p, system=None: "x")["answer"] == NOT_FOUND_MSG


def test_model_not_found_reply_returns_not_found_and_no_sources():
    from src.backend.prompts import NOT_FOUND
    r = rag.answer("q", retrieve_fn=lambda q, k=5: [_r("A.pdf", 1, 0.5)], generate_fn=lambda p, system=None: NOT_FOUND + " whatever")
    assert r == {"answer": NOT_FOUND_MSG, "sources": []}


def test_only_cited_pages_are_returned_as_sources():
    chunks = [_r("A.pdf", 1, 0.9), _r("A.pdf", 2, 0.8), _r("B.pdf", 7, 0.7)]
    r = rag.answer("q", retrieve_fn=lambda q, k=5: chunks, generate_fn=lambda p, system=None: "Fact one (A.pdf, p.2). Fact two (B.pdf, page 7).")
    assert [(s["document"], s["page"]) for s in r["sources"]] == [("A.pdf", 2), ("B.pdf", 7)]


def test_uncited_or_hallucinated_citations_fall_back_to_pages_given():
    chunks = [_r("A.pdf", 1, 0.9), _r("A.pdf", 2, 0.8)]
    for text in ("no citation at all", "made up (Z.pdf, p.99)"):
        r = rag.answer("q", retrieve_fn=lambda q, k=5: chunks, generate_fn=lambda p, system=None, t=text: t)
        assert [s["page"] for s in r["sources"]] == [1, 2]


def test_sources_deduplicated_by_page():
    chunks = [_r("A.pdf", 1, 0.9), _r("A.pdf", 1, 0.8), _r("A.pdf", 3, 0.7)]
    r = rag.answer("q", retrieve_fn=lambda q, k=5: chunks, generate_fn=lambda p, system=None: "x")
    assert [s["page"] for s in r["sources"]] == [1, 3]


def test_parse_citation_formats():
    assert parse_citations("x (AI.pdf, p.3)") == {("ai.pdf", 3)}
    assert parse_citations("x (AI.pdf, page 3)") == {("ai.pdf", 3)}
    assert parse_citations("x (AI.pdf, p.3, 5)") == {("ai.pdf", 3), ("ai.pdf", 5)}
    assert parse_citations("x (A.pdf, p.1; B.pdf, p.2)") == {("a.pdf", 1), ("b.pdf", 2)}
    assert parse_citations("(My_File-v2.pdf, pp. 4)") == {("my_file-v2.pdf", 4)}
    assert parse_citations("no citations here (see above)") == set()
    assert parse_citations(None) == set()


def test_answer_prompt_has_citation_rules():
    from src.backend.prompts import answer_prompt
    system, _ = answer_prompt("q", [_r("A.pdf", 1, 0.5) | {"text": "t"}])
    assert "(file.pdf, p.3)" in system and "Only cite pages" in system and "do not guess" in system
