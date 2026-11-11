"""D6: the RAG chain. answer(question, mode, selection) -> {"answer": str, "sources": [...]}.

retrieve -> build prompt with numbered context -> Gemini -> answer + sources.
The return shape is what the UI's get_answer() promises; never raises for expected
problems (no index, Gemini down) - it returns a friendly message instead.

D7 will add the similarity threshold / "not found" fallback, D8 will use `selection`
to scope retrieval to the chosen subject/module.
"""
from src.backend.config import TOP_K

NO_INDEX_MSG = ("The knowledge base has not been built yet. "
                "Ask the team to run `python scripts/build_index.py`.")
EMPTY_MSG = "Please type a question."


def answer(question, mode="Syllabus", selection=None, k=TOP_K, retrieve_fn=None, generate_fn=None):
    if not question or not question.strip():
        return {"answer": EMPTY_MSG, "sources": []}

    if retrieve_fn is None:
        from src.backend.retrieval import retrieve as retrieve_fn
    if generate_fn is None:
        from src.backend.gemini_client import generate as generate_fn
    from src.backend.gemini_client import GeminiError
    from src.backend.prompts import answer_prompt
    from src.backend.retrieval import to_sources

    try:
        chunks = retrieve_fn(question, k=k)
    except FileNotFoundError:
        return {"answer": NO_INDEX_MSG, "sources": []}

    system, prompt = answer_prompt(question, chunks, mode)
    try:
        text = generate_fn(prompt, system=system)
    except GeminiError as e:
        return {"answer": e.user_message, "sources": []}

    return {"answer": text, "sources": to_sources(chunks)}
