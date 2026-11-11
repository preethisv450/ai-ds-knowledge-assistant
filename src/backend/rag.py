"""D6 + D7: the RAG chain. answer(question, mode, selection) -> {"answer": str, "sources": [...]}.

retrieve -> drop weak chunks -> "not found" if nothing relevant -> prompt -> Gemini ->
keep only the sources the answer actually cites.

Never raises for expected problems (no index, Gemini down): returns a friendly message.
D8: `mode` and `selection` scope retrieval (Regulation -> regulation documents only;
Syllabus -> the chosen subject/module).
"""
import re

from src.backend import config
from src.backend.catalog import make_filter, scope_label
from src.backend.prompts import NOT_FOUND

NOT_FOUND_MSG = NOT_FOUND + " Try rephrasing your question, or check that the right subject and module are selected."
NO_INDEX_MSG = ("The knowledge base has not been built yet. "
                "Ask the team to run `python scripts/build_index.py`.")
EMPTY_MSG = "Please type a question."
NO_DOCS_MSG = "No documents have been added yet for {scope}. Please ask the team to add them."

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


def _dedupe_by_page(chunks):
    seen, out = set(), []
    for c in chunks:  # chunks are best-first, so the first per page is the best
        key = (c["document"].lower(), c["page"])
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def select_sources(answer_text, chunks):
    """Sources the answer actually cites; if it cites none we can match, show the pages we gave it."""
    unique = _dedupe_by_page(chunks)
    cited = parse_citations(answer_text)
    matched = [c for c in unique if (c["document"].lower(), c["page"]) in cited]
    return matched or unique


def answer(question, mode="Syllabus", selection=None, k=None, min_score=None,
           retrieve_fn=None, generate_fn=None):
    if not question or not question.strip():
        return {"answer": EMPTY_MSG, "sources": []}

    k = k or config.TOP_K
    min_score = config.RAG_MIN_SCORE if min_score is None else min_score
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

    return {"answer": text, "sources": to_sources(select_sources(text, chunks))}
