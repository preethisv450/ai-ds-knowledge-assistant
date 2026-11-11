"""D1 exit check. From the repo root run: python scripts/check_env.py"""
import faulthandler
import sys
from pathlib import Path

faulthandler.enable()

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
failed = False


def step(name, fn):
    global failed
    print(f"...   {name}", flush=True)
    try:
        print(f"OK    {name}: {fn()}", flush=True)
    except Exception as e:
        failed = True
        print(f"FAIL  {name}: {e}", flush=True)


def imports():
    for m in ("streamlit", "sentence_transformers", "faiss", "google.genai", "networkx", "pymupdf", "dotenv"):
        __import__(m)
    return "all packages import"


def embed():
    from sentence_transformers import SentenceTransformer
    from src.backend.config import EMBEDDING_MODEL
    return f"embedding dim {SentenceTransformer(EMBEDDING_MODEL).encode(['hello']).shape[1]}"


def faiss_roundtrip():
    import faiss, numpy as np, tempfile, os
    idx = faiss.IndexFlatIP(384)
    idx.add(np.random.rand(10, 384).astype("float32"))
    p = os.path.join(tempfile.mkdtemp(), "t.index")
    faiss.write_index(idx, p)
    return f"saved and reloaded {faiss.read_index(p).ntotal} vectors"


def gemini():
    from google import genai
    from src.backend.config import get_gemini_key, GEMINI_MODEL
    client = genai.Client(api_key=get_gemini_key())  # keep a reference or it gets closed early
    r = client.models.generate_content(
        model=GEMINI_MODEL, contents="Reply with the single word: ready")
    return r.text.strip()


for n, f in [("imports", imports), ("embedding model", embed), ("faiss", faiss_roundtrip), ("gemini call", gemini)]:
    step(n, f)
sys.exit(1 if failed else 0)
