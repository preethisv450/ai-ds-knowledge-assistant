
import streamlit as st
from src.ui.sidebar import render_sidebar

st.set_page_config(
    page_title="AI & DS Knowledge Assistant",
    layout="wide"
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

st.title("AI & DS Knowledge Assistant")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Page",
    [
        "Home",
        "Module Assistant",
        "Regulation Chatbot",
        "Knowledge Network",
        "Timetable"
    ]
)
selection = render_sidebar()

if page == "Home":
    st.header("Welcome!")
    st.write(
        "Your AI-powered academic knowledge assistant."
    )

    st.info(
        "Select a feature from the sidebar to get started."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📚 Module Assistant")
        st.write(
            "Explore subjects, modules, summaries and questions."
        )

    with col2:
        st.subheader("💬 Regulation Chatbot")
        st.write(
            "Ask questions about academic regulations."
        )

elif page == "Module Assistant":
    from src.ui.pages.module_assistant import show_module_assistant
    show_module_assistant()

elif page == "Regulation Chatbot":
    from src.ui.pages.regulation_chatbot import show_regulation_chatbot
    show_regulation_chatbot()

elif page == "Knowledge Network":
    from src.ui.pages.knowledge_network import show_knowledge_network
    show_knowledge_network()

elif page == "Timetable":
    from src.ui.pages.timetable import show_timetable
    show_timetable()
