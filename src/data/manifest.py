"""D7: build data/processed/documents.json - which PDF is what, and which pages hold which module.

This file is what makes module-scoped search work. Without it every question searches
every page of every document; with it, a question asked under 'Machine Learning,
Module 3' only ever sees that module's pages.

Page ranges are found by locating each module's heading in the PDF, cross-checked
against the module titles in curriculum.json. Anything the builder is unsure about is
reported so a person can fix it by hand.
"""
import difflib
import json
import re
from pathlib import Path

from src.backend.config import PDF_DIR, ROOT
from src.data.schema import REGULATION_TOPICS, iter_subjects, module_id_for
from src.data.syllabus_parser import MODULE_HEAD, _module_number
from src.backend.ingest import extract_pages

MANIFEST_PATH = ROOT / "data" / "processed" / "documents.json"
_REG_WORDS = tuple(w for words in REGULATION_TOPICS.values() for w in words) + ("regulation", "ordinance")
TITLE_MATCH = 0.6     # how close a heading must be to the curriculum title to count as a match


def guess_doc_type(pdf_path):
    stem = Path(pdf_path).stem.lower()
    if any(w in stem for w in ("regulation", "ordinance", "rules", "policy", "statute", "bylaw")):
        return "regulation"
    if re.match(r"^[a-z]{2,4}\d{3}", stem):
        return "syllabus"
    text = " ".join(t for _, t in extract_pages(pdf_path)[:2]).lower()
    hits = sum(w in text for w in _REG_WORDS)
    if "module" in text or "unit " in text:
        return "syllabus"
    return "regulation" if hits >= 3 else "other"


def find_module_pages(pdf_path, subject_code, curriculum_modules=None):
    """Return ({module_id: [first, last]}, [notes]) by locating module headings in the PDF."""
    pages = extract_pages(pdf_path, strip_headers=False)
    if not pages:
        return {}, [f"{Path(pdf_path).name}: no selectable text (a scan needs OCR first)"]

    found, notes = [], []
    for page_no, text in pages:
        for line in text.splitlines():
            m = MODULE_HEAD.match(line.strip())
            if not m:
                continue
            n = _module_number(m.group(1))
            if n and not any(n == f[0] for f in found):
                found.append((n, page_no, (m.group(2) or "").strip(" .:-–")))

    if not found:
        notes.append(f"{Path(pdf_path).name}: no 'Module N' or 'Unit N' headings found - add page ranges by hand")
        return {}, notes

    found.sort()
    last_page = pages[-1][0]
    ranges = {}
    for i, (n, page, title) in enumerate(found):
        nxt = found[i + 1][1] if i + 1 < len(found) else None
        end = (nxt - 1 if nxt > page else page) if nxt else last_page
        ranges[module_id_for(subject_code, n)] = [page, end]

    if curriculum_modules:
        titles = {int(re.search(r"-M(\d+)$", mid).group(1)): t
                  for mid, t in curriculum_modules.items() if re.search(r"-M(\d+)$", mid)}
        for n, _, title in found:
            want = titles.get(n)
            if want and title:
                score = difflib.SequenceMatcher(None, want.lower(), title.lower()).ratio()
                if score < TITLE_MATCH:
                    notes.append(f"{Path(pdf_path).name}: module {n} is titled {title!r} in the PDF "
                                 f"but {want!r} in curriculum.json - check they are the same module")
        extra = sorted(set(titles) - {n for n, _, _ in found})
        if extra:
            notes.append(f"{Path(pdf_path).name}: curriculum has module(s) {extra} that were not found in the PDF")
    return ranges, notes


def build(pdf_dir=PDF_DIR, curriculum=None, skip=()):
    """Return (entries, notes) for every PDF in pdf_dir."""
    by_code = {}
    for _, _, subject in iter_subjects(curriculum or {}):
        code = (subject.get("code") or "").upper()
        if code:
            by_code[code] = {m.get("id", "").upper(): m.get("title", "") for m in subject.get("modules", [])}

    entries, notes = [], []
    for pdf in sorted(Path(pdf_dir).glob("*.pdf")):
        if pdf.name in skip:
            continue
        doc_type = guess_doc_type(pdf)
        entry = {"file": pdf.name, "doc_type": doc_type}
        if doc_type == "syllabus":
            m = re.match(r"^([A-Za-z]{2,4}\d{3}[A-Za-z]?)", pdf.stem)
            code = m.group(1).upper() if m else None
            if not code:
                notes.append(f"{pdf.name}: no subject code in the file name - set subject_code by hand")
            else:
                entry["subject_code"] = code
                if curriculum and code not in by_code:
                    notes.append(f"{pdf.name}: subject {code} is not in curriculum.json")
                ranges, n = find_module_pages(pdf, code, by_code.get(code))
                notes += n
                if ranges:
                    entry["modules"] = ranges
        elif doc_type == "other":
            notes.append(f"{pdf.name}: could not tell what this document is - it will not be searched. "
                         f"Set doc_type by hand, or leave it if it is not course material.")
        entries.append(entry)
    return entries, notes


def save(entries, path=MANIFEST_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2) + "\n")
    return path


def merge(existing_entries, new_entries):
    """Keep hand-edited entries, add newly found files. Existing entries always win."""
    by_file = {e["file"].lower(): e for e in new_entries}
    out, kept = [], set()
    for e in existing_entries:
        out.append(e)
        kept.add(e["file"].lower())
    for f, e in by_file.items():
        if f not in kept:
            out.append(e)
    return out
