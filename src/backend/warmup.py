"""D16: load the embedding model and the index ahead of the first question.

The first real question otherwise pays for loading torch, the SBERT model and the index (several seconds).
warm_up() does that work once, never raises, and returns timings. app.py runs it in a background thread
at startup, so the page appears immediately and the first question is fast.
"""
import threading
import time

_started = None


def warm_up(index_dir=None):
    """Returns {"ok": bool, "model_s": float, "index_s": float, "error": str}."""
    out = {"ok": False, "model_s": 0.0, "index_s": 0.0, "error": ""}
    try:
        from src.backend import retrieval
        from src.backend.config import INDEX_DIR
        from src.backend.vector_store import embed_texts

        t = time.time()
        embed_texts(["warm up"])  # loads the model and runs one batch
        out["model_s"] = round(time.time() - t, 2)
        t = time.time()
        retrieval._load(index_dir or INDEX_DIR)
        out["index_s"] = round(time.time() - t, 2)
        out["ok"] = True
    except FileNotFoundError:
        out["error"] = "no index yet (run scripts/build_index.py)"
    except Exception as e:  # warming is an optimisation: it must never break the app
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def start_background():
    """Start warm_up() in a daemon thread, once per process. Returns the thread."""
    global _started
    if _started is None:
        _started = threading.Thread(target=warm_up, name="warm-up", daemon=True)
        _started.start()
    return _started
