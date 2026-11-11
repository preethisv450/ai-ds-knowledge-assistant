"""Build the vector index from data/pdfs/*.pdf, save it, reload it and sanity-check it.
Run from the repo root: python scripts/build_index.py"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.vector_store import build_from_pdfs, embed_texts, load_index
from src.backend.config import INDEX_DIR, PDF_DIR

t = time.time()
index, chunks = build_from_pdfs()
docs = sorted({c["document"] for c in chunks})
print(f"Built index: {index.ntotal} chunks from {len(docs)} PDFs in {time.time()-t:.1f}s -> {INDEX_DIR}")

print("\nHow each document was labelled (this decides what Syllabus / Regulation mode can search):")
seen = {}
for c in chunks:
    seen.setdefault(c["document"], c)
for doc, c in sorted(seen.items()):
    mods = sorted({x["module_id"] for x in chunks if x["document"] == doc and x["module_id"]})
    print(f"  {doc}: {c['doc_type']}" + (f", subject {c['subject_code']}" if c["subject_code"] else "")
          + (f", modules {', '.join(mods)}" if mods else ""))
if not any(c["doc_type"] in ("syllabus", "regulation") for c in chunks):
    print("  -> No syllabus/regulation documents recognised, so scoping is OFF (dev mode). See docs/data_manifest.md")
elif any(c["doc_type"] == "other" for c in chunks):
    print("  -> Documents labelled 'other' are never searched. Rename them or list them in documents.json (docs/data_manifest.md)")
print()

index2, chunks2 = load_index()
assert index2.ntotal == index.ntotal == len(chunks2), "reload mismatch"
print(f"Reloaded OK: {index2.ntotal} vectors, dim {index2.d}")

# Sanity check: each chunk, used as its own query, should find itself first.
sample = chunks2[:: max(len(chunks2) // 5, 1)][:5]
scores, ids = index2.search(embed_texts([c["text"] for c in sample]), 1)
ok = sum(chunks2[i[0]]["chunk_id"] == c["chunk_id"] for i, c in zip(ids, sample))
print(f"Self-retrieval check: {ok}/{len(sample)} chunks found themselves at rank 1")
sys.exit(0 if ok == len(sample) else 1)
