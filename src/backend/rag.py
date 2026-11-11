"""D6 + D7: the RAG chain. answer(question, mode, selection) -> {"answer": str, "sources": [...]}.

retrieve -> drop weak chunks -> "not found" if nothing relevant -> prompt -> Gemini ->
keep only the sources the answer actually cites.

Never raises for expected problems (no index, Gemini down): returns a friendly message.
D8: `mode` and `selection` scope retrieval (Regulation -> regulation documents only;
Syllabus -> the chosen subject/module).
"""
import re

from src.backend import config
from src.backend.cache import AUTO, index_fingerprint, make_key, resolve
from src.backend.catalog import make_filter, scope_label
from src.backend.prompts import NOT_FOUND

NOT_FOUND_MSG = NOT_FOUND + " Try rephrasing your question, or check that the right subject and module are selected."
NO_INDEX_MSG = ("The knowledge base has not been built yet. "
                "Ask the team to run `python scripts/build_index.py`.")
EMPTY_MSG = "Please type a question."
NO_DOCS_MSG = "No documents have been added yet for {scope}. Please ask the team to add them."

_MARKER = re.compile(r"\[S(\d+(?:\s*[,;]\s*S?\d+)*)\](?:\s*\[S\d+(?:\s*[,;]\s*S?\d+)*\])*")
_MARKER_NUMS = re.compile(r"S?(\d+)")
_PAREN = re.compile(r"\(([^()]*\.pdf[^()]*)\)", re.IGNORECASE)
_FILE = re.compile(r"([^\s,;()\[\]]+\.pdf)", re.IGNORECASE)


def parse_citations(text):
    """Return {(document_lowercase, page), ...} for citations like (file.pdf, p.3) / (file.pdf, page 3, 5)."""
    cited = set()
    for group in _PAREN.findall(text or ""):
        for part in group.split(";"):
            m = _FILE.search(part)
            if not m:
                continue
            for num in re.findall(r"\d+", part[m.end():]):
                cited.add((m.group(1).lower(), int(num)))
    return cited


def _marker_numbers(group_text, n_chunks):
    """Distinct valid context numbers (1..n) in a run of markers like '[S1][S3]' or '[S1, S3]'."""
    seen = []
    for m in _MARKER_NUMS.finditer(group_text):
        k = int(m.group(1))
        if 1 <= k <= n_chunks and k not in seen:
            seen.append(k)
    return seen


def render_citations(text, chunks):
    """Replace [S2] markers with (file.pdf, p.N); markers pointing at nothing are removed."""
    def repl(m):
        pages = []
        for k in _marker_numbers(m.group(0), len(chunks)):
            c = chunks[k - 1]
            label = f"{c['document']}, p.{c['page']}"
            if label not in pages:
                pages.append(label)
        return "(" + "; ".join(pages) + ")" if pages else ""
    out = _MARKER.sub(repl, text or "")
    return re.sub(r"[ \t]+([.,;:!?])", r"\1", re.sub(r" {2,}", " ", out)).strip()


def _dedupe_by_page(chunks):
    seen, out = set(), []
    for c in chunks:  # chunks are best-first, so the first per page is the best
        key = (c["document"].lower(), c["page"])
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def select_sources(answer_text, chunks):
    """Sources the answer cites. Prefer [S#] markers (reliable); else file/page text citations;
    if neither matches a retrieved chunk, show the pages we gave the model."""
    unique = _dedupe_by_page(chunks)
    numbered = []
    for m in _MARKER.finditer(answer_text or ""):
        for k in _marker_numbers(m.group(0), len(chunks)):
            numbered.append(chunks[k - 1])
    if numbered:
        return _dedupe_by_page(numbered)
    cited = parse_citations(answer_text)
    matched = [c for c in unique if (c["document"].lower(), c["page"]) in cited]
    return matched or unique


def answer(question, mode="Syllabus", selection=None, k=None, min_score=None,
           retrieve_fn=None, generate_fn=None, cache=AUTO):
    if not question or not question.strip():
        return {"answer": EMPTY_MSG, "sources": []}

    k = k or config.TOP_K
    min_score = config.RAG_MIN_SCORE if min_score is None else min_score
    cache = resolve(cache, retrieve_fn, generate_fn)
    key = None
    if cache:
        sel = selection or {}
        key = make_key("answer", " ".join(question.lower().split()), mode, sel.get("subject_code"),
                       sel.get("module_id"), k, min_score, index_fingerprint())
        hit = cache.get("answer", key)
        if hit:
            return hit
    if retrieve_fn is None:
        from src.backend.retrieval import retrieve as retrieve_fn
    if generate_fn is None:
        from src.backend.gemini_client import generate as generate_fn
    from src.backend.gemini_client import GeminiError
    from src.backend.prompts import answer_prompt
    from src.backend.retrieval import to_sources

    try:
        results = retrieve_fn(question, k=k, where=make_filter(mode, selection))
    except FileNotFoundError:
        return {"answer": NO_INDEX_MSG, "sources": []}

    if not results:  # the scope (subject/module or regulations) has no documents in the index
        return {"answer": NO_DOCS_MSG.format(scope=scope_label(mode, selection)), "sources": []}

    chunks = [c for c in results if c["score"] >= min_score]
    if not chunks:  # nothing relevant enough: do not even call Gemini
        return {"answer": NOT_FOUND_MSG, "sources": []}

    system, prompt = answer_prompt(question, chunks, mode, scope=scope_label(mode, selection))
    try:
        text = generate_fn(prompt, system=system)
    except GeminiError as e:
        return {"answer": e.user_message, "sources": []}

    if text.strip().startswith(NOT_FOUND):  # the model itself found nothing in the context
        return {"answer": NOT_FOUND_MSG, "sources": []}

    result = {"answer": render_citations(text, chunks), "sources": to_sources(select_sources(text, chunks))}
    if cache and key:
        cache.put("answer", key, result)
    return result
