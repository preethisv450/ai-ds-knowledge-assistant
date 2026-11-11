"""D11/D12: study helpers for the Module Assistant.
  generate_summary(selection)            -> {"summary", "sources"}
  generate_questions(selection, type, n) -> {"questions", "message", "sources"}
  generate_quiz(selection, n)            -> {"quiz", "message", "sources"}   (D13)

Same contract style as rag.answer: never raises for expected problems; a friendly message goes
in "summary" and "sources" is []. Reuses retrieval scoping (D8), marker citations (D7/D9)
and Gemini error handling (D5).
"""
import random

from src.backend import config
from src.backend.cache import AUTO, index_fingerprint, make_key, resolve
from src.backend.catalog import make_filter, scope_label
from src.backend.prompts import NOT_FOUND
from src.backend.rag import (NO_DOCS_MSG, NO_INDEX_MSG, NOT_FOUND_MSG, render_citations,
                             select_sources)

SUMMARY_K = 8
QUESTIONS_K = 8
MAX_QUESTIONS = 20
QUIZ_K = 8
MAX_QUIZ = 15
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


def _cache_key(selection, kind, *params):
    sel = selection or {}
    return make_key(kind, sel.get("subject_code"), sel.get("module_id"), sel.get("subject"), sel.get("module"),
                    params, index_fingerprint())


def generate_summary(selection, k=SUMMARY_K, min_score=None, retrieve_fn=None, generate_fn=None,
                     refresh=False, cache=AUTO):
    cache = resolve(cache, retrieve_fn, generate_fn)
    key = _cache_key(selection, "summary", k, min_score) if _topic(selection)[1] else None
    if cache and key and not refresh:
        hit = cache.get("summary", key)
        if hit:
            return hit
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
    result = {"summary": render_citations(text, chunks), "sources": to_sources(select_sources(text, chunks))}
    if cache and key:
        cache.put("summary", key, result)
    return result


def _clamp(n, top, default=5):
    try:
        return max(1, min(int(n), top))
    except (TypeError, ValueError):
        return default


def normalize_qtype(qtype):
    """'Short answer' / 'short' -> 'short'; 'Long answer' / 'long' -> 'long'. Anything else -> 'short'."""
    return "long" if str(qtype or "").strip().lower().startswith("long") else "short"


def generate_questions(selection, qtype="short", n=5, difficulty="medium", k=QUESTIONS_K,
                       min_score=None, retrieve_fn=None, generate_json_fn=None,
                       refresh=False, cache=AUTO):
    """Practice questions with model answers for one module.
    Returns {"questions": [{"question", "model_answer"}], "message": str, "sources": [...]}.
    On any expected problem "questions" is [] and "message" says why (friendly text)."""
    cache = resolve(cache, retrieve_fn, generate_json_fn)
    key = _cache_key(selection, "questions", normalize_qtype(qtype), _clamp(n, MAX_QUESTIONS), difficulty, k, min_score) \
        if _topic(selection)[1] else None
    if cache and key and not refresh:
        hit = cache.get("questions", key)
        if hit:
            return hit
    chunks, problem = _gather(selection, k, min_score, retrieve_fn)
    if problem:
        return {"questions": [], "message": problem, "sources": []}
    if generate_json_fn is None:
        from src.backend.gemini_client import generate_json as generate_json_fn
    from src.backend.gemini_client import GeminiError
    from src.backend.prompts import questions_prompt, validate_questions
    from src.backend.retrieval import to_sources

    n = _clamp(n, MAX_QUESTIONS)
    subject, module = _topic(selection)
    system, prompt = questions_prompt(subject, module, chunks, qtype=normalize_qtype(qtype), n=n,
                                      difficulty=difficulty)
    try:
        data = generate_json_fn(prompt, system=system, validate=validate_questions)
    except GeminiError as e:
        return {"questions": [], "message": e.user_message, "sources": []}
    items = [{"question": str(q["question"]).strip(), "model_answer": str(q["model_answer"]).strip()}
             for q in data][:n]
    result = {"questions": items, "message": "", "sources": to_sources(chunks)}
    if cache and key:
        cache.put("questions", key, result)
    return result


def _shuffle_options(item, rng):
    """Models tend to put the right answer in the same slot; shuffle and remap correct_index."""
    correct = item["options"][item["correct_index"]]
    options = list(item["options"])
    rng.shuffle(options)
    return {"question": str(item["question"]).strip(), "options": [str(o).strip() for o in options],
            "correct_index": options.index(correct), "explanation": str(item["explanation"]).strip()}


def generate_quiz(selection, n=5, k=QUIZ_K, min_score=None, retrieve_fn=None, generate_json_fn=None, rng=None,
                  refresh=False, cache=AUTO):
    """Multiple-choice quiz for one module.
    Returns {"quiz": [{"question", "options": [4], "correct_index": 0-3, "explanation"}],
             "message": str, "sources": [...]}. On any expected problem "quiz" is [] and
    "message" says why."""
    cache = resolve(cache, retrieve_fn, generate_json_fn)
    key = _cache_key(selection, "quiz", _clamp(n, MAX_QUIZ), k, min_score) if _topic(selection)[1] else None
    if cache and key and not refresh:
        hit = cache.get("quiz", key)
        if hit:
            return hit
    chunks, problem = _gather(selection, k, min_score, retrieve_fn)
    if problem:
        return {"quiz": [], "message": problem, "sources": []}
    if generate_json_fn is None:
        from src.backend.gemini_client import generate_json as generate_json_fn
    from src.backend.gemini_client import GeminiError
    from src.backend.prompts import quiz_prompt, validate_quiz
    from src.backend.retrieval import to_sources

    n = _clamp(n, MAX_QUIZ)
    subject, module = _topic(selection)
    system, prompt = quiz_prompt(subject, module, chunks, n=n)
    try:
        data = generate_json_fn(prompt, system=system, validate=validate_quiz)
    except GeminiError as e:
        return {"quiz": [], "message": e.user_message, "sources": []}
    rng = rng or random.Random()
    quiz = [_shuffle_options(q, rng) for q in data[:n]]
    result = {"quiz": quiz, "message": "", "sources": to_sources(chunks)}
    if cache and key:
        cache.put("quiz", key, result)
    return result
