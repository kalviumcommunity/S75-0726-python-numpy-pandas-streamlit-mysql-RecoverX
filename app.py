import streamlit as st

# Page configuration
st.set_page_config(
    page_title="RecoverX - Payment Analytics",
    page_icon="💰",
    layout="wide"
)

# Main header
st.title("💰 RecoverX")
st.subheader("Payment Analytics Platform")
st.divider()

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        ["Dashboard", "Payment Lifecycle", "Failure Analysis", "Retry Analytics", "Revenue Recovery", "Alerts"]
    )
    st.divider()
    st.header("Filters")
    date_range = st.date_input("Select Date Range")

# Main content area
st.header(f"{page}")
st.write("This page will contain the relevant analytics.")

# Footer
st.divider()
st.caption("RecoverX - Recover Your Revenue")
