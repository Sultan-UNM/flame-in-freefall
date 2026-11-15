from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent

INVESTIGATION_NUMERIC_COLS = [
    "o2_min_pct",
    "o2_max_pct",
    "pressure_min_kpa",
    "pressure_max_kpa",
    "airflow_min_cm_s",
    "airflow_max_cm_s",
]

TEST_NUMERIC_COLS = [
    "o2_pct",
    "pressure_kpa",
    "flow_cm_s",
    "metric_value",
]


@st.cache_data
def load_investigations() -> pd.DataFrame:
    df = pd.read_csv(BASE_DIR / "investigations.csv")
    for col in INVESTIGATION_NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data
def load_tests() -> pd.DataFrame:
    df = pd.read_csv(BASE_DIR / "test_conditions.csv")
    for col in TEST_NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df