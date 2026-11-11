import streamlit as st
from src.ui.answer_service import get_answer

MODES = ["Syllabus", "Regulation"]


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

    question = st.chat_input("Type your question here...")

    if question:
        st.session_state["chat_messages"].append(
            {"role": "user", "content": question}
        )

        with st.spinner("Thinking..."):
            result = get_answer(question, mode, selection)

        st.session_state["chat_messages"].append(
            {"role": "assistant", "content": result["answer"]}
        )

        st.rerun()