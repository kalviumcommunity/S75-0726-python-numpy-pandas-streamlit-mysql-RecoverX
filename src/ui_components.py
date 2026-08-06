
import streamlit as st

 frontend_changes
THEMES = {
    "Dark": {
        "sidebar_bg": "#0f172a",
        "sidebar_fg": "#ffffff",
        "sidebar_subtle": "#94a3b8",
        "sidebar_border": "#334155",
        "accent": "#2563eb",
        "body_label": "Dark",
    },
    "Light": {
        "sidebar_bg": "#f8fafc",
        "sidebar_fg": "#0f172a",
        "sidebar_subtle": "#475569",
        "sidebar_border": "#e2e8f0",
        "accent": "#2563eb",
        "body_label": "Light",
    },
    "Blue": {
        "sidebar_bg": "linear-gradient(180deg, #1e3a8a 0%, #1d4ed8 60%, #2563eb 100%)",
        "sidebar_fg": "#ffffff",
        "sidebar_subtle": "#bfdbfe",
        "sidebar_border": "#3b82f6",
        "accent": "#93c5fd",
        "body_label": "Blue",
    },
}

DEFAULT_THEME = "Dark"


def _get_active_theme():
    if "theme" not in st.session_state:
        st.session_state["theme"] = DEFAULT_THEME
    theme_name = st.session_state.get("theme", DEFAULT_THEME)
    if theme_name not in THEMES:
        theme_name = DEFAULT_THEME
        st.session_state["theme"] = theme_name
    return theme_name, THEMES[theme_name]



def _apply_theme(theme: str):
    theme = (theme or "Dark").strip().lower()
    if theme == "light":
        bg = "#ffffff"
        text = "#0f172a"
        sidebar_bg = "#f1f5f9"
        sidebar_text = "#0f172a"
        sidebar_border = "#e2e8f0"
        caption = "#475569"
    else:
        bg = "#0b1220"
        text = "#e5e7eb"
        sidebar_bg = "#0f172a"
        sidebar_text = "#ffffff"
        sidebar_border = "#334155"
        caption = "#94a3b8"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        .stApp [data-testid="stMarkdownContainer"] {{
            color: {text} !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            color: {sidebar_text} !important;
        }}
        [data-testid="stSidebar"] * {{
            color: {sidebar_text} !important;
        }}
        [data-testid="stSidebarNav"] span {{
            color: {sidebar_text} !important;
        }}
        [data-testid="stSidebarNavLink"] {{
            color: {sidebar_text} !important;
        }}
        [data-testid="stSidebar"] hr, [data-testid="stSidebar"] .stDivider {{
            border-color: {sidebar_border} !important;
        }}
        [data-testid="stSidebar"] p {{
            color: {caption} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
main

def setup_page(page_title="RecoverX", page_icon="💰"):
    st.set_page_config(
        page_title=f"RecoverX - {page_title}",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
 frontend_changes
    theme_name, theme = _get_active_theme()
    if theme_name == "Dark":
        body_bg_css = ""
        body_fg_css = ""
    elif theme_name == "Light":
        body_bg_css = """
        [data-testid="stAppViewContainer"], .main, .block-container {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        [data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"] {
            color: #0f172a !important;
        }
        """
        body_fg_css = ""
    else:
        body_bg_css = """
        [data-testid="stAppViewContainer"], .main, .block-container {
            background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%) !important;
            color: #0f172a !important;
        }
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            color: #1e3a8a !important;
        }
        """
        body_fg_css = ""

    st.markdown(
        f"""
        <style>
        /* Sidebar background + foreground */
        [data-testid="stSidebar"] {{
            background: {theme['sidebar_bg']} !important;
            color: {theme['sidebar_fg']} !important;
            border-right: 1px solid {theme['sidebar_border']};
        }}
        [data-testid="stSidebar"] * {{
            color: {theme['sidebar_fg']} !important;
        }}
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
            color: {theme['sidebar_subtle']} !important;
        }}
        [data-testid="stSidebarNav"] span {{
            color: {theme['sidebar_fg']} !important;
        }}
        [data-testid="stSidebarNavLink"] {{
            color: {theme['sidebar_fg']} !important;
            border-radius: 0.5rem;
        }}
        [data-testid="stSidebarNavLink"]:hover {{
            background-color: rgba(255,255,255,0.08);
        }}
        [data-testid="stSidebarContent"] hr,
        [data-testid="stSidebar"] hr {{
            border-color: {theme['sidebar_border']} !important;
        }}
        /* Global accent on primary buttons */
        button[kind="primary"] {{
            background-color: {theme['accent']} !important;
            border-color: {theme['accent']} !important;
        }}
        {body_bg_css}
        {body_fg_css}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "ui_theme" not in st.session_state:
        st.session_state["ui_theme"] = "Dark"
    _apply_theme(st.session_state["ui_theme"])
 main


def render_sidebar():
    theme_name, theme = _get_active_theme()
    with st.sidebar:
        selected_theme = st.selectbox(
            "Theme",
            options=["Dark", "Light"],
            index=0 if st.session_state.get("ui_theme", "Dark") == "Dark" else 1,
        )
        st.session_state["ui_theme"] = selected_theme
        _apply_theme(selected_theme)
        st.markdown(
 frontend_changes
            f"""
            <div style="padding: 1rem 0; border-bottom: 1px solid {theme['sidebar_border']}; margin-bottom: 1rem;">
                <h2 style="color: {theme['sidebar_fg']}; margin:0; font-size: 1.25rem;">💰 RecoverX</h2>
                <p style="color: {theme['sidebar_subtle']}; margin: 0.25rem 0 0 0; font-size: 0.875rem;">Payment Analytics</p>

            """
            <div style="padding: 1rem 0; border-bottom: 1px solid rgba(148,163,184,0.35); margin-bottom: 1rem;">
                <h2 style="margin:0; font-size: 1.25rem;">💰 RecoverX</h2>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem;">Payment Analytics</p>
 main
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div style='margin-bottom: 0.5rem; color: {theme['sidebar_subtle']}; font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase;'>🎨 Theme</div>",
            unsafe_allow_html=True,
        )
        new_theme = st.radio(
            "Appearance",
            options=list(THEMES.keys()),
            index=list(THEMES.keys()).index(theme_name) if theme_name in THEMES else 0,
            horizontal=True,
            label_visibility="collapsed",
            key="theme_picker",
            help="Switch between Dark, Light, and Blue dashboard themes.",
        )
        if new_theme != theme_name:
            st.session_state["theme"] = new_theme
            st.rerun()

        st.divider()
        st.markdown(
            f"<div style='margin-bottom: 0.5rem; color: {theme['sidebar_subtle']}; font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase;'>📅 Filters</div>",
            unsafe_allow_html=True,
        )
        st.subheader("Filters")
        date_range = st.date_input("Select Date Range")
        return date_range


def render_header():
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <div>
                <h1 style="margin:0; font-size: 1.5rem; color: #2563eb;">RecoverX - Payment Analytics Dashboard</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.divider()
    st.caption("RecoverX - Recover Your Revenue")
