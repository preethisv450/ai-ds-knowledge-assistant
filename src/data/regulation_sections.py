"""D3: split the regulation PDF into sections, keeping page numbers.

A regulation document is one long PDF, but students ask about one rule at a time
("what attendance do I need?"). Splitting it into named sections with their page
numbers gives the evaluation set something to check citations against, and gives the
report a table of what the document actually covers.

    from src.data.regulation_sections import split_regulation
    sections = split_regulation("data/pdfs/Academic_Regulations.pdf")
"""
import json
import re
from pathlib import Path

from src.backend.ingest import extract_pages
from src.data.schema import REGULATION_TOPICS

# "4.2 Attendance", "CHAPTER III - EXAMINATIONS", "ATTENDANCE"
NUMBERED = re.compile(r"^\s*((?:\d{1,2}\.){0,3}\d{1,2})[\.\)]?\s+([A-Z][^.]{3,80})$")
CHAPTERED = re.compile(r"^\s*(?:chapter|section|part)\s+([IVXLC\d]+)\s*[-–:.]?\s*(.{3,80})$", re.IGNORECASE)
# "Attendance. A student must have at least 75 percent ..." - a lead-in phrase acting as a heading
INLINE_LEAD = re.compile(r"^([A-Z][A-Za-z\-]{2,}(?:\s+[A-Za-z\-&]{2,}){0,3})\.\s+(?=[A-Z0-9])")
MIN_SECTION_WORDS = 12


def _is_allcaps_heading(line):
    letters = [c for c in line if c.isalpha()]
    return (3 <= len(line.split()) <= 10 and len(letters) >= 6
            and sum(c.isupper() for c in letters) / len(letters) > 0.85 and not line.endswith("."))


def detect_heading(line):
    """Return (number_or_None, title) when the line looks like a heading, else None."""
    line = line.strip()
    if not line or len(line) > 90:
        return None
    m = CHAPTERED.match(line)
    if m:
        return m.group(1), m.group(2).strip(" -–:.")
    m = NUMBERED.match(line)
    if m and not m.group(2).rstrip().endswith((",", ";")):
        return m.group(1), m.group(2).strip(" -–:.")
    if _is_allcaps_heading(line):
        return None, line.strip(" -–:.").title()
    return None


def split_inline_heading(line, min_rest_words=8):
    """'Attendance. A student must ...' -> ('Attendance', 'A student must ...'), else None.
    Only fires when a real paragraph follows, so ordinary sentences are left alone."""
    line = line.strip()
    m = INLINE_LEAD.match(line)
    if not m:
        return None
    rest = line[m.end():].strip()
    if len(rest.split()) < min_rest_words:
        return None
    return m.group(1).strip(), rest


def topic_for(title, body=""):
    """Map a heading to one of the agreed topic keys (attendance, examination, ...)."""
    hay = f"{title} {body[:400]}".lower()
    best, best_hits = None, 0
    for key, words in REGULATION_TOPICS.items():
        hits = sum(w in hay for w in words)
        # a word in the title counts double: the heading says what the section is about
        hits += sum(w in title.lower() for w in words)
        if hits > best_hits:
            best, best_hits = key, hits
    return best


def split_regulation(pdf_path, min_words=MIN_SECTION_WORDS):
    """Return [{"number","title","topic","first_page","last_page","text","word_count"}].

    Text before the first heading becomes a 'Preamble' section so nothing is lost."""
    pdf_path = Path(pdf_path)
    pages = extract_pages(pdf_path)
    if not pages:
        return []

    def new_section(number, title, page, first_line=""):
        return {"number": number, "title": title, "first_page": page,
                "lines": [first_line] if first_line else [], "content_page": page}

    sections, current = [], new_section(None, "Preamble", pages[0][0])
    for page_no, text in pages:
        for line in text.splitlines():
            head, rest = detect_heading(line), ""
            if head is None:
                inline = split_inline_heading(line)
                if inline and current["lines"]:   # a new lead-in only starts a section mid-document
                    head, rest = (None, inline[0]), inline[1]
                else:
                    if line.strip():
                        current["lines"].append(line.strip())
                        current["content_page"] = page_no   # where this section's text really ends
                    continue
            current["last_page"] = current["content_page"]   # not page_no: that is the next section's page
            sections.append(current)
            current = new_section(head[0], head[1], page_no, rest)
    current["last_page"] = current["content_page"]
    sections.append(current)

    out = []
    for s in sections:
        body = " ".join(s["lines"]).strip()
        if len(body.split()) < min_words:          # a heading with almost nothing under it
            if out:                                 # fold it into the previous section
                out[-1]["text"] = (out[-1]["text"] + " " + s["title"] + " " + body).strip()
                out[-1]["last_page"] = s["last_page"]
                out[-1]["word_count"] = len(out[-1]["text"].split())
            continue
        out.append({
            "number": s["number"],
            "title": s["title"],
            "topic": topic_for(s["title"], body),
            "first_page": s["first_page"],
            "last_page": s["last_page"],
            "text": body,
            "word_count": len(body.split()),
        })
    return out


def coverage(sections):
    """Which of the expected regulation topics were found, and which are missing."""
    found = {s["topic"] for s in sections if s["topic"]}
    return {"found": sorted(found), "missing": sorted(set(REGULATION_TOPICS) - found)}


def save(sections, path, source_file=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"source_file": source_file, "sections": sections}, indent=2) + "\n")
    return path
