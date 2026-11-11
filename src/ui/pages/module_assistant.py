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
        sum_new = st.checkbox("Rewrite it (skip the saved summary)", key="sum_new")
        if st.button("Generate summary", key="btn_summary"):
            from src.backend.study import generate_summary  # imported here so the page loads without backend deps

            with st.spinner("Writing the summary..."):
                st.session_state[cache_key] = generate_summary(selection, refresh=sum_new)
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
        q_new = st.checkbox("Make a new set (skip the saved one)", key="q_new")
        if st.button("Generate questions", key="btn_questions"):
            from src.backend.study import generate_questions  # imported here so the page loads without backend deps

            with st.spinner("Writing questions..."):
                st.session_state[q_key] = generate_questions(selection, q_type, int(q_count), refresh=q_new)
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
        quiz_n = st.number_input("Number of questions", min_value=1, max_value=15, value=5, key="quiz_n")
        quiz_key = f"quiz_{selection['module_id']}"
        quiz_new = st.checkbox("Make a new quiz (skip the saved one)", key="quiz_new")
        if st.button("Start quiz", key="btn_quiz"):
            from src.backend.study import generate_quiz  # imported here so the page loads without backend deps

            with st.spinner("Writing the quiz..."):
                st.session_state[quiz_key] = generate_quiz(selection, int(quiz_n), refresh=quiz_new)
            st.session_state[quiz_key + "_done"] = False
            for i in range(15):
                st.session_state.pop(f"{quiz_key}_a{i}", None)
        quiz = st.session_state.get(quiz_key)
        if quiz:
            if not quiz["quiz"]:
                st.warning(quiz["message"])
            else:
                done = st.session_state.get(quiz_key + "_done", False)
                for i, item in enumerate(quiz["quiz"]):
                    st.markdown(f"**Q{i + 1}. {item['question']}**")
                    choice = st.radio("Choose one", range(4), index=None, key=f"{quiz_key}_a{i}",
                                      format_func=lambda j, it=item: it["options"][j],
                                      label_visibility="collapsed", disabled=done)
                    if done:
                        if choice == item["correct_index"]:
                            st.success("Correct. " + item["explanation"])
                        else:
                            st.error(f"Correct answer: {item['options'][item['correct_index']]}. " + item["explanation"])
                if not done:
                    if st.button("Submit answers", key=quiz_key + "_submit"):
                        st.session_state[quiz_key + "_done"] = True
                        st.rerun()
                else:
                    score = sum(st.session_state.get(f"{quiz_key}_a{i}") == it["correct_index"]
                                for i, it in enumerate(quiz["quiz"]))
                    st.subheader(f"Score: {score} / {len(quiz['quiz'])}")
                if quiz["sources"]:
                    with st.expander("Sources used"):
                        for src in quiz["sources"]:
                            st.markdown(f"**{src['document']}**, page {src['page']}")