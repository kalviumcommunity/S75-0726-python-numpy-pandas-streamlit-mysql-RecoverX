import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer

setup_page("Retry Analytics", "🔁")
render_header()
date_range = render_sidebar()

st.subheader("Analyze retry performance")
st.divider()
st.write("This page will show retry analytics and performance.")

render_footer()
