"""D3: embeddings + FAISS index that saves to disk and reloads.

Vectors are L2-normalised and stored in an inner-product index, so the score FAISS
returns is cosine similarity (1.0 = identical). Row i of the index is chunks[i].
"""
import json
import threading
from pathlib import Path

import faiss
import numpy as np

from src.backend.config import EMBEDDING_MODEL, INDEX_DIR, PDF_DIR
from src.backend.catalog import classify, load_manifest
from src.backend.ingest import chunk_pdf

INDEX_FILE = "faiss.index"
CHUNKS_FILE = "chunks.json"
META_FILE = "meta.json"

_model = None
_model_lock = threading.Lock()


def _get_model():
    global _model
    with _model_lock:  # D16: the warm-up thread and the first request must not both load it
        if _model is None:  # load once; it takes a few seconds
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_texts(texts, embed_fn=None):
    """Return a float32 array (n, dim) of normalised embeddings. embed_fn is for tests."""
    if embed_fn is None:
        vecs = _get_model().encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    else:
        vecs = embed_fn(texts)
    vecs = np.asarray(vecs, dtype="float32")
    faiss.normalize_L2(vecs)  # no-op for already-normalised vectors, makes fakes safe too
    return vecs


def build_index(chunks, embed_fn=None):
    if not chunks:
        raise ValueError("No chunks to index. Put PDFs in data/pdfs/ first.")
    vecs = embed_texts([c["text"] for c in chunks], embed_fn)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    return index


def save_index(index, chunks, index_dir=INDEX_DIR):
    d = Path(index_dir)
    d.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(d / INDEX_FILE))
    (d / CHUNKS_FILE).write_text(json.dumps(chunks, ensure_ascii=False))
    (d / META_FILE).write_text(json.dumps(
        {"model": EMBEDDING_MODEL, "dim": index.d, "count": index.ntotal}))


def load_index(index_dir=INDEX_DIR):
    """Return (index, chunks). Raises a clear error if the files are missing or inconsistent."""
    d = Path(index_dir)
    if not (d / INDEX_FILE).exists():
        raise FileNotFoundError(f"No index in {d}. Run: python scripts/build_index.py")
    index = faiss.read_index(str(d / INDEX_FILE))
    chunks = json.loads((d / CHUNKS_FILE).read_text())
    meta = json.loads((d / META_FILE).read_text())
    if meta["model"] != EMBEDDING_MODEL:
        raise RuntimeError(f"Index was built with {meta['model']} but config uses {EMBEDDING_MODEL}. Rebuild it.")
    if index.ntotal != len(chunks):
        raise RuntimeError("Index and chunks.json are out of sync. Rebuild the index.")
    return index, chunks


def build_from_pdfs(pdf_dir=PDF_DIR, index_dir=INDEX_DIR, embed_fn=None, manifest=None):
    pdfs = sorted(Path(pdf_dir).glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDFs found in {pdf_dir}")
    manifest = load_manifest() if manifest is None else manifest
    chunks = []
    for pdf in pdfs:
        for c in chunk_pdf(pdf):
            c.update(classify(c["document"], c["page"], manifest))
            chunks.append(c)
    index = build_index(chunks, embed_fn)
    save_index(index, chunks, index_dir)
    return index, chunks
