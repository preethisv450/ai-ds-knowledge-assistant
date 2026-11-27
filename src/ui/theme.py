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
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "doc": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h6"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
    "clip": '<path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>',
}

# Decorative illustration for the Home banner (books + laptop).
_HERO_ART = (
    '<svg viewBox="0 0 230 110" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<ellipse cx="140" cy="52" rx="86" ry="46" fill="#E2EBF9"/>'
    '<rect x="64" y="14" width="116" height="70" rx="6" fill="#fff" stroke="#0F2A62" stroke-width="2.5"/>'
    '<polyline points="110,37 96,49 110,61" fill="none" stroke="#2E5BBA" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
    '<polyline points="134,37 148,49 134,61" fill="none" stroke="#2E5BBA" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
    '<line x1="127" y1="33" x2="117" y2="65" stroke="#2E5BBA" stroke-width="4" stroke-linecap="round"/>'
    '<rect x="50" y="84" width="144" height="8" rx="4" fill="#0F2A62"/>'
    '<rect x="8" y="70" width="92" height="14" rx="3" fill="#C9D8F2" stroke="#0F2A62" stroke-width="2"/>'
    '<rect x="14" y="56" width="80" height="14" rx="3" fill="#9DB9EC" stroke="#0F2A62" stroke-width="2"/>'
    '<rect x="20" y="42" width="68" height="14" rx="3" fill="#2E5BBA" stroke="#0F2A62" stroke-width="2"/>'
    "</svg>"
)


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
.app-header > svg{width:32px; height:32px; flex:none; color:#fff;}
.app-header .brand{font-size:.92rem; font-weight:700; line-height:1.15; letter-spacing:.01em; color:#fff;}
.app-header .avatar{margin-left:auto; width:38px; height:38px; border-radius:50%; background:#fff; color:var(--navy);
  display:flex; align-items:center; justify-content:center; flex:none;}
.app-header .avatar svg{width:22px; height:22px;}

/* Bottom navigation (relies on role/data-testid hooks, not Streamlit's generated class names) */
.st-key-bottom_nav{position:fixed !important; left:0; right:0; bottom:0; width:100% !important; max-width:100% !important; box-sizing:border-box; z-index:1000; background:#fff;
  border-top:1px solid var(--line); box-shadow:0 -2px 14px rgba(15,42,98,.08);
  padding:6px 12px calc(6px + env(safe-area-inset-bottom)) !important; gap:0 !important;}
.st-key-bottom_nav [data-testid="stWidgetLabel"]{display:none !important;}
.st-key-bottom_nav [data-testid="stElementContainer"], .st-key-bottom_nav [data-testid="stRadio"]{width:100% !important;}
.st-key-bottom_nav [role="radiogroup"]{display:grid !important; grid-template-columns:repeat(5,minmax(0,1fr)); gap:4px;
  max-width:none; margin:0 auto; width:100%;}
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
/*ICON_RULES*/

/* Page header */
.page-hd{display:flex; align-items:center; gap:14px; margin:2px 0 18px;}
.page-hd .ic{color:var(--navy); display:flex; align-items:center; justify-content:center; flex:none;}
.page-hd .ic svg{width:40px; height:40px;}
.page-hd h1{margin:0; padding:0 !important; font-size:1.6rem; font-weight:700; color:var(--navy); line-height:1.2;}
.page-hd p{margin:2px 0 0; color:var(--text); font-size:.95rem;}

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
.hero{background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:18px 26px; margin-bottom:18px;
  box-shadow:0 1px 2px rgba(15,42,98,.05); display:flex; align-items:center; gap:20px; overflow:hidden;}
.hero .hero-ic{color:var(--navy); flex:none; display:flex;}
.hero .hero-ic svg{width:48px; height:48px;}
.hero h1{margin:0; padding:0 !important; font-size:1.9rem; color:var(--navy); line-height:1.2;}
.hero p{margin:6px 0 0; color:var(--text); font-size:1rem;}
.hero .hero-art{margin-left:auto; width:230px; flex:none;}
.hero .hero-art svg{width:100%; height:auto; display:block;}
[class*="st-key-card_"]{background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:20px 22px 18px !important;
  box-shadow:0 1px 2px rgba(15,42,98,.05); min-height:176px; transition:box-shadow .18s, border-color .18s, transform .18s;}
[class*="st-key-card_"]:hover{box-shadow:0 6px 18px rgba(15,42,98,.12); border-color:var(--blue-200); transform:translateY(-1px);}
.fc{display:flex; gap:16px; align-items:flex-start; margin-bottom:14px;}
.fc .ic{width:52px; height:52px; border-radius:50%; background:var(--blue-100); color:var(--navy); flex:none;
  display:flex; align-items:center; justify-content:center;}
.fc .ic svg{width:26px; height:26px;}
.fc .t{font-size:1.08rem; font-weight:700; color:var(--navy); margin:0 0 4px;}
.fc .d{font-size:.92rem; color:var(--text); line-height:1.45; margin:0;}
[class*="st-key-card_"] [data-testid="stElementContainer"]:has(.stButton), [class*="st-key-card_"] [data-testid="stElementContainer"]:has([data-testid="stButton"]){padding-left:68px;}
[class*="st-key-card_"] .stButton, [class*="st-key-card_"] [data-testid="stButton"]{width:auto !important;}
[class*="st-key-card_"] .stButton > button{width:auto !important;}
[class*="st-key-card_"] .stButton > button{background:var(--blue-100); border-color:var(--blue-100); color:var(--navy); padding:.4rem 1.2rem;}
[class*="st-key-card_"] .stButton > button:hover{background:var(--navy); border-color:var(--navy); color:#fff;}
[class*="st-key-card_"] .stButton > button:hover p{color:#fff;}

/* Module Assistant */
.st-key-curriculum_panel{background:#fff; border:1px solid var(--line); border-radius:var(--radius); padding:16px 16px 6px !important;
  box-shadow:0 1px 2px rgba(15,42,98,.05);}
.st-key-curriculum_panel > [data-testid="stElementContainer"], [class*="st-key-card_"] > [data-testid="stElementContainer"]{width:100% !important; max-width:100%;}
.cur-title{font-size:1rem; font-weight:700; color:var(--navy); margin:0 0 6px;}
.st-key-module_main > [data-testid="stElementContainer"]:first-child [data-testid="stHeading"] h3{
  background:var(--blue-100); border-radius:10px; padding:12px 18px !important; margin:0; font-size:1.2rem;
  display:flex !important; align-items:center; gap:14px;}
.st-key-module_main > [data-testid="stElementContainer"]:first-child [data-testid="stHeading"] h3::before{content:""; width:26px; height:26px; flex:none;
  background-color:var(--navy); -webkit-mask:var(--ico-book) center/contain no-repeat; mask:var(--ico-book) center/contain no-repeat;}
.st-key-module_main > [data-testid="stElementContainer"]:first-child [data-testid="stHeaderActionElements"]{display:none;}
.st-key-module_main hr{display:none;}
[data-testid="stTabs"] [role="tablist"]{gap:4px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:4px;}
[data-testid="stTabs"] [role="tab"]{flex:1; height:auto; padding:9px 14px; border-radius:8px; color:var(--muted); font-weight:600;
  display:flex; align-items:center; justify-content:center; gap:8px; background:transparent;}
[data-testid="stTabs"] [role="tab"]::before{content:""; width:18px; height:18px; flex:none; background-color:currentColor;
  -webkit-mask:var(--ico) center/contain no-repeat; mask:var(--ico) center/contain no-repeat;}
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
.st-key-chat_mode [role="radiogroup"]{display:flex !important; gap:4px; background:#E8EEF8; border:1px solid var(--line);
  border-radius:10px; padding:4px; width:100%; max-width:460px;}
.st-key-chat_mode [role="radiogroup"] > *{display:flex; flex:1;}
.st-key-chat_mode [role="radiogroup"] label{flex:1; margin:0 !important; padding:8px 16px !important; border-radius:8px; cursor:pointer; color:var(--muted);
  display:flex !important; align-items:center; justify-content:center; gap:8px;}
.st-key-chat_mode [role="radiogroup"] label::before{content:""; width:18px; height:18px; flex:none; background-color:currentColor;
  -webkit-mask:var(--ico) center/contain no-repeat; mask:var(--ico) center/contain no-repeat;}
.st-key-chat_mode [role="radiogroup"] label div:has(+ [data-testid="stMarkdownContainer"]), .st-key-chat_mode label[data-baseweb="radio"] > div:first-child{display:none !important;}
.st-key-chat_mode [role="radiogroup"] label, .st-key-chat_mode [role="radiogroup"] label *{color:inherit !important;}
.st-key-chat_mode [role="radiogroup"] label p{font-weight:600; margin:0; white-space:nowrap;}
.st-key-chat_mode [role="radiogroup"] label{min-width:max-content;}
.st-key-chat_mode [role="radiogroup"] label{color:var(--muted) !important;}
.st-key-chat_mode [role="radiogroup"] label:has(input:checked){background:var(--navy); color:#fff !important;}
[data-testid="stChatMessage"]{background:transparent !important; border:none !important; padding:6px 0 !important; gap:12px;
  align-items:flex-start; justify-content:flex-start !important; max-width:100%;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){flex-direction:row-reverse;}
[data-testid="stChatMessageContent"]{background:#F6F8FD; border:1px solid var(--line); border-radius:12px; padding:12px 16px;
  max-width:72%; width:fit-content; margin:0 !important; flex:0 1 auto;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"]{background:var(--blue-100);
  border-color:var(--blue-200);}
[data-testid="stChatMessageAvatarAssistant"], [data-testid="stChatMessageAvatarUser"]{border-radius:50% !important; width:40px; height:40px;
  background:var(--blue-100) !important; color:var(--navy) !important;}
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"]{background:var(--blue-50); border:1px solid var(--blue-100);
  border-radius:8px; padding:6px 10px; margin-top:6px; display:block; opacity:1 !important;}
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p{margin:0; color:var(--navy) !important; font-size:.82rem;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) [data-testid="stCaptionContainer"] p::before{content:""; display:inline-block;
  width:14px; height:14px; margin-right:8px; vertical-align:-2px; background-color:var(--navy);
  -webkit-mask:var(--ico-clip) center/contain no-repeat; mask:var(--ico-clip) center/contain no-repeat;}
[data-testid="stChatInput"], [data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea{background:#fff !important;}
[data-testid="stChatInput"]{border-radius:10px; border:1px solid var(--blue-200);}
[data-testid="stChatInput"] textarea{color:var(--text);}
[data-testid="stChatInputSubmitButton"]{background:var(--navy) !important; color:#fff !important; border-radius:8px !important;
  min-width:44px; height:38px; opacity:1;}
[data-testid="stChatInputSubmitButton"]:disabled{opacity:.6;}
[data-testid="stChatInputSubmitButton"] svg{display:none !important;}
[data-testid="stChatInputSubmitButton"]::after{content:""; display:block; width:20px; height:20px; margin:auto; background-color:#fff;
  -webkit-mask:var(--ico-send) center/contain no-repeat; mask:var(--ico-send) center/contain no-repeat;}
[data-testid="stBottom"]{bottom:var(--nav-h) !important; background:transparent !important;}
[data-testid="stBottom"] > div{background:var(--bg) !important;}
[data-testid="stBottomBlockContainer"]{max-width:1180px; padding:8px 24px 14px !important;}

/* Knowledge Network / Timetable: page file's own st.title is replaced by the shared page header */
[data-testid="stMainBlockContainer"]:has(.pg-network) [data-testid="stHeading"]:has(h1), [data-testid="stMainBlockContainer"]:has(.pg-timetable) [data-testid="stHeading"]:has(h1){display:none;}
[data-testid="stMainBlockContainer"]:has(.pg-network) iframe, [data-testid="stMainBlockContainer"]:has(.pg-network) [data-testid="stPlotlyChart"]{
  border:1px solid var(--line); border-radius:var(--radius); background:#fff;}
.st-key-graph_panel, .st-key-legend_panel, .st-key-details_panel{background:#fff; border:1px solid var(--line); border-radius:var(--radius);
  padding:16px 18px !important; box-shadow:0 1px 2px rgba(15,42,98,.05);}
.st-key-graph_panel{min-height:360px;}
.st-key-legend_panel > [data-testid="stElementContainer"], .st-key-details_panel > [data-testid="stElementContainer"]{width:100% !important;}
.side-title{font-size:1rem; font-weight:700; color:var(--navy); margin:0 0 8px;}
.lg-row{display:flex; align-items:center; gap:10px; font-size:.88rem; color:var(--text); margin:8px 0;}
.lg-key{width:34px; flex:none; display:flex; align-items:center; justify-content:center;}
.lg-dot{border-radius:50%; flex:none;}
.lg-sm{width:10px; height:10px; background:#8B5CD6;}
.lg-lg{width:18px; height:18px; background:#8B5CD6;}
.lg-swatch{display:flex; gap:3px;}
.lg-swatch i{width:9px; height:9px; border-radius:50%; display:block;}
.lg-line{width:30px; height:0; border-top:3px solid #9DB9EC;}
.lg-dash{width:30px; height:0; border-top:3px dashed #9DB9EC;}
.lg-sep{height:1px; background:var(--line); margin:12px 0 10px;}
.dt-head{display:flex; justify-content:space-between; background:var(--blue-100); color:var(--navy); font-weight:700; font-size:.88rem;
  padding:7px 10px; border-radius:6px;}
.dt-empty{color:var(--muted); font-size:.88rem; padding:10px 4px 2px;}

/* About / Help (Home) */
.st-key-help_panel{background:#fff; border:1px solid var(--line); border-radius:var(--radius);
  padding:4px 18px !important; margin-top:18px; box-shadow:0 1px 2px rgba(15,42,98,.05);}
.st-key-help_panel [data-testid="stExpander"] details{border:none; background:transparent;}
.st-key-help_panel [data-testid="stExpander"] summary{font-size:1.02rem; padding:10px 0;}
.hp h4{margin:14px 0 6px; font-size:.98rem; color:var(--navy);}
.hp p{margin:0 0 8px; font-size:.92rem; color:var(--text); line-height:1.5;}
.hp ul{margin:0 0 10px; padding-left:18px;}
.hp li{font-size:.92rem; color:var(--text); line-height:1.6;}
.hp .note{background:var(--blue-50); border:1px solid var(--blue-100); border-radius:8px;
  padding:10px 12px; font-size:.88rem; color:var(--text); margin-top:6px;}
.dt-row{display:flex; justify-content:space-between; align-items:center; gap:10px; font-size:.88rem;
  color:var(--text); padding:7px 10px; border-bottom:1px solid var(--line);}
.dt-row:last-of-type{border-bottom:none;}
.dt-n{font-weight:700; color:var(--navy); font-variant-numeric:tabular-nums;}
.side-title.sm{font-size:.92rem; margin-bottom:2px;}
.br-note{font-size:.78rem; color:var(--muted); margin:0 0 10px;}
.br-row{margin:0 0 10px;}
.br-top{font-size:.86rem; color:var(--text); margin-bottom:4px;}
.br-bar{height:7px; border-radius:4px; background:var(--blue-50); overflow:hidden;}
.br-bar i{display:block; height:100%; border-radius:4px; background:var(--navy);}
.br-where{font-size:.74rem; color:var(--muted); margin-top:3px;}

/* Tablet and below */
@media (max-width: 900px){
  [data-testid="stMainBlockContainer"]{padding-left:16px !important; padding-right:16px !important;}
  .st-key-module_layout [data-testid="stHorizontalBlock"], .st-key-network_layout [data-testid="stHorizontalBlock"]{flex-wrap:wrap;}
  .st-key-module_layout [data-testid="stHorizontalBlock"] > [data-testid="stColumn"],
  .st-key-network_layout [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{min-width:100% !important;}
  .hero .hero-art{width:170px;}
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
  .hero{padding:14px 16px; gap:12px;} .hero h1{font-size:1.35rem;} .hero .hero-art{display:none;} .hero .hero-ic svg{width:36px; height:36px;}
  .page-hd h1{font-size:1.3rem;} .page-hd .ic svg{width:34px; height:34px;}
  [class*="st-key-card_"]{min-height:0;}
  [data-testid="stTabs"] [role="tab"]{padding:8px 6px; font-size:.85rem; gap:5px;}
  [data-testid="stTabs"] [role="tab"]::before{width:15px; height:15px;}
  [data-testid="stTabs"] [role="tabpanel"]{padding:14px;}
  [data-testid="stChatMessageContent"]{max-width:84%;}
}
/* Very narrow phones: keep every nav label on whole words */
@media (max-width: 360px){
  :root{--nav-h:84px;}
  .st-key-bottom_nav [role="radiogroup"]{gap:0;}
  .st-key-bottom_nav [role="radiogroup"] label{padding:6px 0 5px !important;}
  .st-key-bottom_nav [role="radiogroup"] label p{font-size:.54rem; word-break:keep-all; overflow-wrap:normal; hyphens:none;}
}
"""


def _icon_rules():
    rules = [
        f':root{{--ico-book:url("{_mask_uri("Module Assistant")}"); --ico-send:url("{_mask_uri("send")}"); '
        f'--ico-clip:url("{_mask_uri("clip")}");}}'
    ]
    # bottom navigation, one icon per page
    for i, name in enumerate(PAGES, start=1):
        rules.append(f'.st-key-bottom_nav [role="radiogroup"] > :nth-child({i}){{--ico:url("{_mask_uri(name)}");}}')
    # Module Assistant tabs: Summary, Q&A, Questions, Quiz
    for i, name in enumerate(["doc", "Regulation Chatbot", "list", "trophy"], start=1):
        rules.append(f'[data-testid="stTabs"] [role="tablist"] > [role="tab"]:nth-child({i}){{--ico:url("{_mask_uri(name)}");}}')
    # chatbot mode switch: Syllabus, Regulation
    for i, name in enumerate(["Module Assistant", "doc"], start=1):
        rules.append(f'.st-key-chat_mode [role="radiogroup"] > :nth-child({i}){{--ico:url("{_mask_uri(name)}");}}')
    return "".join(rules)


def apply_theme():
    """Inject the shared CSS. Call once per run, before anything is drawn."""
    st.markdown(f"<style>{_CSS.replace('/*ICON_RULES*/', _icon_rules())}</style>", unsafe_allow_html=True)


def render_header():
    """Fixed navy header with the app branding and a profile icon."""
    st.markdown(
        f'<div class="app-header">{_svg("logo", 32, 1.6)}'
        '<div class="brand">AI &amp; DS<br>Knowledge Assistant</div>'
        f'<div class="avatar">{_svg("user", 22, 2)}</div></div>',
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
        f'<div class="page-hd"><div class="ic">{_svg(icon, 40, 1.6)}</div>'
        f"<div><h1>{title}</h1>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def home_hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><div class="hero-ic">{_svg("logo", 48, 1.6)}</div>'
        f"<div><h1>{title}</h1><p>{subtitle}</p></div>"
        f'<div class="hero-art">{_HERO_ART}</div></div>',
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


def network_side_panels():
    """Right-hand legend and concept-details panels for the Knowledge Network page.

    Layout only: no graph data is invented here. The details panel stays empty
    until the graph page provides concept data.
    """
    with st.container(key="legend_panel"):
        rows = ['<div class="side-title">Legend</div>']
        for name, colour in st.session_state.get("network_legend", []):
            rows.append(
                f'<div class="lg-row"><span class="lg-key">'
                f'<span class="lg-dot lg-lg" style="background:{colour}"></span></span>{name}</div>'
            )
        rows.append('<div class="lg-sep"></div>')
        rows.append('<div class="lg-row"><span class="lg-key"><span class="lg-line"></span></span>Learn this first</div>')
        rows.append('<div class="lg-row"><span class="lg-key"><span class="lg-dash"></span></span>Taught alongside</div>')
        st.markdown("".join(rows), unsafe_allow_html=True)
    with st.container(key="details_panel"):
        table = st.session_state.get("network_table", [])
        bridges = st.session_state.get("network_bridges", [])
        rows = ['<div class="side-title">Concept Details</div>',
                '<div class="dt-head"><span>Concept</span><span>Connections</span></div>']
        if table:
            for name, links in table:
                rows.append(f'<div class="dt-row"><span>{name}</span><span class="dt-n">{links}</span></div>')
        else:
            rows.append('<div class="dt-empty">Concept details will appear here once the graph is available.</div>')
        if bridges:
            rows.append('<div class="lg-sep"></div>')
            rows.append('<div class="side-title sm">Top bridge concepts</div>')
            rows.append('<div class="br-note">Concepts the most other topics depend on</div>')
            for name, where, pct in bridges:
                rows.append(
                    f'<div class="br-row"><div class="br-top"><span>{name}</span></div>'
                    f'<div class="br-bar"><i style="width:{max(pct, 6)}%"></i></div>'
                    f'<div class="br-where">{where}</div></div>'
                )
        st.markdown("".join(rows), unsafe_allow_html=True)

def help_section():
    """D16: a short About and Help panel, shown at the foot of Home."""
    with st.container(key="help_panel"):
        with st.expander("About and help"):
            st.markdown(
                '<div class="hp">'
                "<p>The AI &amp; DS Knowledge Assistant answers questions from your own "
                "course documents: the syllabus for each subject and the academic "
                "regulations. Every answer shows the document and page it came from, so "
                "you can check it.</p>"
                "<h4>Getting started</h4>"
                "<ul>"
                "<li>Open <b>Module Assistant</b> and pick your year, semester, subject and "
                "module. Everything else follows that choice.</li>"
                "<li><b>Summary</b> writes a structured summary of the module, "
                "<b>Questions</b> makes practice questions with model answers, and "
                "<b>Quiz</b> scores you on multiple choice questions.</li>"
                "<li><b>Regulation Chatbot</b> has two modes: Syllabus answers from the "
                "module you picked, Regulation answers from the rules and policy "
                "documents.</li>"
                "<li><b>Knowledge Network</b> shows how concepts build on each other. "
                "Arrows point from what to learn first to what it leads to.</li>"
                "<li><b>Timetable</b> shows your weekly class schedule.</li>"
                "</ul>"
                "<h4>If something does not work</h4>"
                "<ul>"
                "<li>An answer that says the service is unavailable usually means the "
                "daily quota is used up. Try again later.</li>"
                "<li>If Syllabus mode says to pick a module, open Module Assistant and "
                "choose one first.</li>"
                "<li>A module with no summary or questions yet means its document has not "
                "been added to the library.</li>"
                "</ul>"
                '<div class="note">Answers are generated by an AI model from your course '
                "documents. It can still get things wrong, so check the sources shown "
                "under each answer before relying on it for an exam.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
