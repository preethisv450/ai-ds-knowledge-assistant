"""D8: which document is what. Labels every chunk with doc_type / subject_code / module_id,
and builds the filter that scopes a search to the student's choice.

Labels come from data/processed/documents.json (the manifest) when a file is listed there,
otherwise from the file name:
  AI201_syllabus.pdf        -> syllabus, subject AI201
  Academic_Regulations.pdf  -> regulation (name contains regulation/ordinance/policy/rules/...)
  anything else             -> other (not searched in Syllabus or Regulation mode)
"""
import json
import re
from pathlib import Path

from src.backend.config import ROOT

MANIFEST_PATH = ROOT / "data" / "processed" / "documents.json"
_CODE = re.compile(r"^([A-Za-z]{2,4}\d{3})[_\-\s.]")
_REG_WORDS = ("regulation", "ordinance", "policy", "policies", "rules", "bylaw", "statute")
DOC_TYPES = ("syllabus", "regulation", "other")


def load_manifest(path=MANIFEST_PATH):
    """Return {filename_lowercase: entry}. A missing file means 'no manifest' ({}).
    Accepts a list of entries or {"documents": [...]}. Raises ValueError on bad content."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"{path.name} is not valid JSON: {e}")
    entries = raw.get("documents") if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        raise ValueError(f"{path.name} must be a list of documents (or {{\"documents\": [...]}})")
    out = {}
    for e in entries:
        if not isinstance(e, dict) or not e.get("file"):
            raise ValueError(f"{path.name}: every entry needs a 'file'")
        if e.get("doc_type", "syllabus") not in DOC_TYPES:
            raise ValueError(f"{path.name}: {e['file']} has doc_type {e['doc_type']!r}; use one of {DOC_TYPES}")
        for mid, rng in (e.get("modules") or {}).items():
            ok = isinstance(rng, list) and len(rng) == 2 and all(isinstance(x, int) for x in rng) and rng[0] <= rng[1]
            if not ok:
                raise ValueError(f"{path.name}: {e['file']} module {mid} needs [first_page, last_page]")
        out[e["file"].lower()] = e
    return out


def classify(file, page, manifest=None):
    """Return {"doc_type", "subject_code", "module_id"} for a chunk."""
    entry = (manifest or {}).get(file.lower())
    if entry:
        module_id = None
        for mid, (first, last) in (entry.get("modules") or {}).items():
            if first <= page <= last:
                module_id = mid
                break
        default_type = "syllabus" if entry.get("subject_code") else "other"
        return {"doc_type": entry.get("doc_type", default_type),
                "subject_code": (entry.get("subject_code") or None) and entry["subject_code"].upper(),
                "module_id": module_id}
    m = _CODE.match(Path(file).name)
    if m:
        return {"doc_type": "syllabus", "subject_code": m.group(1).upper(), "module_id": None}
    if any(w in Path(file).stem.lower() for w in _REG_WORDS):
        return {"doc_type": "regulation", "subject_code": None, "module_id": None}
    return {"doc_type": "other", "subject_code": None, "module_id": None}


def make_filter(mode, selection=None):
    """Predicate on a chunk dict. Regulation mode: regulation documents only.
    Syllabus mode: syllabus documents of the chosen subject; if a document is split into
    modules, only the chosen module's pages (documents without module ranges match any module)."""
    if mode == "Regulation":
        return lambda c: c.get("doc_type") == "regulation"
    code = ((selection or {}).get("subject_code") or "").upper()
    module = (selection or {}).get("module_id")

    def ok(c):
        if c.get("doc_type") != "syllabus":
            return False
        if code and (c.get("subject_code") or "").upper() != code:
            return False
        if module and c.get("module_id") not in (None, module):
            return False
        return True
    return ok


def scope_label(mode, selection=None):
    if mode == "Regulation":
        return "the academic regulations"
    if selection and selection.get("subject"):
        return f"{selection['subject']} — {selection.get('module', '')}".rstrip(" —")
    return "the syllabus"
