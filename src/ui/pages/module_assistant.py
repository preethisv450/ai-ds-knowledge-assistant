import streamlit as st


def show_module_assistant():

    selection = st.session_state.get("selection")

    if not selection:
        st.warning("Choose a year, semester, subject and module in the sidebar.")
        return

        st.subheader(f"{selection['subject']} — {selection['module']}")
    st.caption(
        f"{selection['year']} · {selection['semester']} · "
        f"{selection['subject_code']} · {selection['module_id']}"
    )
    st.divider()

    tab_summary, tab_qa, tab_questions, tab_quiz = st.tabs(
        ["Summary", "Q&A", "Questions", "Quiz"]
    )

    with tab_summary:
        st.write("Generate a structured summary of this module.")
        st.button("Generate summary", disabled=True, key="btn_summary")
        st.caption("Connects to Pragna's summary function on Day 11.")

    with tab_qa:
        st.write("Ask a question about this module.")
        st.chat_input("Ask about this module...", disabled=True, key="qa_input")
        st.caption("Connects to the syllabus chatbot on Day 8.")

    with tab_questions:
        st.write("Generate practice questions for this module.")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Type", ["Short answer", "Long answer"],
                         disabled=True, key="q_type")
        with col2:
            st.number_input("How many", min_value=1, max_value=20, value=5,
                            disabled=True, key="q_count")
        st.button("Generate questions", disabled=True, key="btn_questions")
        st.caption("Connects to Pragna's question generator on Day 12.")

    with tab_quiz:
        st.write("Take a multiple-choice quiz on this module.")
        st.button("Start quiz", disabled=True, key="btn_quiz")
        st.caption("Connects to Pragna's quiz generator on Day 13.")