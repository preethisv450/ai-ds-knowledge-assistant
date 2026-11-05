import streamlit as st


def show_module_assistant():

    st.title("📚 Module Assistant")

    selection = st.session_state.get("selection")

    if not selection:
        st.warning("Choose a year, semester, subject and module in the sidebar.")
        return

    st.subheader(f"{selection['subject']} — {selection['module']}")
    st.caption(f"{selection['year']} · {selection['semester']}")

    st.info("Content tabs arrive on Day 3.") 