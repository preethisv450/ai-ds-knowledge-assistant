"""D2: PDF extraction (page-aware) and chunking.

Chunks never span pages, so every chunk has exactly one page number. That keeps
citations simple and correct. Sizes are in words: the embedding model
(all-MiniLM-L6-v2) only reads ~256 word-pieces, so chunks must stay below that
or the tail is silently ignored. ~180 words is roughly 230 word-pieces.
"""
import re
from pathlib import Path

import pymupdf

CHUNK_WORDS = 180
OVERLAP_WORDS = 30
MIN_CHUNK_WORDS = 15  # drop page-number-only / near-empty fragments


def extract_pages(pdf_path):
    """Return [(page_number starting at 1, cleaned_text), ...]; skips blank pages."""
    pages = []
    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            text = _clean(page.get_text("text"))
            if text:
                pages.append((i, text))
    return pages


def _clean(text):
    text = text.replace("­", "")              # soft hyphens
    text = re.sub(r"-\n(?=[a-z])", "-", text)       # keep hyphen: real compounds (data-driven) must survive
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_words(words, size=CHUNK_WORDS, overlap=OVERLAP_WORDS):
    step = max(size - overlap, 1)
    for start in range(0, len(words), step):
        yield words[start:start + size]
        if start + size >= len(words):
            break


def chunk_pdf(pdf_path, size=CHUNK_WORDS, overlap=OVERLAP_WORDS):
    """Return a list of {"document", "page", "chunk_id", "text"} dicts."""
    name = Path(pdf_path).name
    chunks = []
    for page_no, text in extract_pages(pdf_path):
        words = text.split()
        for part in chunk_words(words, size, overlap):
            if len(part) < MIN_CHUNK_WORDS and chunks and chunks[-1]["page"] == page_no:
                continue  # tiny tail already covered by the previous chunk's overlap
            if len(part) < MIN_CHUNK_WORDS and len(words) >= MIN_CHUNK_WORDS:
                continue
            chunks.append({
                "document": name,
                "page": page_no,
                "chunk_id": f"{name}:p{page_no}:{len(chunks)}",
                "text": " ".join(part),
            })
    return chunks
