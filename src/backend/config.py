"""Backend settings. Gemini key comes from Streamlit secrets (deployed) or .env (local)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

PDF_DIR = ROOT / "data" / "pdfs"
INDEX_DIR = ROOT / "data" / "vector_store"  # already in .gitignore
CACHE_DIR = ROOT / ".cache"

# D1 stack decisions
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dim, fast on CPU
VECTOR_STORE = "faiss"  # IndexFlatIP on normalised vectors = cosine similarity
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "")  # optional backup model name
GEMINI_TIMEOUT_S = 60
GEMINI_MAX_RETRIES = 3

CHUNK_WORDS = 180  # see ingest.py: MiniLM reads ~256 word-pieces, so 500 would be truncated
CHUNK_OVERLAP = 30
TOP_K = 5
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.20"))  # below this the chunk is ignored; tune on real data (D9)


def get_gemini_key() -> str:
    try:
        import streamlit as st
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    key = os.getenv("GEMINI_API_KEY", "")
    if not key or key == "your_key_here":
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env or Streamlit secrets.")
    return key
