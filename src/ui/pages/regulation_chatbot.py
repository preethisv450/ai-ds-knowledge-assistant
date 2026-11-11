import streamlit as st
from src.ui.answer_service import get_answer

MODES = ["Syllabus", "Regulation"]


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

    mode = st.radio(
        "Mode",
        MODES,
        horizontal=True,
        label_visibility="collapsed",
        key="chat_mode",
    )

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

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []

    for message in st.session_state["chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            _render_sources(message.get("sources"))

    question = st.chat_input("Type your question here...")

    if question:
        st.session_state["chat_messages"].append(
            {"role": "user", "content": question}
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