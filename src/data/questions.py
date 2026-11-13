"""D8: the evaluation set - 30 questions with expected answers and page numbers.

The set is a CSV so it can live in Sheets. This module writes a blank template with the
right columns and checks a filled-in set against the actual documents, so a typo in a
page number is caught before it is reported as a wrong answer by the chatbot.

Columns:
  id                 1, 2, 3 ...
  question           what a student would really type
  mode               Syllabus or Regulation
  subject_code       for Syllabus questions, e.g. DS202
  module_id          for Syllabus questions, e.g. DS202-M3
  expected_keywords  pipe-separated words that must appear, e.g. precision|TP|FP
  expected_doc       the file the answer is in, e.g. DS202_syllabus.pdf
  expected_page      the page it is on
  answerable         yes, or no for a question the documents cannot answer
  notes              anything for the team
"""
import csv
from pathlib import Path

HEADER = ["id", "question", "mode", "subject_code", "module_id", "expected_keywords",
          "expected_doc", "expected_page", "answerable", "notes"]
TARGET_TOTAL = 30
TARGET_PER_MODE = {"Regulation": 15, "Syllabus": 15}
MIN_UNANSWERABLE = 3


def write_template(path, per_mode=None):
    """Write an empty set with the rows laid out, ready to fill in."""
    per_mode = per_mode or TARGET_PER_MODE
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows, n = [], 0
    for mode in ("Regulation", "Syllabus"):
        for i in range(per_mode.get(mode, 0)):
            n += 1
            unanswerable = i >= per_mode.get(mode, 0) - 2  # last two of each mode
            rows.append({
                "id": n, "question": "", "mode": mode,
                "subject_code": "", "module_id": "",
                "expected_keywords": "", "expected_doc": "", "expected_page": "",
                "answerable": "no" if unanswerable else "yes",
                "notes": "a question the documents genuinely cannot answer" if unanswerable else "",
            })
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
    return path


def check(rows, pdf_dir=None, curriculum=None):
    """Check a filled-in set. Returns a list of problems (strings); empty means it is usable.

    `rows` are the dicts from src.backend.evaluation.load_questions()."""
    problems = []
    page_counts = {}
    if pdf_dir:
        from src.backend.ingest import extract_pages
        for pdf in Path(pdf_dir).glob("*.pdf"):
            try:
                page_counts[pdf.name.lower()] = max((p for p, _ in extract_pages(pdf)), default=0)
            except Exception:
                page_counts[pdf.name.lower()] = 0

    known_modules, known_codes = set(), set()
    if curriculum:
        from src.data.schema import iter_modules, iter_subjects
        known_modules = {(m.get("id") or "").upper() for _, _, _, m in iter_modules(curriculum)}
        known_codes = {(s.get("code") or "").upper() for _, _, s in iter_subjects(curriculum)}

    seen_ids, seen_q = {}, {}
    for r in rows:
        qid = str(r["id"])
        where = f"Q{qid}"
        if qid in seen_ids:
            problems.append(f"{where}: id used twice")
        seen_ids[qid] = True
        key = " ".join(r["question"].lower().split())
        if key in seen_q:
            problems.append(f"{where}: same question as Q{seen_q[key]}")
        seen_q[key] = qid
        if len(r["question"].split()) < 3:
            problems.append(f"{where}: question is too short to be a real question")

        sel = r.get("selection") or {}
        code, mid = (sel.get("subject_code") or ""), (sel.get("module_id") or "")
        if r["mode"] == "Syllabus" and not code:
            problems.append(f"{where}: Syllabus questions need a subject_code, otherwise the scope is not tested")
        if curriculum and code and code.upper() not in known_codes:
            problems.append(f"{where}: subject {code} is not in curriculum.json")
        if curriculum and mid and mid.upper() not in known_modules:
            problems.append(f"{where}: module {mid} is not in curriculum.json")
        if r["mode"] == "Regulation" and (code or mid):
            problems.append(f"{where}: Regulation questions should not set subject_code or module_id")

        if r["answerable"]:
            if not r["keywords"]:
                problems.append(f"{where}: no expected_keywords, so the answer cannot be scored")
            if not r["expected_doc"]:
                problems.append(f"{where}: no expected_doc, so the citation cannot be checked")
            if r["expected_doc"] and page_counts:
                n = page_counts.get(r["expected_doc"].lower())
                if n is None:
                    problems.append(f"{where}: {r['expected_doc']} is not in data/pdfs")
                elif r["expected_page"] and r["expected_page"] > n:
                    problems.append(f"{where}: page {r['expected_page']} but {r['expected_doc']} has {n} pages")
            if not r["expected_page"]:
                problems.append(f"{where}: no expected_page, so retrieval accuracy cannot be measured")
        else:
            if r["keywords"] or r["expected_doc"]:
                problems.append(f"{where}: marked unanswerable but has an expected answer")
    return problems


def balance(rows):
    """How the set is made up, against the D8 target of 30 questions, 15 of each mode."""
    modes = {}
    for r in rows:
        modes[r["mode"]] = modes.get(r["mode"], 0) + 1
    unanswerable = sum(1 for r in rows if not r["answerable"])
    notes = []
    if len(rows) < TARGET_TOTAL:
        notes.append(f"{len(rows)} questions, the plan asks for {TARGET_TOTAL}")
    for mode, want in TARGET_PER_MODE.items():
        have = modes.get(mode, 0)
        if have < want:
            notes.append(f"{have} {mode} questions, the plan asks for {want}")
    if unanswerable < MIN_UNANSWERABLE:
        notes.append(f"only {unanswerable} unanswerable question(s); include at least {MIN_UNANSWERABLE} "
                     f"so refusal is tested too")
    covered = {(r.get("selection") or {}).get("module_id") for r in rows} - {None, ""}
    return {"total": len(rows), "by_mode": modes, "unanswerable": unanswerable,
            "modules_covered": sorted(covered), "notes": notes}
