"""D9/D10: run the test set through the chatbot and report accuracy with failure reasons.

  python scripts/accuracy_report.py                          full run (uses Gemini)
  python scripts/accuracy_report.py --retrieval-only         no Gemini: retrieval only
  python scripts/accuracy_report.py --delay=8                pause between questions
  python scripts/accuracy_report.py --compare=results/accuracy_20261113.csv

D9 is the first run: read the reasons, fix what they point at. D10 is the second run
with --compare, which shows what the fixes changed and checks the 80 percent target.
Every run is saved to results/accuracy_<timestamp>.csv.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend.config import ROOT
from src.backend.evaluation import load_questions, run_eval
from src.backend.gemini_client import _MESSAGES
from src.backend.rag import answer
from src.backend.retrieval import retrieve
from src.data.report import compare, grade_all, load_csv, meets_target, report, save_csv

TARGET = 0.8
path = Path(next((a for a in sys.argv[1:] if not a.startswith("--")), "data/eval/test_questions.csv"))
if not path.exists():
    sys.exit(f"{path} not found. Create it with: python scripts/make_question_set.py --new")
delay = next((float(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--delay=")), 4.0)
previous = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--compare=")), None)
retrieval_only = "--retrieval-only" in sys.argv

rows = load_questions(path)
print(f"{len(rows)} questions from {path}" + ("  (retrieval only, no Gemini)" if retrieval_only else ""))

answer_fn = None
if not retrieval_only:
    quota = _MESSAGES["quota"]

    def answer_fn(q, mode, sel):
        res = answer(q, mode, sel, cache=None, fallback=False)   # measure the real answer
        if res["answer"] == quota:
            print("\nStopped: the daily Gemini quota is used up. Re-run after it resets.")
            sys.exit(2)
        print(".", end="", flush=True)
        time.sleep(delay)
        return res

results = grade_all(run_eval(rows, retrieve, answer_fn))
for r, src in zip(results, rows):
    r["mode"] = src["mode"]
print()

s = report(results)
width = max((len(str(r["id"])) for r in results), default=2)
for r in results:
    mark = {"correct": "OK  ", "partial": "PART", "wrong": "WRONG", "error": "SKIP"}[r["verdict"]]
    print(f"  {mark:<6} Q{str(r['id']):<{width}} {r['question'][:58]:<58} {r.get('reason_text', '')}")

print(f"\n{s['correct']} correct, {s['partial']} partial, {s['wrong']} wrong"
      + (f", {s['errors']} not scored (Gemini unavailable)" if s["errors"] else ""))
if s["accuracy"] is not None:
    print(f"Accuracy        : {s['accuracy']:.0%}   (counting partial as half: {s['accuracy_lenient']:.0%})")
if s["retrieval_hit_rate"] is not None:
    print(f"Retrieval hits  : {s['retrieval_hit_rate']:.0%} of answerable questions had the expected page retrieved")
for mode, counts in s["by_mode"].items():
    print(f"  {mode:<11} {counts.get('correct', 0)} correct / {sum(counts.values())}")

if s["reasons"]:
    print("\nWhy answers were not fully correct")
    from src.data.report import REASONS
    for reason, n in s["reasons"].most_common():
        print(f"  {n:>3}x  {REASONS.get(reason, reason)}")

hit = meets_target(s, TARGET)
if hit is not None:
    print(f"\nD10 target (>= {TARGET:.0%}): {'MET' if hit else 'NOT MET'}")

out = save_csv(results, ROOT / "results" / f"accuracy_{time.strftime('%Y%m%d_%H%M%S')}.csv")
print(f"Saved to {out}")

if previous:
    c = compare(load_csv(previous), results)
    print(f"\nCompared with {Path(previous).name}")
    print(f"  fixed      : {len(c['fixed'])}")
    for qid, q, old, new in c["fixed"]:
        print(f"      Q{qid} {q[:50]}  {old} -> {new}")
    print(f"  regressed  : {len(c['broken'])}")
    for qid, q, old, new in c["broken"]:
        print(f"      Q{qid} {q[:50]}  {old} -> {new}")
    print(f"  unchanged  : {c['unchanged']}")
    if c["still_failing"]:
        print(f"  still not right ({len(c['still_failing'])}):")
        for qid, q, reason in c["still_failing"]:
            print(f"      Q{qid} {q[:50]}  {reason}")
    if c["new_questions"]:
        print(f"  new since then: {', '.join(c['new_questions'])}")
sys.exit(0 if (hit is None or hit) else 1)
