import streamlit as st

st.set_page_config(
    page_title="RecoverX - Alerts",
    page_icon="🔔",
    layout="wide"
)

# Sidebar
with st.sidebar:
    st.header("💰 RecoverX")
    st.caption("Recover Your Revenue")
    st.divider()
    st.subheader("Filters")
    date_range = st.date_input("Select Date Range")

# Main Content
st.title("🔔 Alerts")
st.subheader("Monitor alerts and notifications")
st.divider()
st.write("This page will show active alerts and notifications.")

# Footer
st.divider()
st.caption("RecoverX - Recover Your Revenue")
