
import streamlit as st

from src.rbac import get_user_permissions, role_label, verify_user


_PAGE_KEY_MAP = {
    "Dashboard": "dashboard",
    "CSV Import": "csv_import",
    "Payment Lifecycle": "payment_lifecycle",
    "Failure Analysis": "failure_analysis",
    "Retry Analytics": "retry_analytics",
    "Revenue Recovery": "revenue_recovery",
}


def setup_page(page_title="RecoverX", page_icon="💰"):
    st.set_page_config(
        page_title=f"RecoverX - {page_title}",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded"
    )
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


def _render_auth_section():
    """Render the login/logout box inside the sidebar, managing session_state["user"]."""
    with st.sidebar.container():
        st.markdown(
            """
            <div style="padding: 1rem 0; border-bottom: 1px solid #334155; margin-bottom: 1rem;">
                <h2 style="color: white; margin:0; font-size: 1.25rem;">💰 RecoverX</h2>
                <p style="color: #94a3b8; margin: 0.25rem 0 0 0; font-size: 0.875rem;">Payment Analytics</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        user = st.session_state.get("user")
        if user:
            role = user.get("role")
            st.markdown(f"**👤 {user.get('username')}**")
            st.caption(f"Role: {role_label(role)}")

            perm = get_user_permissions(role)
            allowed = [p for p, ok in perm.items() if ok]
            if allowed:
                allowed_pretty = ", ".join(
                    p.replace("_", " ").title() for p in allowed
                )
                with st.expander("View permissions", expanded=False):
                    st.caption(allowed_pretty)

            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.pop("user", None)
                st.rerun()
            st.divider()
            return

        st.markdown("**🔐 Login Required**")
        with st.form("recoverx_login_form", clear_on_submit=False):
            username = st.text_input("Username", key="rbac_username")
            password = st.text_input("Password", type="password", key="rbac_password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            user = verify_user(username, password)
            if user:
                st.session_state["user"] = user
                st.success(f"Welcome, {user.get('username')}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        with st.expander("Test credentials", expanded=False):
            st.caption(
                "Finance Manager: `finance_manager` / `Finance@123`\n\n"
                "Payments Analyst: `payments_analyst` / `Payments@123`\n\n"
                "Risk Ops: `risk_ops` / `Risk@123`"
            )
        st.divider()


def render_sidebar():
    _render_auth_section()

    with st.sidebar:
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
        unsafe_allow_html=True
    )


def render_footer():
    st.divider()
    st.caption("RecoverX - Recover Your Revenue")


def require_login():
    """Return True if user is present; else render an unauth landing and return False."""
    user = st.session_state.get("user")
    if user:
        return True

    st.warning("🔐 Please log in using the sidebar to access this page.")
    st.stop()
    return False


def require_page_permission(page_name: str) -> bool:
    """
    Ensure the current user both (a) is logged in and (b) has permission
    to access the given Streamlit page title. Stops rendering with a
    clear unauthorized message if not.
    """
    user = st.session_state.get("user")
    if not user:
        st.warning("🔐 Please log in using the sidebar to access this page.")
        st.stop()
        return False

    page_key = _PAGE_KEY_MAP.get(page_name)
    if page_key is None:
        return True

    perm = get_user_permissions(user.get("role"))
    if not perm.get(page_key, False):
        st.error(
            f"🚫 Access denied. Your role ({role_label(user.get('role'))}) "
            f"does not have permission to view **{page_name}**."
        )
        st.info("Use the sidebar to navigate to an allowed page, or log in with a different account.")
        st.stop()
        return False
    return True
