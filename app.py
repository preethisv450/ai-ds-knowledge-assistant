import streamlit as st
from src.ui.sidebar import render_sidebar
from src.ui.theme import (
    apply_theme,
    feature_card,
    home_hero,
    network_side_panels,
    page_header,
    page_marker,
    render_bottom_nav,
    render_header,
)

st.set_page_config(
    page_title="AI & DS Knowledge Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
)



@st.cache_resource
def _warm_up_backend():
    """D16: load the embedding model and the index in the background so the first question is fast."""
    try:
        from src.backend.warmup import start_background
        return start_background()
    except Exception:
        return None


_warm_up_backend()

apply_theme()
render_header()

page = render_bottom_nav()

if page != "Module Assistant":
    # Resolve the curriculum selection without drawing the dropdowns, so the
    # chatbot can still scope syllabus answers to the chosen module.
    selection = render_sidebar(show_controls=False)

if page == "Home":
    page_marker("home")
    home_hero(
        "AI &amp; DS Knowledge Assistant",
        "Your AI-powered academic companion for AI &amp; DS.",
    )

    features = [
        ("module", "Module Assistant", "Module Assistant",
         "Access summaries, practice questions and quizzes for each module."),
        ("chatbot", "Regulation Chatbot", "Regulation Chatbot",
         "Ask questions about academic regulations, policies and curriculum."),
        ("network", "Knowledge Network", "Knowledge Network",
         "Explore the relationships between concepts visually."),
        ("timetable", "Timetable", "Timetable",
         "View and manage your class schedule."),
    ]
    for row in (features[:2], features[2:]):
        cols = st.columns(2)
        for col, (slug, icon, title, description) in zip(cols, row):
            with col:
                feature_card(slug, icon, title, description, target=title)

elif page == "Module Assistant":
    page_marker("module")
    page_header(
        "Module Assistant",
        "Module Assistant",
        "Summaries, practice questions and quizzes for each module.",
    )
    from src.ui.pages.module_assistant import show_module_assistant

    with st.container(key="module_layout"):
        left, right = st.columns([1, 3], gap="medium")
        with left:
            with st.container(key="curriculum_panel"):
                selection = render_sidebar(show_controls=True)
        with right:
            with st.container(key="module_main"):
                show_module_assistant()

elif page == "Regulation Chatbot":
    page_marker("chat")
    page_header(
        "Regulation Chatbot",
        "Regulation Chatbot",
        "Get instant answers on syllabus, regulations and academic policies.",
    )
    from src.ui.pages.regulation_chatbot import show_regulation_chatbot
    show_regulation_chatbot()

elif page == "Knowledge Network":
    page_marker("network")
    page_header(
        "Knowledge Network",
        "Knowledge Network",
        "Visualize and explore the relationship between key concepts.",
    )
    from src.ui.pages.knowledge_network import show_knowledge_network

    with st.container(key="network_layout"):
        left, right = st.columns([3, 1.3], gap="medium")
        with left:
            with st.container(key="graph_panel"):
                show_knowledge_network()
        with right:
            network_side_panels()

elif page == "Timetable":
    page_marker("timetable")
    page_header("Timetable", "Timetable")
    from src.ui.pages.timetable import show_timetable
    show_timetable()