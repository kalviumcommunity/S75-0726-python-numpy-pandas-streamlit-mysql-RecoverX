import streamlit as st

st.set_page_config(
    page_title="RecoverX - Dashboard",
    page_icon="💰",
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
st.title("💰 RecoverX - Dashboard")
st.subheader("Welcome to your Payment Analytics Platform")
st.divider()

st.write("Use the navigation sidebar to explore different sections of the platform.")

st.divider()
st.header("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Transactions", "12,345", "+12%")
with col2:
    st.metric("Success Rate", "85%", "+2%")
with col3:
    st.metric("Revenue Recovered", "$45,678", "+15%")
with col4:
    st.metric("Retry Attempts", "3,456", "-5%")

# Footer
st.divider()
st.caption("RecoverX - Recover Your Revenue")
