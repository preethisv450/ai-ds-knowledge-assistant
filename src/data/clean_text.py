"""D6: strip running headers and footers so they do not pollute retrieval.

Most official PDFs repeat a line at the top or bottom of every page: the college name,
a document title, "Page 4 of 30". Those lines are in every chunk, which wastes the
embedding and makes unrelated pages look similar to each other. Removing them is a
small change that measurably tidies up retrieval.

A line is treated as boilerplate only when it repeats on most pages and sits within the
first or last few lines of the page, so a genuine heading that happens to appear twice
survives.
"""
import re
from collections import Counter

EDGE_LINES = 3          # how many lines at the top and bottom of a page count as the margin
MIN_PAGES = 3           # below this there is not enough evidence to call anything repeated
MIN_SHARE = 0.6         # a line must appear on at least this share of pages
PAGE_NUMBER = re.compile(r"^\s*(?:page\s*)?\d{1,4}\s*(?:/|of)?\s*\d{0,4}\s*$", re.IGNORECASE)


SHORT_LINE_WORDS = 8     # only short lines get their numbers normalised


def _norm(line):
    """Compare lines ignoring the page number inside them, so 'Page 3 of 30' matches 'Page 4 of 30'.

    Only short lines are normalised this way. A long sentence that differs only in a
    number is still a different sentence, and must not be mistaken for a running footer."""
    line = line.strip().lower()
    return re.sub(r"\d+", "#", line) if len(line.split()) <= SHORT_LINE_WORDS else line


def _edge_width(n_lines, edge_lines):
    """How many lines at each end count as the margin.

    Never more than a quarter of the page, so that on a short page the body cannot be
    mistaken for a running header."""
    return max(1, min(edge_lines, n_lines // 4))


def find_boilerplate(pages, edge_lines=EDGE_LINES, min_share=MIN_SHARE):
    """pages: [(page_number, text)]. Returns the set of normalised lines to drop."""
    if len(pages) < MIN_PAGES:
        return set()
    counts = Counter()
    for _, text in pages:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        w = _edge_width(len(lines), edge_lines)
        edge = lines[:w] + lines[-w:]
        for ln in set(_norm(x) for x in edge if x):
            counts[ln] += 1
    threshold = max(MIN_PAGES - 1, int(len(pages) * min_share))
    return {ln for ln, n in counts.items() if n >= threshold and ln}


def strip_boilerplate(pages, edge_lines=EDGE_LINES, min_share=MIN_SHARE):
    """Return (cleaned_pages, report). Page numbers are dropped from the margins too."""
    drop = find_boilerplate(pages, edge_lines, min_share)
    removed = Counter()
    cleaned = []
    for page_no, text in pages:
        lines = [ln for ln in text.splitlines()]
        keep, n = [], len([l for l in lines if l.strip()])
        w = _edge_width(n, edge_lines)
        idx = 0
        for ln in lines:
            stripped = ln.strip()
            if stripped:
                idx += 1
            at_edge = idx <= w or idx > n - w
            if stripped and at_edge and (_norm(stripped) in drop or PAGE_NUMBER.match(stripped)):
                removed[stripped] += 1
                continue
            keep.append(ln)
        body = "\n".join(keep).strip()
        if body:
            cleaned.append((page_no, body))
    return cleaned, {"removed_lines": dict(removed), "patterns": sorted(drop)}
