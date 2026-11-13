"""D9/D10: grade the chatbot's answers correct / partial / wrong, with a reason for each.

The backend's own harness (src/backend/evaluation.py) answers one question: did the
answer pass? Nishant's sheet needs more than that - every wrong answer needs a reason,
so the team knows what to fix, and D10 needs to compare a run against the previous one.

A verdict is one of:
  correct  - the expected keywords are there and the citation points at the right page
  partial  - the answer is on topic but incomplete, or right but cited the wrong page
  wrong    - missed the point, refused a question the documents answer, or answered one
             they do not
  error    - Gemini itself failed. Not counted either way.
"""
import csv
from collections import Counter
from pathlib import Path

from src.backend.config import EVAL_PASS_COVERAGE

PARTIAL_COVERAGE = 0.25      # below this, an answer is not meaningfully on topic
VERDICTS = ("correct", "partial", "wrong", "error")

REASONS = {
    "retrieval_miss": "the expected page was not retrieved at all",
    "refused_wrongly": "said not found, but the documents do contain the answer",
    "answered_unanswerable": "answered a question the documents cannot answer",
    "low_coverage": "the answer missed most of the expected points",
    "partial_coverage": "the answer is on topic but incomplete",
    "wrong_citation": "the content is right but it cited the wrong page",
    "no_citation": "the answer carries no source reference",
    "service_error": "Gemini was unavailable, so this answer was not scored",
}


def grade(result, pass_coverage=EVAL_PASS_COVERAGE, partial_coverage=PARTIAL_COVERAGE):
    """Turn one row from run_eval() into (verdict, reason_key). `result` is scored already."""
    if result.get("error"):
        return "error", "service_error"
    if not result["answerable"]:
        return ("correct", "") if result["correct"] else ("wrong", "answered_unanswerable")

    coverage = result.get("coverage")
    cited_ok = result.get("cited_ok")
    said_not_found = result.get("correct") is False and "not found" in (result.get("why") or "")

    if said_not_found:
        reason = "retrieval_miss" if result.get("retrieval_hit") is False else "refused_wrongly"
        return "wrong", reason
    if coverage is None:
        return "wrong", "low_coverage"
    if coverage >= pass_coverage:
        if cited_ok is False:
            return "partial", "wrong_citation"
        if cited_ok is None and not result.get("answer"):
            return "partial", "no_citation"
        return "correct", ""
    if coverage >= partial_coverage:
        return "partial", "partial_coverage"
    return "wrong", "retrieval_miss" if result.get("retrieval_hit") is False else "low_coverage"


def grade_all(results, **kw):
    """Add 'verdict' and 'reason' to every result. Returns the same list."""
    for r in results:
        verdict, reason = grade(r, **kw)
        r["verdict"], r["reason"] = verdict, reason
        r["reason_text"] = REASONS.get(reason, "")
    return results


def report(results):
    """Counts, accuracy and the failure reasons, grouped."""
    graded = [r for r in results if r.get("verdict") != "error"]
    counts = Counter(r.get("verdict") for r in results)
    scored = len(graded)
    answerable = [r for r in graded if r["answerable"]]
    hits = [r["retrieval_hit"] for r in answerable if r["retrieval_hit"] is not None]
    return {
        "questions": len(results),
        "scored": scored,
        "correct": counts.get("correct", 0),
        "partial": counts.get("partial", 0),
        "wrong": counts.get("wrong", 0),
        "errors": counts.get("error", 0),
        # strict accuracy counts only full marks; lenient gives half a mark for partial
        "accuracy": counts.get("correct", 0) / scored if scored else None,
        "accuracy_lenient": (counts.get("correct", 0) + 0.5 * counts.get("partial", 0)) / scored if scored else None,
        "retrieval_hit_rate": sum(hits) / len(hits) if hits else None,
        "reasons": Counter(r["reason"] for r in results if r.get("reason")),
        "by_mode": {m: Counter(r.get("verdict") for r in results if r.get("mode") == m)
                    for m in sorted({r.get("mode") for r in results if r.get("mode")})},
    }


def meets_target(summary, target=0.8):
    """The D10 milestone check. None when nothing could be scored."""
    return None if summary["accuracy"] is None else summary["accuracy"] >= target


FIELDS = ["id", "mode", "question", "answerable", "verdict", "reason", "reason_text",
          "coverage", "top_score", "retrieval_hit", "cited_ok", "answer"]


def save_csv(results, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow({k: r.get(k) for k in FIELDS})
    return path


def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def compare(previous_rows, results):
    """D10: what changed since the previous run. previous_rows comes from load_csv()."""
    before = {str(r.get("id")): (r.get("verdict") or "").strip() for r in previous_rows}
    fixed, broken, still_wrong, unchanged = [], [], [], 0
    rank = {"wrong": 0, "partial": 1, "correct": 2, "error": -1}
    for r in results:
        old, new = before.get(str(r["id"])), r.get("verdict")
        if old is None:
            continue
        if old == new:
            unchanged += 1
            if new in ("wrong", "partial"):
                still_wrong.append((r["id"], r["question"], r.get("reason_text") or r.get("reason")))
        elif rank.get(new, -1) > rank.get(old, -1):
            fixed.append((r["id"], r["question"], old, new))
        else:
            broken.append((r["id"], r["question"], old, new))
    return {"fixed": fixed, "broken": broken, "still_failing": still_wrong, "unchanged": unchanged,
            "new_questions": [r["id"] for r in results if str(r["id"]) not in before]}
