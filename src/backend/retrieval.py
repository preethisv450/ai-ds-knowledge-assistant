"""D4: retrieve(query, k) -> top-k chunks with file, page, snippet and similarity score.

Scores are cosine similarity (1.0 = identical meaning, ~0 = unrelated). The index is
loaded once and cached, so repeated calls from the UI are fast.
"""
import threading
from pathlib import Path

from src.backend.config import INDEX_DIR, TOP_K
from src.backend.vector_store import embed_texts, load_index

SNIPPET_CHARS = 300
_cache = {}
_lock = threading.Lock()


def _load(index_dir):
    key = str(Path(index_dir).resolve())
    with _lock:
        if key not in _cache:
            _cache[key] = load_index(index_dir)
        return _cache[key]


def clear_cache():
    _cache.clear()


def _snippet(text, n=SNIPPET_CHARS):
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "..."


def _has_classified(chunks):
    return any(c.get("doc_type") in ("syllabus", "regulation") for c in chunks)


def retrieve(query, k=TOP_K, index_dir=INDEX_DIR, embed_fn=None, where=None):
    """Return up to k results, best first:
    {"document", "page", "snippet", "score", "chunk_id", "text"}

    where: optional predicate on a chunk dict (see catalog.make_filter). It is ignored while
    the index has no labelled documents at all (dev mode before real data / a manifest exists)."""
    if not query or not query.strip():
        raise ValueError("Query is empty.")
    index, chunks = _load(index_dir)
    filt = where if (where and _has_classified(chunks)) else None
    n = index.ntotal
    # A flat index is exact and fast, so with a filter we rank everything and keep the first k that pass.
    scores, ids = index.search(embed_texts([query.strip()], embed_fn), n if filt else max(1, min(k, n)))
    results = []
    for score, i in zip(scores[0], ids[0]):
        if i < 0:  # FAISS pads with -1 when it has fewer results than asked for
            continue
        c = chunks[i]
        if filt and not filt(c):
            continue
        results.append({
            "document": c["document"],
            "page": c["page"],
            "snippet": _snippet(c["text"]),
            "score": round(float(score), 4),
            "chunk_id": c["chunk_id"],
            "text": c["text"],
        })
        if len(results) >= k:
            break
    return results


def to_sources(results):
    """Shape results for the UI's get_answer() 'sources' field."""
    return [{"document": r["document"], "page": r["page"], "snippet": r["snippet"]} for r in results]
