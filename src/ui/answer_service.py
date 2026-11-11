"""Answer service boundary.

D6: wired to Pragna's RAG backend (src/backend/rag.py). The signature and the return
shape are unchanged from the Day 6 stub, so the chat UI needs no changes.
"""


def get_answer(question, mode, selection=None):
    """Answer a question.

    Args:
        question: the user's question text.
        mode: "Syllabus" or "Regulation".
        selection: the sidebar selection dict, or None.

    Returns:
        {
            "answer": str,                     # markdown
            "sources": [                       # may be empty
                {"document": str, "page": int, "snippet": str},
            ],
        }
    """
    from src.backend.rag import answer  # imported here so the UI still loads if the backend is missing deps

    return answer(question, mode, selection)
