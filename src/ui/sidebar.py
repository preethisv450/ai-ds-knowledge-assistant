import streamlit as st
from src.ui.stub_data import get_curriculum


def render_sidebar():
    curriculum = get_curriculum()

    st.sidebar.markdown("---")
    st.sidebar.header("📘 Select Curriculum")

    year = st.sidebar.selectbox("Year", list(curriculum.keys()))

    semesters = curriculum[year]
    semester = st.sidebar.selectbox("Semester", list(semesters.keys()))

    subjects = semesters[semester]
    subject = st.sidebar.selectbox("Subject", list(subjects.keys()))

    modules = subjects[subject]
    module = st.sidebar.selectbox("Module", modules)

    selection = {
        "year": year,
        "semester": semester,
        "subject": subject,
        "module": module,
    }
    st.session_state["selection"] = selection

    return selection