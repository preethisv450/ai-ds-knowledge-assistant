"""Tests every available Gemini flash model in parallel, saves the best working one to .env.
Run from the repo root: python scripts/pick_model.py   (takes at most ~35 seconds)"""
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from google import genai
from src.backend.config import get_gemini_key

client = genai.Client(api_key=get_gemini_key())

names = []
for m in client.models.list():
    n = (m.name or "").replace("models/", "")
    if "generateContent" in (getattr(m, "supported_actions", None) or []) and "flash" in n:
        if not any(x in n for x in ("image", "tts", "live", "audio", "native", "robotics", "computer", "omni")):
            names.append(n)
print(f"Testing {len(names)} models at once (30s limit each): {names}\n", flush=True)


def test(n):
    t = time.time()
    try:
        r = client.models.generate_content(model=n, contents="Reply with the single word: ready")
        return n, True, f"{r.text.strip()!r} in {time.time()-t:.1f}s"
    except Exception as e:
        return n, False, f"{time.time()-t:.1f}s {str(e)[:100]}"


pool = ThreadPoolExecutor(max_workers=len(names))
futures = [pool.submit(test, n) for n in names]
done, not_done = wait(futures, timeout=30)

good = []
for f in done:
    n, ok, msg = f.result()
    print(("OK    " if ok else "FAIL  ") + f"{n}: {msg}", flush=True)
    if ok:
        good.append(n)
for f in not_done:
    print("TIMEOUT: one model did not answer within 30s", flush=True)


def prefer(n):  # non-lite first, then newest version number
    return ("lite" in n, [-int(x) for x in re.findall(r"\d+", n)])


if not good:
    print("\nNo model worked. Paste this whole output to Claude.")
    os._exit(1)

winner = sorted(good, key=prefer)[0]
env = ROOT / ".env"
text = env.read_text()
if re.search(r"^GEMINI_MODEL=.*$", text, flags=re.M):
    text = re.sub(r"^GEMINI_MODEL=.*$", f"GEMINI_MODEL={winner}", text, flags=re.M)
else:
    text = text.rstrip("\n") + f"\nGEMINI_MODEL={winner}\n"
env.write_text(text)
print(f"\nSaved GEMINI_MODEL={winner} to .env. Now run: python scripts/check_env.py", flush=True)
os._exit(0)
