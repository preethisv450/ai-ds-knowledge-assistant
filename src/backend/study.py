"""D11/D12: study helpers for the Module Assistant.
  generate_summary(selection)            -> {"summary", "sources"}
  generate_questions(selection, type, n) -> {"questions", "message", "sources"}

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
QUESTIONS_K = 8
MAX_QUESTIONS = 20
NEED_MODULE_MSG = "Please choose a subject and a module first."


def _topic(selection):
    sel = selection or {}
    return sel.get("subject") or "", sel.get("module") or ""


def _gather(selection, k, min_score, retrieve_fn):
    """Retrieve the module's chunks. Returns (chunks, None) or (None, friendly_message)."""
    subject, module = _topic(selection)
    if not module:
        return None, NEED_MODULE_MSG
    min_score = config.RAG_MIN_SCORE if min_score is None else min_score
    if retrieve_fn is None:
        from src.backend.retrieval import retrieve as retrieve_fn
    try:
        results = retrieve_fn(f"{subject} {module}".strip(), k=k, where=make_filter("Syllabus", selection))
    except FileNotFoundError:
        return None, NO_INDEX_MSG
    if not results:
        return None, NO_DOCS_MSG.format(scope=scope_label("Syllabus", selection))
    chunks = [c for c in results if c["score"] >= min_score]
    return (chunks, None) if chunks else (None, NOT_FOUND_MSG)


def generate_summary(selection, k=SUMMARY_K, min_score=None, retrieve_fn=None, generate_fn=None):
    chunks, problem = _gather(selection, k, min_score, retrieve_fn)
    if problem:
        return {"summary": problem, "sources": []}
    if generate_fn is None:
        from src.backend.gemini_client import generate as generate_fn
    from src.backend.gemini_client import GeminiError
    from src.backend.prompts import summary_prompt
    from src.backend.retrieval import to_sources

    subject, module = _topic(selection)
    system, prompt = summary_prompt(subject, module, chunks)
    try:
        text = generate_fn(prompt, system=system)
    except GeminiError as e:
        return {"summary": e.user_message, "sources": []}
    if text.strip().startswith(NOT_FOUND):
        return {"summary": NOT_FOUND_MSG, "sources": []}
    return {"summary": render_citations(text, chunks), "sources": to_sources(select_sources(text, chunks))}


def normalize_qtype(qtype):
    """'Short answer' / 'short' -> 'short'; 'Long answer' / 'long' -> 'long'. Anything else -> 'short'."""
    return "long" if str(qtype or "").strip().lower().startswith("long") else "short"


def generate_questions(selection, qtype="short", n=5, difficulty="medium", k=QUESTIONS_K,
                       min_score=None, retrieve_fn=None, generate_json_fn=None):
    """Practice questions with model answers for one module.
    Returns {"questions": [{"question", "model_answer"}], "message": str, "sources": [...]}.
    On any expected problem "questions" is [] and "message" says why (friendly text)."""
    chunks, problem = _gather(selection, k, min_score, retrieve_fn)
    if problem:
        return {"questions": [], "message": problem, "sources": []}
    if generate_json_fn is None:
        from src.backend.gemini_client import generate_json as generate_json_fn
    from src.backend.gemini_client import GeminiError
    from src.backend.prompts import questions_prompt, validate_questions
    from src.backend.retrieval import to_sources

    try:
        n = max(1, min(int(n), MAX_QUESTIONS))
    except (TypeError, ValueError):
        n = 5
    subject, module = _topic(selection)
    system, prompt = questions_prompt(subject, module, chunks, qtype=normalize_qtype(qtype), n=n,
                                      difficulty=difficulty)
    try:
        data = generate_json_fn(prompt, system=system, validate=validate_questions)
    except GeminiError as e:
        return {"questions": [], "message": e.user_message, "sources": []}
    items = [{"question": str(q["question"]).strip(), "model_answer": str(q["model_answer"]).strip()}
             for q in data][:n]
    return {"questions": items, "message": "", "sources": to_sources(chunks)}
