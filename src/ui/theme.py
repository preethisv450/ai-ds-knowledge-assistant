"""Shared visual theme: navy header, fixed bottom navigation, page chrome.

UI only. Nothing in here touches data, backend, session selection or page logic.
Pages are styled from the outside with CSS, using a hidden marker element
(`page_marker`) so the page modules themselves do not need to change.

Needs Streamlit >= 1.39 (keyed containers, st-key-* classes).
"""

from urllib.parse import quote

import streamlit as st

PAGES = [
    "Home",
    "Module Assistant",
    "Regulation Chatbot",
    "Knowledge Network",
    "Timetable",
]

# Simple line icons (24x24 grid, stroke only).
ICONS = {
    "Home": '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    "Module Assistant": '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>',
    "Regulation Chatbot": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "Knowledge Network": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 13.5 6.8 4M15.4 6.5l-6.8 4"/>',
    "Timetable": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/>',
    "logo": '<path d="M22 10 12 5 2 10l10 5z"/><path d="M6 12v5c3 2 9 2 12 0v-5"/><path d="M22 10v6"/>',
}


def _svg(name, size=24, stroke=1.8):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'
    )


def _mask_uri(name):
    raw = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#000" '
        f'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )
    return "data:image/svg+xml;utf8," + quote(raw)


_CSS = """
:root{
  --navy:#0F2A62; --navy-2:#173A82; --blue-50:#F0F4FB; --blue-100:#E2EBF9; --blue-200:#C9D8F2;
  --bg:#F3F6FB; --card:#FFFFFF; --line:#DCE3EF; --text:#18233A; --muted:#66758E;
  --hdr-h:56px; --nav-h:72px; --radius:12px;
}
html, body, [data-testid="stApp"]{background:var(--bg);}
[data-testid="stApp"], [data-testid="stApp"] *{font-family:"Inter","Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;}
[data-testid="stIconMaterial"], .material-icons, [class*="material-symbols"]{font-family:"Material Symbols Rounded","Material Icons" !important;}

/* No sidebar, no default Streamlit header */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"],
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], footer{display:none !important;}

[data-testid="stMainBlockContainer"]{
  max-width:1180px; padding:calc(var(--hdr-h) + 24px) 24px calc(var(--nav-h) + 40px) !important;
}

/* Elements that only carry markup (header, markers) take no layout space */
[data-testid="stElementContainer"]:has(.app-header){height:0; min-height:0; margin:0 0 -1rem 0;}
[data-testid="stElementContainer"]:has(.pg-marker){display:none;}

/* Header */
.app-header{position:fixed; top:0; left:0; right:0; height:var(--hdr-h); background:var(--navy); color:#fff;
  display:flex; align-items:center; gap:12px; padding:0 20px; z-index:1001;
  box-shadow:0 2px 10px rgba(15,42,98,.28);}
.app-header svg{width:30px; height:30px; flex:none; color:#fff;}
.app-header .brand{font-size:.92rem; font-weight:700; line-height:1.15; letter-spacing:.01em; color:#fff;}

/* Bottom navigation (relies on role/data-testid hooks, not Streamlit's generated class names) */
.st-key-bottom_nav{position:fixed !important; left:0; right:0; bottom:0; width:100% !important; max-width:100% !important; box-sizing:border-box; z-index:1000; background:#fff;
  border-top:1px solid var(--line); box-shadow:0 -2px 14px rgba(15,42,98,.08);
  padding:6px 12px calc(6px + env(safe-area-inset-bottom)) !important; gap:0 !important;}
.st-key-bottom_nav [data-testid="stWidgetLabel"]{display:none !important;}
.st-key-bottom_nav [data-testid="stElementContainer"], .st-key-bottom_nav [data-testid="stRadio"]{width:100% !important;}
.st-key-bottom_nav [role="radiogroup"]{display:grid !important; grid-template-columns:repeat(5,minmax(0,1fr)); gap:4px;
  max-width:880px; margin:0 auto; width:100%;}
.st-key-bottom_nav [role="radiogroup"] > *{display:flex; min-width:0;}
.st-key-bottom_nav [role="radiogroup"] label{flex:1; display:flex !important; flex-direction:column; align-items:center;
  justify-content:flex-start; gap:3px; margin:0 !important; padding:8px 4px 7px !important; border-radius:10px;
  cursor:pointer; color:var(--muted); min-width:0; transition:background .15s, color .15s;}
.st-key-bottom_nav [role="radiogroup"] label > div{display:flex; flex-direction:column; align-items:center; justify-content:center;}
.st-key-bottom_nav [role="radiogroup"] label div:has(+ [data-testid="stMarkdownContainer"]), .st-key-bottom_nav label[data-baseweb="radio"] > div:first-child{display:none !important;}
.st-key-bottom_nav [role="radiogroup"] label:hover{background:var(--blue-50); color:var(--navy);}
.st-key-bottom_nav [role="radiogroup"] label::before{content:""; width:22px; height:22px; flex:none; background-color:currentColor;
  -webkit-mask:var(--ico) center/contain no-repeat; mask:var(--ico) center/contain no-repeat;}
.st-key-bottom_nav [role="radiogroup"] label p{font-size:.74rem; font-weight:500; line-height:1.15; margin:0; text-align:center; color:inherit !important;}
.st-key-bottom_nav [role="radiogroup"] label:has(input:checked){background:var(--blue-100); color:var(--navy);}
.st-key-bottom_nav [role="radiogroup"] label:has(input:checked) p{font-weight:700;}
/*NAV_ICONS*/

/* Page header */
.page-hd{display:flex; align-items:center; gap:14px; margin:2px 0 18px;}
.page-hd .ic{width:46px; height:46px; border-radius:12px; background:var(--blue-100); color:var(--navy);
  display:flex; align-items:center; justify-content:center; flex:none;}
.page-hd .ic svg{width:24px; height:24px;}
.page-hd h1{margin:0; padding:0 !important; font-size:1.55rem; font-weight:700; color:var(--navy); line-height:1.2;}
.page-hd p{margin:2px 0 0; color:var(--muted); font-size:.95rem;}

/* Typography */
h1, h2, h3, h4{color:var(--navy); font-weight:700; letter-spacing:-.005em;}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li{color:var(--text);}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p{color:var(--muted) !important;}
hr{border-color:var(--line) !important;}

/* Buttons */
.stButton > button, .stDownloadButton > button{border-radius:8px; border:1px solid var(--blue-200); background:#fff;
  color:var(--navy); font-weight:600; padding:.45rem 1rem; transition:background .15s, border-color .15s, color .15s;}
.stButton > button:hover{background:var(--blue-50); border-color:var(--navy); color:var(--navy);}
.stButton > button:focus-visible{outline:2px solid var(--navy-2); outline-offset:2px;}
.stButton > button:disabled{background:#F4F6FA; color:#9AA6BA; border-color:var(--line);}
.stButton > button[kind="primary"]{background:var(--navy); color:#fff; border-color:var(--navy);}

/* Inputs */
[data-testid="stWidgetLabel"] p{font-weight:600; font-size:.84rem; color:var(--text);}
[data-testid="stSelectbox"] [role="group"], [data-baseweb="select"] > div, [data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stNumberInputContainer"]{
  border-radius:8px !important; border:1px solid var(--line) !important; background:#fff !important;}
[data-testid="stSelectbox"], [data-baseweb="select"]{max-width:100%;}
[data-baseweb="select"] > div{box-sizing:border-box;}
[data-testid="stSelectbox"] [role="group"]:hover, [data-baseweb="select"] > div:hover{border-color:var(--navy-2) !important;}

/* Expanders, alerts */
[data-testid="stExpander"] details{border:1px solid var(--line); border-radius:10px; background:#fff;}
[data-testid="stExpander"] summary{font-weight:600; color:var(--navy);}
[data-testid="stAlert"]{border-radius:10px;}

/* Home */
.hero{background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:22px 26px; margin-bottom:18px;
  box-shadow:0 1px 2px rgba(15,42,98,.05);}
.hero h1{margin:0; padding:0 !important; font-size:1.8rem; color:var(--navy);}
.hero p{margin:6px 0 0; color:var(--muted); font-size:1rem;}
[class*="st-key-card_"]{background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:20px 22px 18px !important;
  box-shadow:0 1px 2px rgba(15,42,98,.05); min-height:176px; transition:box-shadow .18s, border-color .18s, transform .18s;}
[class*="st-key-card_"]:hover{box-shadow:0 6px 18px rgba(15,42,98,.12); border-color:var(--blue-200); transform:translateY(-1px);}
.fc{display:flex; gap:16px; align-items:flex-start; margin-bottom:16px;}
.fc .ic{width:52px; height:52px; border-radius:14px; background:var(--blue-100); color:var(--navy); flex:none;
  display:flex; align-items:center; justify-content:center;}
.fc .ic svg{width:26px; height:26px;}
.fc .t{font-size:1.08rem; font-weight:700; color:var(--navy); margin:0 0 4px;}
.fc .d{font-size:.92rem; color:var(--muted); line-height:1.45; margin:0;}
[class*="st-key-card_"] .stButton > button{background:var(--blue-100); border-color:var(--blue-100); color:var(--navy); padding:.4rem 1.2rem;}
[class*="st-key-card_"] .stButton > button:hover{background:var(--navy); border-color:var(--navy); color:#fff;}
[class*="st-key-card_"] .stButton > button:hover p{color:#fff;}

/* Module Assistant */
.st-key-curriculum_panel{background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:16px 16px 6px !important;
  box-shadow:0 1px 2px rgba(15,42,98,.05);}
.st-key-curriculum_panel > [data-testid="stElementContainer"], [class*="st-key-card_"] > [data-testid="stElementContainer"]{width:100% !important; max-width:100%;}
.cur-title{font-size:1rem; font-weight:700; color:var(--navy); margin:0 0 6px;}
.st-key-module_main > [data-testid="stElementContainer"]:first-child [data-testid="stHeading"] h3{
  background:var(--blue-100); border-radius:10px; padding:12px 18px !important; margin:0; font-size:1.2rem;}
.st-key-module_main > [data-testid="stElementContainer"]:first-child [data-testid="stHeaderActionElements"]{display:none;}
.st-key-module_main hr{display:none;}
[data-testid="stTabs"] [role="tablist"]{gap:4px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:4px;}
[data-testid="stTabs"] [role="tab"]{flex:1; height:auto; padding:9px 14px; border-radius:8px; color:var(--muted); font-weight:600;
  justify-content:center; background:transparent;}
[data-testid="stTabs"] [role="tab"] p{color:inherit !important; font-weight:600;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:var(--navy); color:#fff;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p{color:#fff !important;}
[data-testid="stTabs"] .react-aria-SelectionIndicator, [data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"]{display:none !important;}
[data-testid="stTabs"] [role="tabpanel"]{background:#fff; border:1px solid var(--line); border-radius:var(--radius);
  padding:20px 22px; margin-top:12px; box-shadow:0 1px 2px rgba(15,42,98,.05);}
.st-key-module_layout [data-testid="stHorizontalBlock"]{align-items:flex-start;}

/* Regulation Chatbot (scoped by marker, so the quiz/nav radios are untouched) */
[data-testid="stMainBlockContainer"]:has(.pg-chat) [data-testid="stHeading"]{display:none;}
.st-key-chat_mode [role="radiogroup"]{display:inline-flex !important; gap:4px; background:#E8EEF8; border:1px solid var(--line);
  border-radius:10px; padding:4px;}
.st-key-chat_mode [role="radiogroup"] > *{display:flex;}
.st-key-chat_mode [role="radiogroup"] label{margin:0 !important; padding:7px 24px !important; border-radius:8px; cursor:pointer; color:var(--muted);}
.st-key-chat_mode [role="radiogroup"] label div:has(+ [data-testid="stMarkdownContainer"]), .st-key-chat_mode label[data-baseweb="radio"] > div:first-child{display:none !important;}
.st-key-chat_mode [role="radiogroup"] label, .st-key-chat_mode [role="radiogroup"] label *{color:inherit !important;}
.st-key-chat_mode [role="radiogroup"] label p{font-weight:600; margin:0;}
.st-key-chat_mode [role="radiogroup"] label{color:var(--muted) !important;}
.st-key-chat_mode [role="radiogroup"] label:has(input:checked){background:var(--navy); color:#fff !important;}
[data-testid="stChatMessage"]{border-radius:12px; padding:12px 16px; margin-bottom:8px; background:#fff; border:1px solid var(--line); max-width:90%;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){background:var(--blue-100); border-color:var(--blue-200);
  margin-left:auto; flex-direction:row-reverse; max-width:80%;}
[data-testid="stChatMessageAvatarAssistant"]{background:var(--navy) !important; color:#fff !important;}
[data-testid="stChatMessageAvatarUser"]{background:var(--blue-200) !important; color:var(--navy) !important;}
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"]{background:var(--blue-50); border:1px solid var(--blue-100);
  border-radius:8px; padding:6px 10px; margin-top:6px; display:inline-block; opacity:1 !important;}
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p{margin:0; color:var(--navy) !important; font-size:.82rem;}
[data-testid="stChatInput"]{border-radius:10px; border:1px solid var(--blue-200); background:#fff;}
[data-testid="stChatInput"] textarea{color:var(--text);}
[data-testid="stBottom"]{bottom:var(--nav-h) !important; background:transparent !important;}
[data-testid="stBottom"] > div{background:var(--bg) !important;}
[data-testid="stBottomBlockContainer"]{max-width:1180px; padding:8px 24px 14px !important;}

/* Knowledge Network / Timetable: page file's own st.title is replaced by the shared page header */
[data-testid="stMainBlockContainer"]:has(.pg-network) [data-testid="stHeading"]:has(h1), [data-testid="stMainBlockContainer"]:has(.pg-timetable) [data-testid="stHeading"]:has(h1){display:none;}
[data-testid="stMainBlockContainer"]:has(.pg-network) iframe, [data-testid="stMainBlockContainer"]:has(.pg-network) [data-testid="stPlotlyChart"]{
  border:1px solid var(--line); border-radius:var(--radius); background:#fff;}

/* Tablet and below */
@media (max-width: 900px){
  [data-testid="stMainBlockContainer"]{padding-left:16px !important; padding-right:16px !important;}
  .st-key-module_layout [data-testid="stHorizontalBlock"]{flex-wrap:wrap;}
  .st-key-module_layout [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{min-width:100% !important;}
}
@media (min-width: 641px) and (max-width: 900px){
  .st-key-curriculum_panel{display:grid !important; grid-template-columns:1fr 1fr; column-gap:16px;}
  .st-key-curriculum_panel > [data-testid="stElementContainer"]:first-child{grid-column:1 / -1;}
}
/* Mobile */
@media (max-width: 640px){
  :root{--hdr-h:52px; --nav-h:78px;}
  .app-header{padding:0 14px;}
  .st-key-bottom_nav{padding:4px 4px calc(4px + env(safe-area-inset-bottom)) !important;}
  .st-key-bottom_nav [role="radiogroup"]{gap:2px;}
  .st-key-bottom_nav [role="radiogroup"] label{padding:6px 2px 5px !important; gap:2px;}
  .st-key-bottom_nav [role="radiogroup"] label::before{width:20px; height:20px;}
  .st-key-bottom_nav [role="radiogroup"] label p{font-size:.62rem;}
  [data-testid="stMainBlockContainer"]{padding-left:12px !important; padding-right:12px !important;}
  [data-testid="stBottomBlockContainer"]{padding-left:12px !important; padding-right:12px !important;}
  .hero{padding:16px 16px;} .hero h1{font-size:1.4rem;}
  .page-hd h1{font-size:1.3rem;} .page-hd .ic{width:40px; height:40px;}
  [class*="st-key-card_"]{min-height:0;}
  [data-testid="stTabs"] [role="tab"]{padding:8px 6px; font-size:.85rem;}
  [data-testid="stTabs"] [role="tabpanel"]{padding:14px;}
}
/* Very narrow phones: keep every nav label on whole words */
@media (max-width: 360px){
  :root{--nav-h:84px;}
  .st-key-bottom_nav [role="radiogroup"]{gap:0;}
  .st-key-bottom_nav [role="radiogroup"] label{padding:6px 0 5px !important;}
  .st-key-bottom_nav [role="radiogroup"] label p{font-size:.54rem; word-break:keep-all; overflow-wrap:normal; hyphens:none;}
}
"""


def apply_theme():
    """Inject the shared CSS. Call once per run, before anything is drawn."""
    rules = "".join(
        f'.st-key-bottom_nav [role="radiogroup"] > :nth-child({i}){{--ico:url("{_mask_uri(name)}");}}'
        for i, name in enumerate(PAGES, start=1)
    )
    st.markdown(f"<style>{_CSS.replace('/*NAV_ICONS*/', rules)}</style>", unsafe_allow_html=True)


def render_header():
    """Fixed navy header with the app branding."""
    st.markdown(
        f'<div class="app-header">{_svg("logo", 30, 1.6)}'
        '<div class="brand">AI &amp; DS<br>Knowledge Assistant</div></div>',
        unsafe_allow_html=True,
    )


def render_bottom_nav():
    """Fixed bottom navigation. Returns the selected page name.

    The radio keeps its state in st.session_state["nav_page"], so Home cards can
    switch page by setting that key (see go_to).
    """
    with st.container(key="bottom_nav"):
        return st.radio(
            "Navigation",
            PAGES,
            horizontal=True,
            label_visibility="collapsed",
            key="nav_page",
        )


def go_to(page):
    """on_click callback: switch the bottom navigation to `page`."""
    st.session_state["nav_page"] = page


def page_marker(name):
    """Hidden marker so the CSS above can scope rules to the current page."""
    st.markdown(f'<div class="pg-marker pg-{name}"></div>', unsafe_allow_html=True)


def page_header(icon, title, subtitle=None):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="page-hd"><div class="ic">{_svg(icon, 24)}</div>'
        f"<div><h1>{title}</h1>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def home_hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def feature_card(slug, icon, title, description, target):
    """A Home card: icon, title, description and an Open button that switches page."""
    with st.container(key=f"card_{slug}"):
        st.markdown(
            f'<div class="fc"><div class="ic">{_svg(icon, 26)}</div>'
            f'<div><div class="t">{title}</div><div class="d">{description}</div></div></div>',
            unsafe_allow_html=True,
        )
        st.button("Open  →", key=f"open_{slug}", on_click=go_to, args=(target,))