"""Answer service boundary.

Day 6: stub implementation so the chat UI can be built and demoed.
When Pragna's function lands, replace the body of get_answer() only.
The return shape must not change.
"""

import time


def get_answer(question, mode, selection=None):
    """Answer a question.

    Args:
        question: the user's question text
        mode: "Syllabus" or "Regulation"
        selection: the sidebar selection dict, or None

    Returns:
        {
            "answer": str,                     # markdown
            "sources": [                       # may be empty
                {"document": str, "page": int, "snippet": str},
            ],
        }
    """
    time.sleep(1.0)  # stand-in for retrieval + generation latency

    scope = "the academic regulations"
    if mode == "Syllabus" and selection:
        scope = f"{selection['subject']} — {selection['module']}"

    return {
        "answer": (
            f"**Placeholder answer** for: _{question}_\n\n"
            f"This would be answered from {scope}."
        ),
                "sources": [
            {
                "document": "AI_Syllabus.pdf" if mode == "Syllabus"
                            else "Academic_Regulations.pdf",
                "page": 4,
                "snippet": "Placeholder source snippet text.",
            }
        ],
    }