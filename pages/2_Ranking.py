import pandas as pd
import streamlit as st
from data_loader import load_investigations, load_tests

try:
    from scoring import DEFAULT_WEIGHTS, environment_basis, score_investigations

    USING_STUB = False
except ImportError:
    from scoring_stub import DEFAULT_WEIGHTS, environment_basis, score_investigations

    USING_STUB = True

st.set_page_config(page_title="Ranking | Flame in Freefall", layout="wide")
st.title("2. Ranking")

if USING_STUB:
    st.warning(
        "Using fallback `scoring_stub.py`. "
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

WEIGHT_LABELS = {
    "zone_match": "Zone Match",
    "fuel_relevance": "Fuel Relevance",
    "role_relevance": "Role Relevance",
    "verified_share": "Verified Share",
}

weight_keys = ["zone_match", "fuel_relevance", "role_relevance", "verified_share"]

st.subheader("Scoring Weights")
cols = st.columns(len(weight_keys))
weights: dict[str, float] = {}

for col, key in zip(cols, weight_keys):
    default_val = float(DEFAULT_WEIGHTS[key])
    max_val = max(1.0, default_val * 2.0)
    step_val = 0.05 if max_val <= 1.0 else 0.5
    with col:
        weights[key] = st.slider(
            WEIGHT_LABELS.get(key, key),
            min_value=0.0,
            max_value=float(max_val),
            value=default_val,
            step=float(step_val),
            key=f"slider_{key}",
        )

ranked_df = score_investigations(inv_df, tests_df, selected_env, weights=weights)

display_df = ranked_df.copy()
for col in display_df.columns:
    display_df[col] = display_df[col].apply(
        lambda v: "no data" if pd.isna(v) or str(v).strip() == "" else v
    )

st.subheader(f"Ranked Investigations for {selected_env} ({len(display_df)})")
st.info(str(environment_basis(selected_env)))

col_cfg = {}
if "why" in display_df.columns:
    col_cfg["why"] = st.column_config.TextColumn("Why", width="large")
if "reason" in display_df.columns:
    col_cfg["reason"] = st.column_config.TextColumn("Reason", width="large")

st.dataframe(
    display_df,
    column_config=col_cfg,
    use_container_width=True,
    hide_index=True,
)

st.caption("BASS-II pressure is assumed (1 atm)")

explanation_col = "why" if "why" in display_df.columns else ("reason" if "reason" in display_df.columns else None)
if explanation_col and not display_df.empty:
    with st.expander("Detailed Scoring Explanations"):
        for _, row in display_df.iterrows():
            inv_id = row.get("id", "no data")
            inv_name = row.get("name", "no data")
            inv_score = row.get("score", "no data")
            inv_why = row.get(explanation_col, "no data")
            st.markdown(f"**{inv_id} — {inv_name}** (Score: `{inv_score}`): {inv_why}")
