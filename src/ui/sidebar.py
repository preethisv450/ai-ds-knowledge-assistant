import streamlit as st
from src.ui.data_loader import get_curriculum, get_module_meta

# Last chosen Year / Semester / Subject / Module. The selectors now live on the
# Module Assistant page instead of a sidebar that was always on screen, so the
# choice is remembered here to survive switching pages.
_SAVED = "curriculum_choice"


def _choose(label, options, saved_value, parent_matches, key, show_controls):
    """One cascading dropdown. Falls back to the first option when the parent changed."""
    options = list(options)
    index = options.index(saved_value) if (parent_matches and saved_value in options) else 0
    if show_controls:
        return st.selectbox(label, options, index=index, key=key)
    return options[index]


def render_sidebar(show_controls=True):
    """Resolve the curriculum selection and store it in st.session_state["selection"].

    Kept under its original name so existing imports keep working. There is no
    sidebar any more: with show_controls=True the four dropdowns are drawn where
    this is called (Module Assistant page); with show_controls=False the same
    selection is resolved without drawing anything (every other page).
    """
    curriculum = get_curriculum()
    saved = st.session_state.get(_SAVED, {})

    if show_controls:
        st.markdown('<div class="cur-title">Select Curriculum</div>', unsafe_allow_html=True)

    year = _choose("Year", curriculum.keys(), saved.get("year"), True,
                   "cur_year", show_controls)

    semesters = curriculum[year]
    same_year = saved.get("year") == year
    semester = _choose("Semester", semesters.keys(), saved.get("semester"), same_year,
                       f"cur_semester|{year}", show_controls)

    subjects = semesters[semester]
    same_sem = same_year and saved.get("semester") == semester
    subject = _choose("Subject", subjects.keys(), saved.get("subject"), same_sem,
                      f"cur_subject|{year}|{semester}", show_controls)

    modules = subjects[subject]
    same_subject = same_sem and saved.get("subject") == subject
    module = _choose("Module", modules, saved.get("module"), same_subject,
                     f"cur_module|{year}|{semester}|{subject}", show_controls)

    code, module_id = get_module_meta(year, semester, subject, module)

    selection = {
        "year": year,
        "semester": semester,
        "subject": subject,
        "subject_code": code,
        "module": module,
        "module_id": module_id,
    }
    st.session_state[_SAVED] = {
        "year": year, "semester": semester, "subject": subject, "module": module,
    }
    st.session_state["selection"] = selection

    return selection