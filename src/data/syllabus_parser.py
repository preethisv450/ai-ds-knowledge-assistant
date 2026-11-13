"""D2: turn a syllabus PDF into a draft structured record for hand-correction.

Real syllabus PDFs are laid out differently by every department, so this is a draft
generator, not a finished parser. It finds what it can, marks what it guessed in
`_review`, and leaves the rest for a human to fix. Running it on a new PDF and editing
the result is much faster than typing the whole subject by hand.

    from src.data.syllabus_parser import parse_syllabus
    draft = parse_syllabus("data/pdfs/AI201_syllabus.pdf")
"""
import re
from pathlib import Path

from src.backend.ingest import extract_pages
from src.data.schema import MODULE_ID, SUBJECT_CODE, module_id_for

# "Module 3", "MODULE-3", "Unit IV", "UNIT 2 :"
MODULE_HEAD = re.compile(
    r"^\s*(?:module|unit)\s*[-–:]?\s*(\d{1,2}|[ivxIVX]{1,5})\b[\s:.\-–]*(.*)$", re.IGNORECASE)
CODE_IN_TEXT = re.compile(r"\b([A-Z]{2,4}\d{3}[A-Z]?)\b")
# "3:0:0:3", "L-T-P-C 3-0-0-3", "Credits: 4"
CREDITS_LTPC = re.compile(r"\b(\d)\s*[:\-]\s*(\d)\s*[:\-]\s*(\d)\s*[:\-]\s*(\d)\b")
CREDITS_WORD = re.compile(r"\bcredits?\s*[:\-]?\s*(\d{1,2})\b", re.IGNORECASE)
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10}
_NOISE = re.compile(r"^(page\s*\d+|\d+)$", re.IGNORECASE)


def _module_number(token):
    token = token.strip().lower()
    return int(token) if token.isdigit() else ROMAN.get(token)


def _split_topics(text, max_topics=40):
    """Topics are usually comma or semicolon separated inside a module's body."""
    body = re.sub(r"\s+", " ", text).strip(" .;,")
    if not body:
        return []
    parts = re.split(r"\s*[;,]\s*|\s+[·•]\s+", body)
    topics, seen = [], set()
    for p in parts:
        p = p.strip(" .;:-–").strip()
        if not (2 <= len(p.split()) <= 8) or len(p) < 4 or _NOISE.match(p):
            continue
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        topics.append(p)
        if len(topics) >= max_topics:
            break
    return topics


_TRAILING = re.compile(r"[\s\-–:|]*(syllabus|course\s+plan|scheme|curriculum)\s*$", re.IGNORECASE)


def _guess_name(lines, code):
    """The subject name is a short title line near the top, usually on the same line as the code."""
    best, best_score = "", -1
    for i, line in enumerate(lines[:10]):
        line = line.strip()
        if not line or _NOISE.match(line):
            continue
        has_code = bool(code) and re.search(r"\b" + re.escape(code) + r"\b", line, re.IGNORECASE)
        cleaned = re.sub(r"\b" + re.escape(code) + r"\b", "", line, flags=re.IGNORECASE) if code else line
        cleaned = _TRAILING.sub("", cleaned).strip(" -:–|,.")
        words = cleaned.split()
        if not (2 <= len(words) <= 12) or len(cleaned) < 4:
            continue
        if sum(c.isalpha() or c.isspace() for c in cleaned) / len(cleaned) < 0.8:
            continue
        if cleaned.endswith("."):          # a sentence, not a title
            continue
        score = (40 if has_code else 0) + (10 - i) + (6 if len(words) <= 6 else 0)
        if score > best_score:
            best, best_score = cleaned, score
    return best


def parse_syllabus(pdf_path, subject_code=None):
    """Return a draft subject record:
        {"code", "name", "credits", "modules": [{"id","title","topics","pages"}],
         "source_file", "_review": [...]}
    `_review` lists what a human must check. An empty list does not mean it is perfect."""
    pdf_path = Path(pdf_path)
    # headers are kept on purpose: the running title is often where the subject name lives
    pages = extract_pages(pdf_path, strip_headers=False)
    review = []
    if not pages:
        return {"code": subject_code, "name": "", "modules": [], "source_file": pdf_path.name,
                "_review": ["no selectable text in this PDF - it may be scanned and need OCR"]}

    all_lines = [(p, ln.strip()) for p, text in pages for ln in text.splitlines() if ln.strip()]
    first_page_lines = [ln for p, ln in all_lines if p == pages[0][0]]

    code = (subject_code or "").upper()
    if not code:
        stem = CODE_IN_TEXT.search(pdf_path.stem.upper())
        found = stem.group(1) if stem else None
        if not found:
            hits = CODE_IN_TEXT.findall(" ".join(first_page_lines).upper())
            found = hits[0] if hits else None
        code = found or ""
        review.append("subject code guessed from the file name or first page" if code
                      else "no subject code found - fill in 'code' by hand")
    if code and not SUBJECT_CODE.match(code):
        review.append(f"subject code {code!r} does not match the agreed pattern (e.g. AI201)")

    name = _guess_name(first_page_lines, code)
    if not name:
        review.append("subject name not found - fill in 'name' by hand")
    else:
        review.append("subject name guessed from the first page - check it reads correctly")

    head = " ".join(first_page_lines)
    credits = None
    m = CREDITS_LTPC.search(head)
    if m:
        credits = int(m.group(4))
    else:
        m = CREDITS_WORD.search(head)
        if m:
            credits = int(m.group(1))
    if credits is None:
        review.append("credits not found - add 'credits' by hand if the syllabus states them")

    # --- modules: a heading line starts a module, everything until the next one is its body
    starts = []
    for page, line in all_lines:
        m = MODULE_HEAD.match(line)
        if not m:
            continue
        n = _module_number(m.group(1))
        if n and not any(n == s[0] for s in starts):
            starts.append((n, page, (m.group(2) or "").strip(" .:-–"), line))

    modules = []
    if not starts:
        review.append("no 'Module N' or 'Unit N' headings found - add the modules by hand")
    else:
        bodies = {n: [] for n, _, _, _ in starts}
        current, heads = None, {s[3] for s in starts}
        for page, line in all_lines:
            if line in heads:
                current = next(n for n, _, _, h in starts if h == line)
                continue
            if current is not None:
                bodies[current].append(line)
        for i, (n, page, title, _) in enumerate(sorted(starts)):
            nxt = sorted(starts)[i + 1][1] if i + 1 < len(starts) else None
            last_page = (nxt - 1 if nxt > page else page) if nxt else pages[-1][0]
            topics = _split_topics(" ".join(bodies[n]))
            if not title:
                title = topics[0] if topics else f"Module {n}"
                review.append(f"module {n} has no title on its heading line - using a guess")
            modules.append({
                "id": module_id_for(code or "XX000", n),
                "title": title,
                "topics": topics,
                "pages": [page, last_page],
            })
            if not topics:
                review.append(f"module {n} has no topics - add them by hand")

    return {"code": code or None, "name": name, "credits": credits, "modules": modules,
            "source_file": pdf_path.name, "_review": review}


def to_curriculum_entry(draft):
    """Strip the draft-only fields so the record can be pasted into curriculum.json."""
    return {
        "code": draft.get("code"),
        "name": draft.get("name"),
        **({"credits": draft["credits"]} if draft.get("credits") is not None else {}),
        "source_file": draft.get("source_file"),
        "modules": [{"id": m["id"], "title": m["title"], **({"topics": m["topics"]} if m.get("topics") else {})}
                    for m in draft.get("modules", [])],
    }


def module_pages(draft):
    """{module_id: [first_page, last_page]} - what the manifest (D7) needs."""
    return {m["id"]: list(m["pages"]) for m in draft.get("modules", []) if m.get("pages")}
