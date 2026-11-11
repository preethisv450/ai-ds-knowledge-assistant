import pymupdf
import pytest

from src.backend.ingest import (
    CHUNK_WORDS, MIN_CHUNK_WORDS, _clean, chunk_pdf, chunk_words, extract_pages,
)

SENTENCE = "Machine learning is the study of algorithms that improve with experience. "


@pytest.fixture
def sample_pdf(tmp_path):
    """3 text pages with a blank page in the middle (page 2)."""
    doc = pymupdf.open()
    for i in (1, 2, 3):
        page = doc.new_page()
        if i != 2:
            page.insert_textbox(pymupdf.Rect(50, 50, 550, 780), f"Unit {i}\n\n" + SENTENCE * 40, fontsize=10)
    path = tmp_path / "sample.pdf"
    doc.save(path)
    return path


def test_extract_keeps_real_page_numbers_and_skips_blank(sample_pdf):
    pages = extract_pages(sample_pdf)
    assert [n for n, _ in pages] == [1, 3]  # blank page 2 skipped, numbering not shifted
    assert "Unit 3" in pages[1][1]


def test_chunks_have_required_fields(sample_pdf):
    chunks = chunk_pdf(sample_pdf)
    assert chunks
    for c in chunks:
        assert set(c) == {"document", "page", "chunk_id", "text"}
        assert c["document"] == "sample.pdf"


def test_chunks_never_cross_pages_and_stay_under_size_limit(sample_pdf):
    chunks = chunk_pdf(sample_pdf)
    assert {c["page"] for c in chunks} == {1, 3}
    assert all(len(c["text"].split()) <= CHUNK_WORDS for c in chunks)
    assert all(len(c["text"].split()) >= MIN_CHUNK_WORDS for c in chunks)


def test_chunk_ids_are_unique(sample_pdf):
    ids = [c["chunk_id"] for c in chunk_pdf(sample_pdf)]
    assert len(ids) == len(set(ids))


def test_overlap_between_consecutive_chunks():
    words = [f"w{i}" for i in range(400)]
    parts = list(chunk_words(words, size=100, overlap=20))
    assert parts[0][-20:] == parts[1][:20]
    assert parts[-1][-1] == "w399"  # nothing lost at the end
    assert sum(len(p) for p in parts) >= 400


def test_short_text_gives_one_chunk():
    assert len(list(chunk_words(["a"] * 10, size=100, overlap=20))) == 1


def test_clean_keeps_hyphenated_compounds_across_line_breaks():
    assert "sentence-transformers" in _clean("uses sentence-\ntransformers for embeddings")
    assert "\u00ad" not in _clean("soft\u00adhyphen")
