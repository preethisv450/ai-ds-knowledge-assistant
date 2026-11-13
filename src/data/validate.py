"""D4: check the data before it is handed over.

Two kinds of finding:
  error   - will break the app or give wrong answers. Fix before handing over.
  warning - worth looking at, but the app still works.

    from src.data.validate import validate_all
    findings = validate_all()          # [] means everything passed
"""
import json
from pathlib import Path

from src.backend.config import PDF_DIR, ROOT
from src.data.schema import (MAX_CREDITS, MODULE_ID, SUBJECT_CODE, iter_modules, iter_subjects,
                             subject_of_module)

CURRICULUM_PATH = ROOT / "data" / "processed" / "curriculum.json"
MANIFEST_PATH = ROOT / "data" / "processed" / "documents.json"


def _f(level, where, message):
    return {"level": level, "where": where, "message": message}


def load_json(path, what):
    path = Path(path)
    if not path.exists():
        return None, [_f("error", path.name, f"{what} not found at {path}")]
    try:
        return json.loads(path.read_text()), []
    except json.JSONDecodeError as e:
        return None, [_f("error", path.name, f"not valid JSON: {e}")]


def validate_curriculum(curriculum):
    """Structure, naming and completeness of the Year -> Semester -> Subject -> Module tree."""
    out = []
    if not isinstance(curriculum, dict):
        return [_f("error", "curriculum.json", "top level must be an object")]
    if "schema_version" not in curriculum:
        out.append(_f("warning", "curriculum.json", "no schema_version field"))
    years = curriculum.get("years")
    if not isinstance(years, list) or not years:
        return out + [_f("error", "curriculum.json", "'years' must be a non-empty list")]

    seen_codes, seen_modules, seen_names = {}, {}, {}
    for year, sem, subject in iter_subjects(curriculum):
        where = f"{year} / {sem}"
        code = (subject.get("code") or "").strip()
        name = (subject.get("name") or "").strip()
        if not code:
            out.append(_f("error", where, "a subject has no code"))
        elif not SUBJECT_CODE.match(code.upper()):
            out.append(_f("warning", where, f"subject code {code!r} does not match the agreed pattern (e.g. AI201)"))
        if code:
            if code.upper() in seen_codes:
                out.append(_f("error", where, f"subject code {code} is used twice (also in {seen_codes[code.upper()]})"))
            else:
                seen_codes[code.upper()] = where
        if not name:
            out.append(_f("error", where, f"subject {code or '?'} has no name"))
        else:
            if name != subject.get("name"):
                out.append(_f("warning", where, f"subject name {subject['name']!r} has stray spaces"))
            key = name.lower()
            if key in seen_names and seen_names[key] != name:
                out.append(_f("warning", where, f"{name!r} and {seen_names[key]!r} differ only by case"))
            seen_names[key] = name
        credits = subject.get("credits")
        if credits is not None and (not isinstance(credits, (int, float)) or not 0 < credits <= MAX_CREDITS):
            out.append(_f("error", where, f"{code}: credits {credits!r} should be a number between 1 and {MAX_CREDITS}"))

        modules = subject.get("modules")
        if not isinstance(modules, list) or not modules:
            out.append(_f("error", where, f"subject {code or name} has no modules"))
            continue
        numbers = []
        for module in modules:
            mid = (module.get("id") or "").strip()
            title = (module.get("title") or "").strip()
            if not mid:
                out.append(_f("error", where, f"{code}: a module has no id"))
                continue
            m = MODULE_ID.match(mid.upper())
            if not m:
                out.append(_f("error", where, f"module id {mid!r} should look like {code}-M1"))
            else:
                numbers.append(int(m.group(2)))
                if code and subject_of_module(mid) != code.upper():
                    out.append(_f("error", where, f"module {mid} does not belong to subject {code}"))
            if mid.upper() in seen_modules:
                out.append(_f("error", where, f"module id {mid} is used twice (also in {seen_modules[mid.upper()]})"))
            else:
                seen_modules[mid.upper()] = where
            if not title:
                out.append(_f("error", where, f"module {mid} has no title"))
            if not module.get("topics"):
                out.append(_f("warning", where, f"module {mid} has no topics listed"))
        if numbers and sorted(numbers) != list(range(1, len(numbers) + 1)):
            out.append(_f("warning", where, f"{code}: module numbers are {sorted(numbers)}, expected 1..{len(numbers)}"))
    return out


def validate_manifest(manifest, curriculum=None, pdf_dir=PDF_DIR):
    """Every listed file exists, page ranges make sense, codes and modules are real."""
    from src.backend.ingest import extract_pages
    out = []
    if not manifest:
        return [_f("warning", "documents.json", "no manifest: documents will be labelled from their file names only")]
    known_codes = {(s.get("code") or "").upper() for _, _, s in iter_subjects(curriculum or {})}
    known_modules = {(m.get("id") or "").upper() for _, _, _, m in iter_modules(curriculum or {})}

    for name, entry in manifest.items():
        file = entry.get("file", name)
        path = Path(pdf_dir) / file
        if not path.exists():
            out.append(_f("error", file, "listed in documents.json but not found in data/pdfs"))
            continue
        try:
            page_count = max((p for p, _ in extract_pages(path)), default=0)
        except Exception as e:
            out.append(_f("error", file, f"could not be read: {type(e).__name__}"))
            continue
        if page_count == 0:
            out.append(_f("error", file, "no selectable text - it may be a scan and need OCR"))
        code = (entry.get("subject_code") or "").upper()
        if code and curriculum and code not in known_codes:
            out.append(_f("error", file, f"subject_code {code} is not in curriculum.json"))
        ranges = (entry.get("modules") or {})
        if entry.get("doc_type", "syllabus") == "syllabus" and code and not ranges:
            out.append(_f("warning", file, "no module page ranges: module-scoped search will fall back to the whole document"))
        covered = []
        for mid, rng in sorted(ranges.items()):
            if curriculum and mid.upper() not in known_modules:
                out.append(_f("error", file, f"module {mid} is not in curriculum.json"))
            if code and subject_of_module(mid) not in (None, code):
                out.append(_f("error", file, f"module {mid} does not belong to subject {code}"))
            first, last = rng
            if last > page_count:
                out.append(_f("error", file, f"module {mid} ends on page {last} but the file has {page_count} pages"))
            covered.append((first, last, mid))
        covered.sort()
        for (f1, l1, m1), (f2, _, m2) in zip(covered, covered[1:]):
            if f2 <= l1:
                out.append(_f("error", file, f"modules {m1} and {m2} both claim page {f2}"))
        if covered:
            pages_used = {p for f1, l1, _ in covered for p in range(f1, l1 + 1)}
            missing = sorted(set(range(1, page_count + 1)) - pages_used)
            if missing:
                out.append(_f("warning", file, f"pages {missing} belong to no module and will not be found in module-scoped search"))
    return out


def validate_coverage(curriculum, manifest):
    """Which subjects in the curriculum have no document behind them."""
    out = []
    documented = {(e.get("subject_code") or "").upper() for e in (manifest or {}).values()}
    for year, sem, subject in iter_subjects(curriculum or {}):
        code = (subject.get("code") or "").upper()
        if code and code not in documented:
            out.append(_f("warning", f"{year} / {sem}", f"{code} {subject.get('name', '')}: no syllabus PDF listed in documents.json"))
    if not any(e.get("doc_type") == "regulation" for e in (manifest or {}).values()):
        out.append(_f("error", "documents.json", "no regulation document listed - Regulation mode will find nothing"))
    return out


def validate_all(curriculum_path=CURRICULUM_PATH, manifest_path=MANIFEST_PATH, pdf_dir=PDF_DIR):
    from src.backend.catalog import load_manifest
    curriculum, problems = load_json(curriculum_path, "curriculum.json")
    if curriculum is None:
        return problems
    findings = problems + validate_curriculum(curriculum)
    try:
        manifest = load_manifest(manifest_path)
    except ValueError as e:
        return findings + [_f("error", "documents.json", str(e))]
    findings += validate_manifest(manifest, curriculum, pdf_dir)
    findings += validate_coverage(curriculum, manifest)
    return findings


def counts(findings):
    return {"errors": sum(f["level"] == "error" for f in findings),
            "warnings": sum(f["level"] == "warning" for f in findings)}
