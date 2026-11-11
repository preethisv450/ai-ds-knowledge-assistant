import streamlit as st
from src.ui.data_loader import get_curriculum, get_module_meta


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

    code, module_id = get_module_meta(year, semester, subject, module)

    selection = {
        "year": year,
        "semester": semester,
        "subject": subject,
        "subject_code": code,
        "module": module,
        "module_id": module_id,
    }
    st.session_state["selection"] = selection

    return selection