import pandas as pd
import streamlit as st
from constants import MOON_O2_MIN_PCT, MOON_P_MAX_KPA
from data_loader import load_investigations, load_tests

st.set_page_config(page_title="Catalog | Flame in Freefall", layout="wide")
st.title("1. Catalog")

inv_df = load_investigations()
tests_df = load_tests()


def fmt_val(val) -> str:
    if pd.isna(val):
        return "no data"
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return "no data"
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return s


def fmt_range(min_val, max_val, unit: str) -> str:
    min_na = pd.isna(min_val)
    max_na = pd.isna(max_val)
    if min_na and max_na:
        return "no data"
    if not min_na and not max_na:
        return f"{fmt_val(min_val)}–{fmt_val(max_val)} {unit}"
    if not min_na:
        return f"{fmt_val(min_val)}–no data {unit}"
    return f"no data–{fmt_val(max_val)} {unit}"

def check_moon_overlap(row: pd.Series) -> str:
    o2_max = row.get("o2_max_pct")
    p_min = row.get("pressure_min_kpa")
    if pd.isna(o2_max) or pd.isna(p_min):
        return "no data"
    overlaps = (float(o2_max) >= MOON_O2_MIN_PCT) and (float(p_min) <= MOON_P_MAX_KPA)
    return "yes" if overlaps else "no"


def build_comparison_record(row: pd.Series) -> dict[str, str]:
    return {
        "Fuel Phase": fmt_val(row.get("fuel_phase")),
        "Fuel Description": fmt_val(row.get("fuel_description")),
        "Sample Geometry": fmt_val(row.get("sample_geometry")),
        "Hardware": fmt_val(row.get("hardware")),
        "O2 Range": fmt_range(row.get("o2_min_pct"), row.get("o2_max_pct"), "%"),
        "Pressure Range": fmt_range(
            row.get("pressure_min_kpa"), row.get("pressure_max_kpa"), "kPa"
        ),
        "Airflow Range": fmt_range(
            row.get("airflow_min_cm_s"), row.get("airflow_max_cm_s"), "cm/s"
        ),
        "Diluents": fmt_val(row.get("diluents")),
        "Sensors": fmt_val(row.get("sensors")),
        "Safety Role": fmt_val(row.get("safety_role")),
        "Overlaps Moon Base Zone": check_moon_overlap(row),
    }

filter_cols = ["project_family", "fuel_phase", "safety_role", "hardware", "verified"]

with st.sidebar:
    st.header("Filters")
    selected_filters = {}
    for col in filter_cols:
        if col in inv_df.columns:
            options = sorted(
                inv_df[col].apply(fmt_val).unique().tolist()
            )
            selected_filters[col] = st.multiselect(
                col.replace("_", " ").title(),
                options=options,
                default=options,
            )
    search_query = st.text_input("Search by investigation name or fuel description", "")

tab_catalog, tab_compare = st.tabs(["Catalog", "Comparison"])

with tab_catalog:
    filtered_df = inv_df.copy()
    for col, allowed_vals in selected_filters.items():
        filtered_df = filtered_df[filtered_df[col].apply(fmt_val).isin(allowed_vals)]

    if search_query.strip():
        q = search_query.strip().lower()
        name_match = (
            filtered_df["name"].fillna("").astype(str).str.lower().str.contains(q, na=False)
        )
        fuel_match = (
            filtered_df["fuel_description"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(q, na=False)
        )
        filtered_df = filtered_df[name_match | fuel_match]

    st.subheader(f"Investigations ({len(filtered_df)})")

    display_df = filtered_df.copy()
    for col in display_df.columns:
        display_df[col] = display_df[col].apply(fmt_val)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Investigation Details")

    if filtered_df.empty:
        st.info("No investigations match the current filters.")
    else:
        name_options = filtered_df["name"].apply(fmt_val).tolist()
        selected_name = st.selectbox("Select an investigation", options=name_options)

        selected_row = filtered_df[filtered_df["name"].apply(fmt_val) == selected_name].iloc[0]
        inv_id = fmt_val(selected_row.get("id"))

        test_count = int(
            (tests_df["investigation_id"].astype(str) == str(selected_row.get("id"))).sum()
        )

        o2_range = fmt_range(selected_row.get("o2_min_pct"), selected_row.get("o2_max_pct"), "%")
        pressure_range = fmt_range(
            selected_row.get("pressure_min_kpa"), selected_row.get("pressure_max_kpa"), "kPa"
        )
        airflow_range = fmt_range(
            selected_row.get("airflow_min_cm_s"), selected_row.get("airflow_max_cm_s"), "cm/s"
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Test Conditions Count", test_count)
        m2.metric("O2 Range", o2_range)
        m3.metric("Pressure Range", pressure_range)
        m4.metric("Airflow Range", airflow_range)

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown(f"**ID:** {inv_id}")
            st.markdown(f"**Name:** {fmt_val(selected_row.get('name'))}")
            st.markdown(f"**Project Family:** {fmt_val(selected_row.get('project_family'))}")
            st.markdown(f"**Safety Role:** {fmt_val(selected_row.get('safety_role'))}")
            st.markdown(f"**Fuel Phase:** {fmt_val(selected_row.get('fuel_phase'))}")
            st.markdown(f"**Fuel Description:** {fmt_val(selected_row.get('fuel_description'))}")
            st.markdown(f"**Sample Geometry:** {fmt_val(selected_row.get('sample_geometry'))}")
            st.markdown(f"**Hardware:** {fmt_val(selected_row.get('hardware'))}")

        with col_right:
            st.markdown(f"**Diluents:** {fmt_val(selected_row.get('diluents'))}")
            st.markdown(f"**Sensors:** {fmt_val(selected_row.get('sensors'))}")
            st.markdown(f"**Verified:** {fmt_val(selected_row.get('verified'))}")
            st.markdown(f"**Source Document:** {fmt_val(selected_row.get('source_doc'))}")
            st.markdown(f"**Source Page:** {fmt_val(selected_row.get('source_page'))}")

            psi_url = fmt_val(selected_row.get("psi_url"))
            if psi_url != "no data" and psi_url.startswith(("http://", "https://")):
                st.markdown(f"**PSI URL:** [{psi_url}]({psi_url})")
            else:
                st.markdown(f"**PSI URL:** {psi_url}")

            st.markdown(f"**Notes:** {fmt_val(selected_row.get('notes'))}")

with tab_compare:
    st.subheader("Side-by-Side Investigation Comparison")
    all_names = inv_df["name"].apply(fmt_val).tolist()

    if len(all_names) < 2:
        st.info("Not enough investigations loaded for comparison.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            name_a = st.selectbox("First Investigation", options=all_names, index=0, key="cmp_a")
        with c2:
            default_b = 1 if len(all_names) > 1 else 0
            name_b = st.selectbox(
                "Second Investigation", options=all_names, index=default_b, key="cmp_b"
            )

        row_a = inv_df[inv_df["name"].apply(fmt_val) == name_a].iloc[0]
        row_b = inv_df[inv_df["name"].apply(fmt_val) == name_b].iloc[0]

        rec_a = build_comparison_record(row_a)
        rec_b = build_comparison_record(row_b)

        col_a_label = f"{fmt_val(row_a.get('id'))} — {name_a}"
        col_b_label = f"{fmt_val(row_b.get('id'))} — {name_b}"
        if col_a_label == col_b_label:
            col_b_label = f"{col_b_label} (2)"

        comp_rows = []
        for field in rec_a:
            val_a = rec_a[field]
            val_b = rec_b[field]
            comp_rows.append(
                {
                    "Field": field,
                    "Match": "=" if val_a == val_b else "≠",
                    col_a_label: val_a,
                    col_b_label: val_b,
                }
            )

        comp_df = pd.DataFrame(comp_rows)

        def highlight_diff(row: pd.Series) -> list[str]:
            if row["Match"] != "=":
                return ["background-color: rgba(255, 165, 0, 0.22)"] * len(row)
            return [""] * len(row)

        st.dataframe(
            comp_df.style.apply(highlight_diff, axis=1),
            use_container_width=True,
            hide_index=True,
        )