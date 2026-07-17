import streamlit as st

st.set_page_config(
    page_title="RecoverX - Failure Analysis",
    page_icon="❌",
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
st.title("❌ Failure Analysis")
st.subheader("Analyze payment failure patterns")
st.divider()
st.write("This page will analyze payment failures and their causes.")

# Footer
st.divider()
st.caption("RecoverX - Recover Your Revenue")
