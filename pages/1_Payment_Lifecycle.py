import streamlit as st

st.set_page_config(
    page_title="RecoverX - Payment Lifecycle",
    page_icon="🔄",
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
st.title("🔄 Payment Lifecycle")
st.subheader("Track complete journey of payments")
st.divider()
st.write("This page will display payment lifecycle details.")

# Footer
st.divider()
st.caption("RecoverX - Recover Your Revenue")
