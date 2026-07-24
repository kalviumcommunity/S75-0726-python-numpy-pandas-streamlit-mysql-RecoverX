
import streamlit as st

def setup_page(page_title="RecoverX", page_icon="💰"):
    st.set_page_config(
        page_title=f"RecoverX - {page_title}",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # Custom CSS for sidebar styling (to match Figma dark blue)
    st.markdown(
        """
        <style>
        /* Sidebar background */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            color: white !important;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        [data-testid="stSidebar"] .st-emotion-cache-1r6slb0 {
            color: white !important;
        }
        /* Sidebar header text */
        [data-testid="stSidebarNav"] span {
            color: white !important;
        }
        /* Sidebar active link */
        [data-testid="stSidebarNavLink"] {
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 1rem 0; border-bottom: 1px solid #334155; margin-bottom: 1rem;">
                <h2 style="color: white; margin:0; font-size: 1.25rem;">💰 RecoverX</h2>
                <p style="color: #94a3b8; margin: 0.25rem 0 0 0; font-size: 0.875rem;">Payment Analytics</p>
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

