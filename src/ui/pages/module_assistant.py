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
        cache_key = f"summary_{selection['module_id']}"
        if st.button("Generate summary", key="btn_summary"):
            from src.backend.study import generate_summary  # imported here so the page loads without backend deps

            with st.spinner("Writing the summary..."):
                st.session_state[cache_key] = generate_summary(selection)
        result = st.session_state.get(cache_key)
        if result:
            st.markdown(result["summary"])
            if result["sources"]:
                with st.expander("Sources"):
                    for src in result["sources"]:
                        st.markdown(f"**{src['document']}**, page {src['page']}")
                        st.caption(src["snippet"])

    with tab_qa:
        st.write("Ask a question about this module.")
        st.chat_input("Ask about this module...", disabled=True, key="qa_input")
        st.caption("Connects to the syllabus chatbot on Day 8.")

    with tab_questions:
        st.write("Generate practice questions for this module.")
        col1, col2 = st.columns(2)
        with col1:
            q_type = st.selectbox("Type", ["Short answer", "Long answer"], key="q_type")
        with col2:
            q_count = st.number_input("How many", min_value=1, max_value=20, value=5, key="q_count")
        q_key = f"questions_{selection['module_id']}"
        if st.button("Generate questions", key="btn_questions"):
            from src.backend.study import generate_questions  # imported here so the page loads without backend deps

            with st.spinner("Writing questions..."):
                st.session_state[q_key] = generate_questions(selection, q_type, int(q_count))
        q_result = st.session_state.get(q_key)
        if q_result:
            if not q_result["questions"]:
                st.warning(q_result["message"])
            for i, item in enumerate(q_result["questions"], 1):
                st.markdown(f"**Q{i}. {item['question']}**")
                with st.expander("Model answer"):
                    st.markdown(item["model_answer"])
            if q_result["sources"]:
                with st.expander("Sources used"):
                    for src in q_result["sources"]:
                        st.markdown(f"**{src['document']}**, page {src['page']}")

    with tab_quiz:
        st.write("Take a multiple-choice quiz on this module.")
        st.button("Start quiz", disabled=True, key="btn_quiz")
        st.caption("Connects to Pragna's quiz generator on Day 13.")