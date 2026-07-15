import streamlit as st

# Page configuration
st.set_page_config(
    page_title="RecoverX - Dashboard",
    page_icon="💰",
    layout="wide"
)

# Main header
st.title("💰 RecoverX")
st.subheader("Payment Analytics Platform - Dashboard")
st.divider()

st.write("Welcome to RecoverX! Use the navigation sidebar to explore different sections.")
st.divider()

st.header("Key Metrics (Placeholder)")
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
