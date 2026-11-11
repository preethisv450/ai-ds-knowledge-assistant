import hashlib

import numpy as np
import pytest

from src.backend import vector_store as vs

DIM = 16


def fake_embed(texts):
    """Deterministic fake embedder: same text -> same vector, different text -> different."""
    out = []
    for t in texts:
        seed = int(hashlib.md5(t.encode()).hexdigest()[:8], 16)
        out.append(np.random.default_rng(seed).normal(size=DIM))
    return np.array(out)


CHUNKS = [{"document": "a.pdf", "page": i, "chunk_id": f"a.pdf:p{i}:{i}", "text": f"chunk number {i} about topic {i*7}"}
          for i in range(1, 8)]


def test_embeddings_are_normalised_float32():
    v = vs.embed_texts(["x", "y"], fake_embed)
    assert v.dtype == np.float32 and v.shape == (2, DIM)
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-5)


def test_build_index_has_one_vector_per_chunk():
    assert vs.build_index(CHUNKS, fake_embed).ntotal == len(CHUNKS)


def test_save_and_reload_roundtrip(tmp_path):
    index = vs.build_index(CHUNKS, fake_embed)
    vs.save_index(index, CHUNKS, tmp_path)
    index2, chunks2 = vs.load_index(tmp_path)
    assert index2.ntotal == index.ntotal and chunks2 == CHUNKS


def test_reloaded_index_finds_chunk_as_its_own_nearest_neighbour(tmp_path):
    vs.save_index(vs.build_index(CHUNKS, fake_embed), CHUNKS, tmp_path)
    index, chunks = vs.load_index(tmp_path)
    for c in CHUNKS:
        scores, ids = index.search(vs.embed_texts([c["text"]], fake_embed), 1)
        assert chunks[ids[0][0]]["chunk_id"] == c["chunk_id"]
        assert scores[0][0] == pytest.approx(1.0, abs=1e-4)


def test_empty_chunks_raise_clear_error():
    with pytest.raises(ValueError):
        vs.build_index([], fake_embed)


def test_load_missing_index_gives_helpful_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="build_index"):
        vs.load_index(tmp_path)


def test_load_rejects_index_built_with_other_model(tmp_path):
    vs.save_index(vs.build_index(CHUNKS, fake_embed), CHUNKS, tmp_path)
    meta = tmp_path / vs.META_FILE
    meta.write_text(meta.read_text().replace(vs.EMBEDDING_MODEL, "some/other-model"))
    with pytest.raises(RuntimeError, match="Rebuild"):
        vs.load_index(tmp_path)


def test_load_detects_out_of_sync_files(tmp_path):
    vs.save_index(vs.build_index(CHUNKS, fake_embed), CHUNKS, tmp_path)
    (tmp_path / vs.CHUNKS_FILE).write_text("[]")
    with pytest.raises(RuntimeError, match="out of sync"):
        vs.load_index(tmp_path)


def test_build_from_pdfs_end_to_end(tmp_path):
    import pymupdf
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(50, 50, 550, 780), "Gradient descent minimises a loss function. " * 30, fontsize=10)
    doc.save(pdf_dir / "ml.pdf")
    index, chunks = vs.build_from_pdfs(pdf_dir, tmp_path / "idx", fake_embed)
    assert index.ntotal == len(chunks) > 0
    index2, chunks2 = vs.load_index(tmp_path / "idx")
    assert chunks2[0]["document"] == "ml.pdf" and chunks2[0]["page"] == 1
