import pandas as pd
import streamlit as st
from data_loader import load_investigations, load_tests

try:
    from scoring import score_investigations

    USING_STUB = False
except ImportError:
    from scoring_stub import score_investigations

    USING_STUB = True

st.set_page_config(page_title="Ranking | Flame in Freefall", layout="wide")
st.title("2. Ranking")

if USING_STUB:
    st.warning(
        "Using fallback `scoring_stub.py` (score = number of test conditions). "
        "Official `scoring.py` module from Person A is not found yet."
    )

inv_df = load_investigations()
tests_df = load_tests()

environments = ["ISS", "Moon base", "Pressurized rover", "Mars habitat"]
selected_env = st.radio(
    "Target Environment",
    options=environments,
    horizontal=True,
)

st.subheader("Scoring Weights")
col1, col2, col3 = st.columns(3)
with col1:
    w_atmosphere = st.slider(
        "Weight 1: Atmosphere Match (placeholder)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
    )
with col2:
    w_fuel = st.slider(
        "Weight 2: Fuel & Geometry Relevance (placeholder)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
    )
with col3:
    w_safety = st.slider(
        "Weight 3: Data Completeness & Safety Role (placeholder)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
    )

weights = {
    "weight_1": w_atmosphere,
    "weight_2": w_fuel,
    "weight_3": w_safety,
}

ranked_df = score_investigations(inv_df, tests_df, selected_env, weights)

display_df = ranked_df.copy()
for col in display_df.columns:
    display_df[col] = display_df[col].apply(
        lambda v: "no data" if pd.isna(v) or str(v).strip() == "" else v
    )

st.subheader(f"Ranked Investigations for {selected_env} ({len(display_df)})")
st.dataframe(display_df, use_container_width=True, hide_index=True)