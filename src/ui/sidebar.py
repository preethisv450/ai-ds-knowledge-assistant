import streamlit as st
from src.ui.data_loader import get_curriculum, get_module_meta, load_curriculum

# Last chosen Year / Semester / Subject / Module. The selectors now live on the
# Module Assistant page instead of a sidebar that was always on screen, so the
# choice is remembered here to survive switching pages.
_SAVED = "curriculum_choice"


def first_indexed_choice(curriculum, indexed_codes, code_of):
    """First (year, semester, subject) whose subject has documents in the knowledge base, else None.

    Without this the app opens on the first subject in the curriculum, which may have no documents
    yet and would answer "No documents have been added" on the very first screen."""
    for year, semesters in curriculum.items():
        for semester, subjects in semesters.items():
            for subject in subjects:
                if code_of(year, semester, subject) in indexed_codes:
                    return year, semester, subject
    return None


def _indexed_subject_codes():
    try:
        from src.backend.catalog import load_manifest
        return {e.get("subject_code") for e in load_manifest().values() if e.get("doc_type") == "syllabus"} - {None}
    except Exception:  # the choice of default must never break the page
        return set()


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
    if not saved:  # first visit: start on a subject that has documents
        _, index = load_curriculum()
        first = first_indexed_choice(curriculum, _indexed_subject_codes(),
                                     lambda y, s, n: index[(y, s, n)]["code"])
        if first:
            saved = {"year": first[0], "semester": first[1], "subject": first[2]}

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