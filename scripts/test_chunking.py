"""Usage: python scripts/test_chunking.py data/pdfs/<file>.pdf"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.ingest import chunk_pdf

chunks = chunk_pdf(sys.argv[1])
pages = sorted({c["page"] for c in chunks})
sizes = [len(c["text"].split()) for c in chunks]
print(f"{len(chunks)} chunks from {len(pages)} pages (pages {pages[0]}-{pages[-1]})")
print(f"words per chunk: min {min(sizes)}, max {max(sizes)}, avg {sum(sizes)//len(sizes)}")
for c in chunks[:3]:
    print(f"\n[{c['chunk_id']}]\n{c['text'][:300]}...")
