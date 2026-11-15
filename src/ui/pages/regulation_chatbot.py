import streamlit as st
from src.ui.answer_service import get_answer

MODES = ["Syllabus", "Regulation"]


def _scope_label(mode, selection):
    if mode == "Syllabus" and selection:
        return f"Syllabus · {selection['subject']} — {selection['module']}"
    return "Regulation"


def _render_sources(sources):
    if not sources:
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
        st.info("Ask a question below to start the conversation.")

    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("scope"):
                st.caption(message["scope"])
            _render_sources(message.get("sources"))

    blocked = mode == "Syllabus" and not selection

    question = st.chat_input(
        "Pick a module first..." if blocked else "Type your question here...",
        disabled=blocked,
    )

    if question:
        st.session_state["chat_messages"].append(
            {
                "role": "user",
                "content": question,
                "scope": _scope_label(mode, selection),
            }
        )

        with st.spinner("Thinking..."):
            result = get_answer(question, mode, selection)

        st.session_state["chat_messages"].append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
            }
        )

        st.rerun()