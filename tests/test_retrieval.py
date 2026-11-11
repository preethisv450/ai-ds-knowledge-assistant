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
