import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer

setup_page("Failure Analysis", "❌")
render_header()
date_range = render_sidebar()

st.subheader("Analyze payment failure patterns")
st.divider()
st.write("This page will analyze payment failures and their causes.")

render_footer()
