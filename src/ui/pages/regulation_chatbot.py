import streamlit as st
from src.ui.answer_service import get_answer

MODES = ["Syllabus", "Regulation"]

EXAMPLE_QUESTIONS = {
    "Syllabus": [
        "What are the main topics in this module?",
        "Explain the key concepts with an example.",
        "What should I revise first?",
    ],
    "Regulation": [
        "What is the minimum attendance requirement?",
        "How many backlogs are allowed to move up a year?",
        "What is the passing mark for internal assessment?",
    ],
}


def _scope_label(mode, selection):
    if mode == "Syllabus" and selection:
        return f"Syllabus · {selection['subject']} — {selection['module']}"
    return "Regulation"


def _render_sources(sources):
    if not sources:
        st.caption("No source passages were returned for this answer.")
        return

    labels = ", ".join(
        f"{s['document']} (p. {s['page']})" for s in sources
    )
    st.caption(f"Sources: {labels}")

    with st.expander("View source passages"):
        for i, s in enumerate(sources):
            st.markdown(f"**{s['document']}** — page {s['page']}")
            st.markdown(f"> {s['snippet']}")
            if i < len(sources) - 1:
                st.divider()


def show_regulation_chatbot():

    st.subheader("Chat")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    left, right = st.columns([4, 1])

    with left:
        mode = st.radio(
            "Mode",
            MODES,
            horizontal=True,
            label_visibility="collapsed",
            key="chat_mode",
        )

    with right:
        if st.button(
            "Clear chat",
            use_container_width=True,
            disabled=not st.session_state["chat_messages"],
        ):
            st.session_state["chat_messages"] = []
            st.rerun()

    selection = st.session_state.get("selection")
    blocked = mode == "Syllabus" and not selection

    if mode == "Syllabus":
        if selection:
            st.caption(
                f"Answering from {selection['subject']} — "
                f"{selection['module']} ({selection['module_id']})"
            )
        else:
            st.caption("Pick a module in the sidebar to scope syllabus questions.")
    else:
        st.caption("Answering from academic regulations and policy documents.")

    st.divider()

    if not st.session_state["chat_messages"]:
        st.info("Ask a question below, or try one of these:")
        for i, example in enumerate(EXAMPLE_QUESTIONS[mode]):
            if st.button(
                example,
                key=f"example_{mode}_{i}",
                use_container_width=True,
                disabled=blocked,
            ):
                st.session_state["pending_question"] = example
                st.rerun()

    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            if message.get("is_error"):
                st.error(message["content"])
            else:
                st.markdown(message["content"])

            if message.get("scope"):
                st.caption(message["scope"])

            if message["role"] == "assistant" and not message.get("is_error"):
                _render_sources(message.get("sources"))

    typed = st.chat_input(
        "Pick a module first..." if blocked else "Type your question here...",
        disabled=blocked,
    )

    question = typed or st.session_state.pop("pending_question", None)

    if question:
        st.session_state["chat_messages"].append(
            {
                "role": "user",
                "content": question,
                "scope": _scope_label(mode, selection),
            }
        )

        try:
            with st.spinner("Searching documents and writing an answer..."):
                result = get_answer(question, mode, selection)
        except Exception as exc:
            st.session_state["chat_messages"].append(
                {
                    "role": "assistant",
                    "content": (
                        "I couldn't answer that just now. The AI service may be "
                        "unavailable or out of quota — try again in a moment.\n\n"
                        f"`{type(exc).__name__}: {exc}`"
                    ),
                    "is_error": True,
                }
            )
        else:
            answer_text = (result.get("answer") or "").strip()
            if not answer_text:
                answer_text = (
                    "I couldn't find anything relevant in the documents for that "
                    "question. Try rephrasing it, or check you've picked the right "
                    "module in the sidebar."
                )

            st.session_state["chat_messages"].append(
                {
                    "role": "assistant",
                    "content": answer_text,
                    "sources": result.get("sources", []),
                }
            )

        st.rerun()