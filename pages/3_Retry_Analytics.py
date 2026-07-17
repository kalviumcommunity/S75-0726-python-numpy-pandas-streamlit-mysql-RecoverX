import streamlit as st

st.set_page_config(
    page_title="RecoverX - Retry Analytics",
    page_icon="🔁",
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
st.title("🔁 Retry Analytics")
st.subheader("Analyze retry performance")
st.divider()
st.write("This page will show retry analytics and performance.")

# Footer
st.divider()
st.caption("RecoverX - Recover Your Revenue")
