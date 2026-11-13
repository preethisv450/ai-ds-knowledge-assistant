"""D14: small on-disk cache for generated outputs (summaries, questions, quizzes, answers).

One JSON file per entry in .cache/generated/ (already gitignored). Entries are keyed by what was
asked plus a fingerprint of the index, so rebuilding the index or adding PDFs automatically makes
old entries unreachable. Only successful results are stored; errors and 'not found' messages never are.
A corrupt or expired file counts as a miss and is never an error.
"""
import hashlib
import json
import os
import time
from pathlib import Path

from src.backend import config

AUTO = object()  # "use the real cache when running for real, none when functions are injected (tests)"
_default = None


def index_fingerprint(index_dir=None):
    """Changes whenever the index is rebuilt. 'none' when there is no index."""
    d = Path(index_dir or config.INDEX_DIR)
    parts = []
    for name in ("chunks.json", "faiss.index", "meta.json"):
        f = d / name
        if not f.exists():
            return "none"
        st = f.stat()
        parts.append(f"{name}:{st.st_size}:{st.st_mtime_ns}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def make_key(*parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:32]


class Cache:
    def __init__(self, directory=None, ttl_s=None, now=time.time):
        self.dir = Path(directory) if directory else Path(config.CACHE_DIR) / "generated"
        self.ttl_s = config.CACHE_TTL_S if ttl_s is None else ttl_s
        self._now = now

    def _path(self, kind, key):
        return self.dir / f"{kind}-{key}.json"

    def get(self, kind, key, allow_stale=False):
        """allow_stale=True also returns expired entries (used when Gemini is down: an old answer beats none)."""
        try:
            entry = json.loads(self._path(kind, key).read_text())
            if not allow_stale and self._now() - entry["saved"] > self.ttl_s:
                return None
            return entry["value"]
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def put(self, kind, key, value):
        """Best effort: a cache that cannot be written must never break the feature."""
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            path = self._path(kind, key)
            tmp = path.with_suffix(f".{os.getpid()}.tmp")
            tmp.write_text(json.dumps({"saved": self._now(), "value": value}))
            os.replace(tmp, path)
        except OSError:
            pass

    def clear(self):
        n = 0
        if self.dir.exists():
            for f in self.dir.glob("*.json"):
                try:
                    f.unlink()
                    n += 1
                except OSError:
                    pass
        return n


def get_cache():
    global _default
    if _default is None:
        _default = Cache()
    return _default


def resolve(cache, *injected):
    """AUTO -> the shared cache, unless a function was injected (tests/evaluation), then no cache."""
    if cache is AUTO:
        return get_cache() if all(f is None for f in injected) else None
    return cache
