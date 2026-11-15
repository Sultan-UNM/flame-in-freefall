import pandas as pd
import plotly.express as px
import streamlit as st
from constants import MOON_O2_MIN_PCT, MOON_P_MAX_KPA
from data_loader import load_investigations, load_tests

st.set_page_config(page_title="Coverage Map | Flame in Freefall", layout="wide")
st.title("3. Coverage Map")

inv_df = load_investigations()
tests_df = load_tests()

inv_meta = inv_df[["id", "name", "fuel_phase"]].drop_duplicates(subset=["id"])
merged_df = tests_df.merge(
    inv_meta,
    left_on="investigation_id",
    right_on="id",
    how="left",
    suffixes=("", "_inv"),
)

with st.sidebar:
    st.header("Filters")

    all_inv_ids = sorted(merged_df["investigation_id"].dropna().astype(str).unique().tolist())
    selected_inv_ids = st.multiselect(
        "Investigations",
        options=all_inv_ids,
        default=all_inv_ids,
    )

    verified_options = (
        merged_df["verified"]
        .fillna("no data")
        .astype(str)
        .unique()
        .tolist()
    )
    verified_options = sorted(verified_options)
    selected_verified = st.multiselect(
        "Verified status",
        options=verified_options,
        default=verified_options,
    )

    solid_only = st.toggle("Solid fuel only", value=False)

filtered_df = merged_df[
    merged_df["investigation_id"].astype(str).isin(selected_inv_ids)
    & merged_df["verified"].fillna("no data").astype(str).isin(selected_verified)
].copy()

if solid_only:
    is_solid = (
        filtered_df["fuel_phase"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.contains("solid", na=False)
    )
    filtered_df = filtered_df[is_solid].copy()

missing_coords_mask = filtered_df["o2_pct"].isna() | filtered_df["pressure_kpa"].isna()
missing_coords_count = int(missing_coords_mask.sum())
plot_df = filtered_df[~missing_coords_mask].copy()

hover_cols = ["test_id", "fuel", "flow_cm_s", "outcome", "source_doc", "source_page"]
for col in hover_cols:
    if col in plot_df.columns:
        plot_df[f"{col}_display"] = plot_df[col].apply(
            lambda v: "no data" if pd.isna(v) or str(v).strip() == "" else str(v)
        )
    else:
        plot_df[f"{col}_display"] = "no data"

max_o2 = max(
    float(plot_df["o2_pct"].max()) if not plot_df.empty else 100.0,
    float(MOON_O2_MIN_PCT) + 20.0,
    100.0,
)
max_p = max(
    float(plot_df["pressure_kpa"].max()) if not plot_df.empty else 110.0,
    float(MOON_P_MAX_KPA) + 30.0,
)

fig = px.scatter(
    plot_df,
    x="o2_pct",
    y="pressure_kpa",
    color="investigation_id",
    custom_data=[
        "test_id_display",
        "fuel_display",
        "flow_cm_s_display",
        "outcome_display",
        "source_doc_display",
        "source_page_display",
    ],
    labels={
        "o2_pct": "O2 Concentration (%)",
        "pressure_kpa": "Pressure (kPa)",
        "investigation_id": "Investigation ID",
    },
    title="Test Conditions vs. Moon Base Target Zone",
)

fig.update_traces(
    marker=dict(size=7, opacity=0.65),
    hovertemplate=(
        "<b>Investigation:</b> %{fullData.name}<br>"
        "<b>Test ID:</b> %{customdata[0]}<br>"
        "<b>O2 (%):</b> %{x}<br>"
        "<b>Pressure (kPa):</b> %{y}<br>"
        "<b>Fuel:</b> %{customdata[1]}<br>"
        "<b>Flow (cm/s):</b> %{customdata[2]}<br>"
        "<b>Outcome:</b> %{customdata[3]}<br>"
        "<b>Source Doc:</b> %{customdata[4]}<br>"
        "<b>Source Page:</b> %{customdata[5]}<extra></extra>"
    ),
)

fig.add_shape(
    type="rect",
    x0=MOON_O2_MIN_PCT,
    x1=max_o2,
    y0=0,
    y1=MOON_P_MAX_KPA,
    fillcolor="rgba(255, 165, 0, 0.18)",
    line=dict(color="rgba(255, 140, 0, 0.8)", width=2, dash="dash"),
    layer="below",
)

fig.add_annotation(
    x=MOON_O2_MIN_PCT + (max_o2 - MOON_O2_MIN_PCT) * 0.5,
    y=MOON_P_MAX_KPA * 0.9,
    text="Moon base target zone",
    showarrow=False,
    font=dict(size=13, color="darkorange"),
    bgcolor="rgba(0, 0, 0, 0.5)",
)

fig.update_layout(
    xaxis=dict(range=[0, max_o2 * 1.03]),
    yaxis=dict(range=[0, max_p * 1.05]),
    height=620,
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    f"Rows excluded from chart due to missing O2 or pressure values: {missing_coords_count}"
)

in_moon_zone = plot_df[
    (plot_df["o2_pct"] >= MOON_O2_MIN_PCT)
    & (plot_df["pressure_kpa"] <= MOON_P_MAX_KPA)
]
moon_zone_solid = in_moon_zone[
    in_moon_zone["fuel_phase"]
    .fillna("")
    .astype(str)
    .str.lower()
    .str.contains("solid", na=False)
]

total_plotted = len(plot_df)
moon_count = len(in_moon_zone)
moon_solid_count = len(moon_zone_solid)

col1, col2, col3 = st.columns(3)
col1.metric("Total Tests on Chart", total_plotted)
col2.metric("Tests in Moon Base Zone", moon_count if moon_count > 0 else "no data")
col3.metric(
    "Solid-Fuel Tests in Moon Base Zone",
    moon_solid_count if moon_count > 0 else "no data",
)

if moon_count == 0:
    st.info("No data in the Moon base target zone for the selected filters (нет данных).")
