"""D9: evaluate the chatbot on a test set.
  python scripts/evaluate.py data/eval/test_questions.csv                  full run (calls Gemini, ~2s per question)
  python scripts/evaluate.py data/eval/test_questions.csv --retrieval-only  no Gemini; retrieval + threshold advice only
  add --delay=8 to wait 8 seconds between Gemini calls (default 5) if you hit "AI service is busy" errors
  try another threshold without editing code:  RAG_MIN_SCORE=0.15 python scripts/evaluate.py ...
Writes results/eval_<time>.csv with a row per question."""
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend import config
from src.backend.gemini_client import _MESSAGES
from src.backend.evaluation import load_questions, run_eval, summarize, sweep_threshold
from src.backend.rag import answer
from src.backend.retrieval import retrieve

args = [a for a in sys.argv[1:] if not a.startswith("--")]
delay = next((float(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--delay=")), 5.0)
if not args:
    sys.exit(__doc__)
retrieval_only = "--retrieval-only" in sys.argv
rows = load_questions(args[0])
if not retrieval_only:
    print(f"Note: a full run makes up to {len(rows)} Gemini requests; free-tier daily quotas are small (20/day on some models).")
print(f"{len(rows)} questions | threshold {config.RAG_MIN_SCORE} | {'retrieval only' if retrieval_only else 'full run'}\n")

progress = {"n": 0}


def paced_answer(q, mode, sel):
    progress["n"] += 1
    print(f"  [{progress['n']}/{len(rows)}] asking: {q[:70]}", flush=True)
    t = time.time()
    res = answer(q, mode, sel, cache=None)  # D14: never read saved answers while measuring accuracy
    print(f"        done in {time.time() - t:.1f}s", flush=True)
    if res["answer"] == _MESSAGES["quota"]:
        sys.exit("\nStopped: the daily Gemini quota is used up (free tier limits are small and per model). "
                 "Use --retrieval-only (costs nothing), switch GEMINI_MODEL in .env, or wait for the reset.")
    time.sleep(delay)  # stay under the free-tier requests-per-minute limit
    return res


results = run_eval(rows, retrieve, None if retrieval_only else paced_answer)
s = summarize(results)
pct = lambda v: "n/a" if v is None else f"{v:.0%}"
print(f"Answerable: {s['answerable']}  Unanswerable: {s['unanswerable']}")
print(f"Retrieval hit rate (expected page in top {config.TOP_K}): {pct(s['retrieval_hit_rate'])}")
if not retrieval_only:
    print(f"Accuracy: {pct(s['accuracy'])} of {s['questions'] - s['errors']} scored questions   (plan target: 80%)")
    if s["errors"]:
        print(f"WARNING: {s['errors']} question(s) got a Gemini error (busy/timeout) and were NOT scored. Rerun with a larger --delay.")
    print(f"Answers citing the expected page: {pct(s['citation_rate'])}")
    fails = [r for r in results if r["correct"] is False]
    print(f"\nFailures ({len(fails)}):")
    for r in fails:
        print(f"  [{r['id']}] {r['question']}\n       -> {r['why']} (top score {r['top_score']:.2f})")
print(f"\nTop retrieval score: lowest for an answerable question = {s['answerable_top_score_min']}, "
      f"highest for an unanswerable one = {s['unanswerable_top_score_max']}")
best = sweep_threshold(results)[:3]
print("Best thresholds by retrieval score alone: " + ", ".join(f"{t:.2f} ({a:.0%})" for t, a in best)
      + f"   [current: {config.RAG_MIN_SCORE}]")

out = Path(config.ROOT) / "results" / f"eval_{time.strftime('%Y%m%d_%H%M%S')}.csv"
out.parent.mkdir(exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(results[0]))
    w.writeheader()
    w.writerows(results)
print(f"\nPer-question results saved to {out}")
