import pytest

from src.backend import retrieval, vector_store as vs
from tests.test_vector_store import CHUNKS, fake_embed


@pytest.fixture
def idx(tmp_path):
    vs.save_index(vs.build_index(CHUNKS, fake_embed), CHUNKS, tmp_path)
    retrieval.clear_cache()
    return tmp_path


def test_exact_text_query_returns_that_chunk_first(idx):
    r = retrieval.retrieve(CHUNKS[3]["text"], k=3, index_dir=idx, embed_fn=fake_embed)
    assert r[0]["chunk_id"] == CHUNKS[3]["chunk_id"]
    assert r[0]["score"] == pytest.approx(1.0, abs=1e-3)


def test_results_have_fields_and_are_sorted_best_first(idx):
    r = retrieval.retrieve("anything", k=4, index_dir=idx, embed_fn=fake_embed)
    assert len(r) == 4
    assert set(r[0]) == {"document", "page", "snippet", "score", "chunk_id", "text"}
    scores = [x["score"] for x in r]
    assert scores == sorted(scores, reverse=True)


def test_k_larger_than_index_is_clamped(idx):
    r = retrieval.retrieve("x", k=999, index_dir=idx, embed_fn=fake_embed)
    assert len(r) == len(CHUNKS)


def test_empty_query_rejected(idx):
    for q in ("", "   "):
        with pytest.raises(ValueError):
            retrieval.retrieve(q, index_dir=idx, embed_fn=fake_embed)


def test_snippet_is_shortened_but_text_is_full():
    long = "word " * 200
    s = retrieval._snippet(long)
    assert len(s) <= retrieval.SNIPPET_CHARS + 3 and s.endswith("...")
    assert retrieval._snippet("short text") == "short text"


def test_to_sources_matches_ui_contract(idx):
    src = retrieval.to_sources(retrieval.retrieve("x", k=2, index_dir=idx, embed_fn=fake_embed))
    assert all(set(s) == {"document", "page", "snippet"} for s in src)
    assert isinstance(src[0]["page"], int)


def test_index_is_loaded_once_and_cached(idx):
    retrieval.retrieve("a", index_dir=idx, embed_fn=fake_embed)
    retrieval.retrieve("b", index_dir=idx, embed_fn=fake_embed)
    assert len(retrieval._cache) == 1


# ---- D8: scoped retrieval ----
from src.backend.catalog import make_filter


def _labelled_index(tmp_path):
    chunks = [
        {"document": "AI201_syl.pdf", "page": 1, "chunk_id": "a1", "text": "neural networks and perceptrons", "doc_type": "syllabus", "subject_code": "AI201", "module_id": "AI201-M1"},
        {"document": "AI201_syl.pdf", "page": 6, "chunk_id": "a2", "text": "search algorithms and heuristics", "doc_type": "syllabus", "subject_code": "AI201", "module_id": "AI201-M2"},
        {"document": "DS202_syl.pdf", "page": 1, "chunk_id": "d1", "text": "linear regression", "doc_type": "syllabus", "subject_code": "DS202", "module_id": None},
        {"document": "Regulations.pdf", "page": 3, "chunk_id": "r1", "text": "attendance must be at least 75 percent", "doc_type": "regulation", "subject_code": None, "module_id": None},
    ]
    vs.save_index(vs.build_index(chunks, fake_embed), chunks, tmp_path)
    retrieval.clear_cache()
    return tmp_path


def test_where_filter_limits_results_to_matching_chunks(tmp_path):
    idx = _labelled_index(tmp_path)
    r = retrieval.retrieve("attendance", k=5, index_dir=idx, embed_fn=fake_embed, where=make_filter("Regulation"))
    assert [x["chunk_id"] for x in r] == ["r1"]
    sel = {"subject_code": "AI201", "module_id": "AI201-M2"}
    r = retrieval.retrieve("anything", k=5, index_dir=idx, embed_fn=fake_embed, where=make_filter("Syllabus", sel))
    assert [x["chunk_id"] for x in r] == ["a2"]


def test_filter_still_returns_best_k_among_matches(tmp_path):
    idx = _labelled_index(tmp_path)
    r = retrieval.retrieve("search algorithms and heuristics", k=1, index_dir=idx, embed_fn=fake_embed,
                           where=make_filter("Syllabus", {"subject_code": "AI201"}))
    assert [x["chunk_id"] for x in r] == ["a2"] and r[0]["score"] == pytest.approx(1.0, abs=1e-3)


def test_filter_matching_nothing_returns_empty_list(tmp_path):
    idx = _labelled_index(tmp_path)
    r = retrieval.retrieve("x", index_dir=idx, embed_fn=fake_embed, where=make_filter("Syllabus", {"subject_code": "ZZ999"}))
    assert r == []


def test_filter_is_ignored_when_index_has_no_labelled_documents(idx):
    # the plain CHUNKS index has no doc_type labels (dev mode): filters must not hide everything
    r = retrieval.retrieve("x", k=3, index_dir=idx, embed_fn=fake_embed, where=make_filter("Regulation"))
    assert len(r) == 3
