"""D11: study helpers for the Module Assistant. generate_summary(selection) -> {"summary", "sources"}.

Same contract style as rag.answer: never raises for expected problems; a friendly message goes
in "summary" and "sources" is []. Reuses retrieval scoping (D8), marker citations (D7/D9)
and Gemini error handling (D5).
"""
from src.backend import config
from src.backend.catalog import make_filter, scope_label
from src.backend.prompts import NOT_FOUND
from src.backend.rag import (NO_DOCS_MSG, NO_INDEX_MSG, NOT_FOUND_MSG, render_citations,
                             select_sources)

SUMMARY_K = 8
NEED_MODULE_MSG = "Please choose a subject and a module first."


def _topic(selection):
    sel = selection or {}
    return sel.get("subject") or "", sel.get("module") or ""


def generate_summary(selection, k=SUMMARY_K, min_score=None, retrieve_fn=None, generate_fn=None):
    subject, module = _topic(selection)
    if not module:
        return {"summary": NEED_MODULE_MSG, "sources": []}

    min_score = config.RAG_MIN_SCORE if min_score is None else min_score
    if retrieve_fn is None:
        from src.backend.retrieval import retrieve as retrieve_fn
    if generate_fn is None:
        from src.backend.gemini_client import generate as generate_fn
    from src.backend.gemini_client import GeminiError
    from src.backend.prompts import summary_prompt
    from src.backend.retrieval import to_sources

    try:
        results = retrieve_fn(f"{subject} {module}".strip(), k=k, where=make_filter("Syllabus", selection))
    except FileNotFoundError:
        return {"summary": NO_INDEX_MSG, "sources": []}
    if not results:
        return {"summary": NO_DOCS_MSG.format(scope=scope_label("Syllabus", selection)), "sources": []}

    chunks = [c for c in results if c["score"] >= min_score]
    if not chunks:
        return {"summary": NOT_FOUND_MSG, "sources": []}

    system, prompt = summary_prompt(subject, module, chunks)
    try:
        text = generate_fn(prompt, system=system)
    except GeminiError as e:
        return {"summary": e.user_message, "sources": []}

    if text.strip().startswith(NOT_FOUND):
        return {"summary": NOT_FOUND_MSG, "sources": []}
    return {"summary": render_citations(text, chunks), "sources": to_sources(select_sources(text, chunks))}
