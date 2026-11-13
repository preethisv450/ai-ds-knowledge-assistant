"""D15: end-to-end check of every AI feature on the documents in data/pdfs.

  python scripts/e2e_check.py                run everything (about 25-35 Gemini requests)
  python scripts/e2e_check.py --delay=6      seconds to wait between Gemini calls (default 4)
  python scripts/e2e_check.py --no-gemini    only the free checks: index labels and retrieval scoping

Needs the index (python scripts/build_index.py) and data/processed/documents.json. Without real
documents, run python scripts/make_sample_data.py first. Exit code 0 only if nothing FAILED.
"""
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backend import config
from src.backend.catalog import load_manifest, make_filter
from src.backend.e2e import Quota, check_module, module_targets
from src.backend.evaluation import load_questions, run_eval, summarize
from src.backend.gemini_client import _MESSAGES
from src.backend.rag import answer
from src.backend.retrieval import retrieve
from src.backend.study import generate_questions, generate_quiz, generate_summary

delay = next((float(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--delay=")), 4.0)
use_gemini = "--no-gemini" not in sys.argv
rows = []


def add(area, check, status, detail=""):
    rows.append({"module": area, "check": check, "status": status, "detail": detail})
    print(f"  {status:<4} {area}: {check}" + (f"  ({detail})" if detail else ""), flush=True)


manifest = load_manifest()
curriculum = json.loads((config.ROOT / "data" / "processed" / "curriculum.json").read_text())
targets = list(module_targets(curriculum, manifest))
if not manifest or not targets:
    sys.exit("No modules with page ranges found. Create data/processed/documents.json "
             "(see docs/data_manifest.md) or run python scripts/make_sample_data.py")

print(f"Threshold {config.RAG_MIN_SCORE} | model {config.GEMINI_MODEL} | {len(targets)} modules | "
      f"{'with Gemini' if use_gemini else 'no Gemini'}\n\n1. Retrieval is scoped to the chosen module")
for sel, doc, (a, b) in targets:
    res = retrieve(f"{sel['subject']} {sel['module']}", k=5,
                   where=make_filter("Syllabus", sel))
    bad = [r for r in res if r["document"].lower() != doc.lower() or not a <= r["page"] <= b]
    add(sel["module_id"], "retrieval stays inside the module", "PASS" if res and not bad else "FAIL",
        f"{len(res)} chunks" if res and not bad else ("no chunks" if not res else f"leaked: {[(r['document'], r['page']) for r in bad]}"))

qfile = config.ROOT / "data" / "eval" / "e2e_questions.csv"
if not use_gemini:
    if qfile.exists():
        print("\n2. Chat retrieval (no Gemini)")
        s = summarize(run_eval(load_questions(qfile), retrieve))
        hit = s["retrieval_hit_rate"]
        add("chat", "expected page in top 5", "PASS" if hit is not None and hit >= 0.8 else "FAIL",
            "n/a" if hit is None else f"{hit:.0%}")
else:
    def pause():
        time.sleep(delay)

    print("\n2. Summary, questions and quiz for every module")
    quota = _MESSAGES["quota"]
    try:
        for sel, doc, pages in targets:
            for r in check_module(
                    sel, doc, pages,
                    lambda s, refresh: generate_summary(s, refresh=refresh, fallback=False),
                    lambda s, t, n, refresh: generate_questions(s, t, n, refresh=refresh, fallback=False),
                    lambda s, n, refresh: generate_quiz(s, n, refresh=refresh, fallback=False),
                    pause=pause, quota_message=quota):
                add(r["module"], r["check"], r["status"], r["detail"])
    except Quota:
        sys.exit("\nStopped: the daily Gemini quota is used up. Wait for the reset (about 13:30 IST) or switch GEMINI_MODEL in .env.")

    if qfile.exists():
        print("\n3. Chat answers with page references")

        def paced(q, mode, sel):
            res = answer(q, mode, sel, cache=None, fallback=False)
            if res["answer"] == quota:
                sys.exit("\nStopped: the daily Gemini quota is used up.")
            time.sleep(delay)
            return res
        results = run_eval(load_questions(qfile), retrieve, paced)
        s = summarize(results)
        for r in results:
            if r["error"]:
                add("chat", f"Q{r['id']} {r['question'][:45]}", "SKIP", "Gemini problem")
            else:
                add("chat", f"Q{r['id']} {r['question'][:45]}", "PASS" if r["correct"] else "FAIL", r["why"])
        if s["accuracy"] is not None:
            add("chat", "accuracy at least 80% (plan target)", "PASS" if s["accuracy"] >= 0.8 else "FAIL", f"{s['accuracy']:.0%}")

counts = {k: sum(r["status"] == k for r in rows) for k in ("PASS", "FAIL", "SKIP")}
print(f"\nSummary: {counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped (Gemini problems)")
out = config.ROOT / "results" / f"e2e_{time.strftime('%Y%m%d_%H%M%S')}.csv"
out.parent.mkdir(exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["module", "check", "status", "detail"])
    w.writeheader()
    w.writerows(rows)
print(f"Saved to {out}")
sys.exit(1 if counts["FAIL"] else 0)
