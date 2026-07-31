
import streamlit as st


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

def setup_page(page_title="RecoverX", page_icon="💰"):
    st.set_page_config(
        page_title=f"RecoverX - {page_title}",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    if "ui_theme" not in st.session_state:
        st.session_state["ui_theme"] = "Dark"
    _apply_theme(st.session_state["ui_theme"])

def render_sidebar():
    with st.sidebar:
        selected_theme = st.selectbox(
            "Theme",
            options=["Dark", "Light"],
            index=0 if st.session_state.get("ui_theme", "Dark") == "Dark" else 1,
        )
        st.session_state["ui_theme"] = selected_theme
        _apply_theme(selected_theme)
        st.markdown(
            """
            <div style="padding: 1rem 0; border-bottom: 1px solid rgba(148,163,184,0.35); margin-bottom: 1rem;">
                <h2 style="margin:0; font-size: 1.25rem;">💰 RecoverX</h2>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem;">Payment Analytics</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.subheader("Filters")
        date_range = st.date_input("Select Date Range")
        return date_range

def render_header():
    # Top header with title, date picker, user/notification icons (simple version for now)
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <div>
                <h1 style="margin:0; font-size: 1.5rem; color: #2563eb;">RecoverX - Payment Analytics Dashboard</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_footer():
    st.divider()
    st.caption("RecoverX - Recover Your Revenue")

