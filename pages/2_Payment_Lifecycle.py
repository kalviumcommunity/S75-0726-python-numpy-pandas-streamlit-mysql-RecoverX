import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer

setup_page("Payment Lifecycle", "🔄")
render_header()
date_range = render_sidebar()

st.subheader("Track complete journey of payments")
st.divider()
st.write("This page will display payment lifecycle details.")

render_footer()
