import streamlit as st
from data_loader import load_investigations, load_tests

st.set_page_config(
    page_title="Flame in Freefall",
    layout="wide",
)

st.title("Flame in Freefall")

st.info(
    "Lunar bases will operate at 30%+ O2, but most NASA solid-material tests were at much lower O2"
)

st.subheader("Project Pages")
st.markdown(
    """
- **1. Catalog** — Browse and filter NASA microgravity combustion and fire safety investigations with detailed experiment cards and test conditions.
- **2. Ranking** — Score and rank investigations by relevance to lunar habitat atmosphere and fire safety requirements.
- **3. Coverage Map** — Visualize tested parameter ranges ($O_2$ vs. pressure) against the lunar habitat target zone ($O_2 \\ge 30\\%$, $P \\le 70.3\\text{ kPa}$).
- **4. Assistant** — Ask the AI assistant questions strictly grounded in the catalog data, citing investigation `id` and `name`.
"""
)

inv_df = load_investigations()
tests_df = load_tests()

st.divider()
col1, col2 = st.columns(2)
col1.metric("Loaded Investigations", len(inv_df))
col2.metric("Loaded Test Conditions", len(tests_df))

with st.sidebar:
    st.caption(f"Investigations loaded: {len(inv_df)}")
    st.caption(f"Test conditions loaded: {len(tests_df)}")
