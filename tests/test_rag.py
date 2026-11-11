from src.backend import rag
from src.backend.gemini_client import GeminiError

RESULTS = [
    {"document": "AI.pdf", "page": 4, "snippet": "A perceptron...", "score": 0.6, "chunk_id": "a", "text": "A perceptron computes y."},
    {"document": "AI.pdf", "page": 5, "snippet": "Backprop...", "score": 0.4, "chunk_id": "b", "text": "Backpropagation uses the chain rule."},
]


def fake_retrieve(q, k=5, where=None):
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

    def ret(q, k=5, where=None):
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
    def no_index(q, k=5, where=None):
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

    r = rag.answer("capital of Peru?", retrieve_fn=lambda q, k=5, where=None: [_r("A.pdf", 1, 0.05)], generate_fn=fail)
    assert r == {"answer": NOT_FOUND_MSG, "sources": []}


def test_weak_chunks_are_dropped_from_the_prompt():
    seen = {}

    def gen(prompt, system=None):
        seen["prompt"] = prompt
        return "ok (A.pdf, p.1)"

    rag.answer("q", retrieve_fn=lambda q, k=5, where=None: [_r("A.pdf", 1, 0.5), _r("B.pdf", 2, 0.05)], generate_fn=gen)
    assert "A.pdf, page 1" in seen["prompt"] and "B.pdf" not in seen["prompt"]


def test_threshold_is_inclusive_and_overridable():
    res = lambda q, k=5, where=None: [_r("A.pdf", 1, 0.20)]
    assert rag.answer("q", retrieve_fn=res, generate_fn=lambda p, system=None: "yes (A.pdf, p.1)")["answer"].startswith("yes")
    assert rag.answer("q", min_score=0.5, retrieve_fn=res, generate_fn=lambda p, system=None: "x")["answer"] == NOT_FOUND_MSG


def test_model_not_found_reply_returns_not_found_and_no_sources():
    from src.backend.prompts import NOT_FOUND
    r = rag.answer("q", retrieve_fn=lambda q, k=5, where=None: [_r("A.pdf", 1, 0.5)], generate_fn=lambda p, system=None: NOT_FOUND + " whatever")
    assert r == {"answer": NOT_FOUND_MSG, "sources": []}


def test_only_cited_pages_are_returned_as_sources():
    chunks = [_r("A.pdf", 1, 0.9), _r("A.pdf", 2, 0.8), _r("B.pdf", 7, 0.7)]
    r = rag.answer("q", retrieve_fn=lambda q, k=5, where=None: chunks, generate_fn=lambda p, system=None: "Fact one (A.pdf, p.2). Fact two (B.pdf, page 7).")
    assert [(s["document"], s["page"]) for s in r["sources"]] == [("A.pdf", 2), ("B.pdf", 7)]


def test_uncited_or_hallucinated_citations_fall_back_to_pages_given():
    chunks = [_r("A.pdf", 1, 0.9), _r("A.pdf", 2, 0.8)]
    for text in ("no citation at all", "made up (Z.pdf, p.99)"):
        r = rag.answer("q", retrieve_fn=lambda q, k=5, where=None: chunks, generate_fn=lambda p, system=None, t=text: t)
        assert [s["page"] for s in r["sources"]] == [1, 2]


def test_sources_deduplicated_by_page():
    chunks = [_r("A.pdf", 1, 0.9), _r("A.pdf", 1, 0.8), _r("A.pdf", 3, 0.7)]
    r = rag.answer("q", retrieve_fn=lambda q, k=5, where=None: chunks, generate_fn=lambda p, system=None: "x")
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
    assert "[S2]" in system and "Use only markers" in system and "do not guess" in system
    assert "Never write file names or page numbers" in system


# ---- D8: scoping ----
def test_rag_passes_a_scope_filter_to_retrieval():
    from src.backend.catalog import make_filter
    got = {}

    def ret(q, k=5, where=None):
        got["where"] = where
        return [_r("A.pdf", 1, 0.5)]

    sel = {"subject": "AI", "module": "NN", "subject_code": "AI201", "module_id": "AI201-M1"}
    rag.answer("q", "Syllabus", sel, retrieve_fn=ret, generate_fn=lambda p, system=None: "ok")
    f = got["where"]
    assert f({"doc_type": "syllabus", "subject_code": "AI201", "module_id": "AI201-M1"})
    assert not f({"doc_type": "regulation"})
    rag.answer("q", "Regulation", sel, retrieve_fn=ret, generate_fn=lambda p, system=None: "ok")
    assert got["where"]({"doc_type": "regulation"}) and not got["where"]({"doc_type": "syllabus", "subject_code": "AI201"})


def test_empty_scope_gives_specific_no_documents_message():
    sel = {"subject": "Machine Learning", "module": "Regression", "subject_code": "DS202", "module_id": "DS202-M1"}

    def fail(*a, **k):
        raise AssertionError("Gemini must not be called")

    r = rag.answer("q", "Syllabus", sel, retrieve_fn=lambda q, k=5, where=None: [], generate_fn=fail)
    assert "Machine Learning" in r["answer"] and "No documents" in r["answer"] and r["sources"] == []
    r = rag.answer("q", "Regulation", None, retrieve_fn=lambda q, k=5, where=None: [], generate_fn=fail)
    assert "regulations" in r["answer"]


def test_selected_module_is_named_in_the_prompt():
    seen = {}

    def gen(prompt, system=None):
        seen["system"] = system
        return "ok"

    sel = {"subject": "Machine Learning", "module": "Regression"}
    rag.answer("q", "Syllabus", sel, retrieve_fn=lambda q, k=5, where=None: [_r("A.pdf", 1, 0.5)], generate_fn=gen)
    assert "Machine Learning — Regression" in seen["system"]


# ---- marker citations ([S2] -> real file and page) ----
from src.backend.rag import render_citations


def _chunks3():
    return [_r("A.pdf", 1, 0.9), _r("A.pdf", 7, 0.8), _r("B.pdf", 3, 0.7)]


def test_markers_become_file_and_page_and_select_sources():
    r = rag.answer("q", retrieve_fn=lambda q, k=5, where=None: _chunks3(),
                   generate_fn=lambda p, system=None: "Fact one [S2]. Fact two [S3].")
    assert r["answer"] == "Fact one (A.pdf, p.7). Fact two (B.pdf, p.3)."
    assert [(s["document"], s["page"]) for s in r["sources"]] == [("A.pdf", 7), ("B.pdf", 3)]


def test_multiple_markers_merge_and_duplicate_pages_collapse():
    out = render_citations("Both facts [S1][S3] and again [S1, S1].", _chunks3())
    assert out == "Both facts (A.pdf, p.1; B.pdf, p.3) and again (A.pdf, p.1)."


def test_markers_pointing_at_nothing_are_removed_and_fall_back_to_all_pages():
    r = rag.answer("q", retrieve_fn=lambda q, k=5, where=None: _chunks3(),
                   generate_fn=lambda p, system=None: "Invented source [S9].")
    assert r["answer"] == "Invented source." and [s["page"] for s in r["sources"]] == [1, 7, 3]


def test_code_like_brackets_are_left_alone():
    text = "Use arr[1] and matrix[2][3], not citations."
    assert render_citations(text, _chunks3()) == text


def test_legacy_file_page_citations_still_work_when_no_markers():
    r = rag.answer("q", retrieve_fn=lambda q, k=5, where=None: _chunks3(),
                   generate_fn=lambda p, system=None: "Fact (B.pdf, p.3).")
    assert [s["page"] for s in r["sources"]] == [3] and r["answer"] == "Fact (B.pdf, p.3)."


def test_context_labels_use_s_markers():
    from src.backend.prompts import format_context
    ctx = format_context([{"document": "A.pdf", "page": 2, "text": "t"}])
    assert ctx.startswith("[S1] (Source: A.pdf, page 2)")
