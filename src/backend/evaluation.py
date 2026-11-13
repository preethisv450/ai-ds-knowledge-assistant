"""D9: score the chatbot on a test set (CSV) and help choose RAG_MIN_SCORE.

CSV columns (header row required; only `question` is mandatory):
  id, question, mode (Syllabus|Regulation), subject_code, module_id,
  expected_keywords (pipe-separated, e.g. retries|timeout), expected_doc, expected_page,
  answerable (yes|no; 'no' = the documents do not contain the answer)
"""
import csv

from src.backend.catalog import make_filter
from src.backend.config import EVAL_PASS_COVERAGE, RAG_MIN_SCORE, TOP_K
from src.backend.gemini_client import _MESSAGES
from src.backend.prompts import NOT_FOUND

REQUIRED = "question"
SERVICE_ERRORS = set(_MESSAGES.values())  # friendly texts returned when Gemini itself failed


def is_service_error(text):
    """True for a friendly Gemini-failure text, also when a fallback adds passages after it (D16)."""
    return any((text or "").startswith(m) for m in SERVICE_ERRORS)


def load_questions(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if REQUIRED not in (reader.fieldnames or []):
            raise ValueError(f"{path}: header must include a 'question' column (found {reader.fieldnames})")
        rows = []
        for n, r in enumerate(reader, start=2):
            q = (r.get("question") or "").strip()
            if not q:
                continue
            mode = (r.get("mode") or "Syllabus").strip().capitalize()
            if mode not in ("Syllabus", "Regulation"):
                raise ValueError(f"{path} line {n}: mode must be Syllabus or Regulation, got {r.get('mode')!r}")
            ans = (r.get("answerable") or "yes").strip().lower()
            if ans not in ("yes", "no", "y", "n", "true", "false"):
                raise ValueError(f"{path} line {n}: answerable must be yes or no, got {r.get('answerable')!r}")
            page = (r.get("expected_page") or "").strip()
            if page and not page.isdigit():
                raise ValueError(f"{path} line {n}: expected_page must be a number, got {page!r}")
            code, mod = (r.get("subject_code") or "").strip(), (r.get("module_id") or "").strip()
            rows.append({
                "id": (r.get("id") or str(len(rows) + 1)).strip(),
                "question": q,
                "mode": mode,
                "selection": {"subject_code": code or None, "module_id": mod or None} if (code or mod) else None,
                "keywords": [k.strip() for k in (r.get("expected_keywords") or "").split("|") if k.strip()],
                "expected_doc": (r.get("expected_doc") or "").strip() or None,
                "expected_page": int(page) if page else None,
                "answerable": ans in ("yes", "y", "true"),
            })
    if not rows:
        raise ValueError(f"{path}: no questions found")
    return rows


def keyword_coverage(answer, keywords):
    """Fraction of expected keywords that appear in the answer (case-insensitive). 1.0 if none expected."""
    if not keywords:
        return 1.0
    a = (answer or "").lower()
    return sum(k.lower() in a for k in keywords) / len(keywords)


def _is_not_found(answer):
    return (answer or "").strip().startswith(NOT_FOUND)


def _page_hit(items, doc, page):
    if not doc:
        return None
    return any(i["document"].lower() == doc.lower() and (page is None or i["page"] == page) for i in items)


def run_eval(rows, retrieve_fn, answer_fn=None, min_score=None, pass_coverage=EVAL_PASS_COVERAGE, k=TOP_K):
    """answer_fn=None -> retrieval-only (no Gemini calls). Returns one result dict per question."""
    min_score = RAG_MIN_SCORE if min_score is None else min_score
    out = []
    for r in rows:
        retrieved = retrieve_fn(r["question"], k=k, where=make_filter(r["mode"], r["selection"]))
        top = retrieved[0]["score"] if retrieved else 0.0
        res = {"id": r["id"], "question": r["question"], "answerable": r["answerable"], "top_score": top,
               "retrieval_hit": _page_hit(retrieved, r["expected_doc"], r["expected_page"]),
               "answer": None, "coverage": None, "cited_ok": None, "correct": None, "why": "", "error": False}
        if answer_fn is not None:
            a = answer_fn(r["question"], r["mode"], r["selection"])
            text, sources = a["answer"], a["sources"]
            nf = _is_not_found(text)
            res["answer"] = text
            if is_service_error(text):  # Gemini failed: this says nothing about answer quality, so do not score it
                res["error"], res["why"] = True, "Gemini error, not scored"
            elif r["answerable"]:
                res["coverage"] = keyword_coverage(text, r["keywords"])
                res["cited_ok"] = (len(sources) > 0) if r["expected_doc"] is None else bool(_page_hit(sources, r["expected_doc"], r["expected_page"]))
                if nf:
                    res["correct"], res["why"] = False, "said not found, but the answer is in the documents"
                elif res["coverage"] < pass_coverage:
                    res["correct"], res["why"] = False, f"answer covers {res['coverage']:.0%} of expected keywords"
                else:
                    res["correct"] = True
            else:
                res["correct"] = nf
                res["why"] = "" if nf else "answered a question the documents cannot answer"
        out.append(res)
    return out


def sweep_threshold(results, grid=None):
    """For each candidate threshold: accuracy of 'answerable iff top retrieval score >= t'.
    Needs no Gemini calls. Returns [(t, accuracy)] sorted by accuracy desc, then lower t first."""
    grid = grid or [round(x * 0.01, 2) for x in range(5, 51)]
    scored = []
    for t in grid:
        ok = sum((r["top_score"] >= t) == r["answerable"] for r in results)
        scored.append((t, ok / len(results)))
    return sorted(scored, key=lambda x: (-x[1], x[0]))


def summarize(results):
    n = len(results)
    ans = [r for r in results if r["answerable"]]
    un = [r for r in results if not r["answerable"]]
    s = {"questions": n, "answerable": len(ans), "unanswerable": len(un)}
    hits = [r["retrieval_hit"] for r in ans if r["retrieval_hit"] is not None]
    s["retrieval_hit_rate"] = sum(hits) / len(hits) if hits else None
    judged = [r for r in results if r["correct"] is not None]
    s["accuracy"] = sum(r["correct"] for r in judged) / len(judged) if judged else None
    cited = [r["cited_ok"] for r in ans if r["cited_ok"] is not None]
    s["citation_rate"] = sum(cited) / len(cited) if cited else None
    s["errors"] = sum(r.get("error", False) for r in results)
    s["answerable_top_score_min"] = min((r["top_score"] for r in ans), default=None)
    s["unanswerable_top_score_max"] = max((r["top_score"] for r in un), default=None)
    return s
