
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import streamlit as st
from src.ui_components import setup_page, render_header, render_sidebar, render_footer, require_login

setup_page("RecoverX", "💠")
render_header()
date_range = render_sidebar()

require_login()

st.markdown("## Welcome to RecoverX")
st.markdown(
    "**Payment Recovery Analytics Platform** — track failed transactions, "
    "analyse retry performance, and prioritise revenue recovery."
)
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Navigation")
    st.markdown(
        "Use the **sidebar** on the left to open any page:\n\n"
        "- **Dashboard** — key metrics, transactions overview, and payment method totals\n"
        "- **CSV Import** — bulk-import transactions and retries from CSV\n"
        "- **Payment Lifecycle** — search, filter and export transaction timelines\n"
        "- **Failure Analysis** — temporary vs. permanent failures, response-code & gateway breakdowns\n"
        "- **Retry Analytics** — success rates per attempt, timing gaps and best retry windows\n"
        "- **Revenue Recovery** — recoverable vs. lost revenue, high-value failed transactions"
    )

with col2:
    st.subheader("🚀 Quick Tips")
    st.markdown(
        "- Start on the **Dashboard** for the big picture.\n"
        "- Use the **date-range picker in the sidebar** to filter every page.\n"
        "- Drill into failures on the **Failure Analysis** page.\n"
        "- Tune your retry cadence using **Retry Analytics**.\n"
        "- Prioritise which failed txns to re-attempt via the **Revenue Recovery** page."
    )

st.divider()
st.info("💡 Tip: Click on **Dashboard** in the sidebar to view the live analytics dashboard.")
render_footer()
