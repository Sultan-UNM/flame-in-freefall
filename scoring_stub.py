import pandas as pd

DEFAULT_WEIGHTS: dict[str, float] = {
    "zone_match": 0.4,
    "fuel_relevance": 0.25,
    "role_relevance": 0.2,
    "verified_share": 0.15,
}


def environment_basis(environment: str) -> str:
    return f"Target environment basis for {environment} (stub fallback)."


def score_investigations(
    investigations_df: pd.DataFrame,
    tests_df: pd.DataFrame,
    environment: str,
    weights: dict[str, float],
) -> pd.DataFrame:
    if investigations_df.empty:
        return pd.DataFrame(columns=["id", "name", "score", "why"])

    test_counts = (
        tests_df["investigation_id"]
        .astype(str)
        .value_counts()
        .to_dict()
        if not tests_df.empty and "investigation_id" in tests_df.columns
        else {}
    )

    weight_sum = sum(float(v) for v in weights.values())

    rows = []
    for _, row in investigations_df.iterrows():
        inv_id = str(row.get("id", "no data")) if pd.notna(row.get("id")) else "no data"
        inv_name = (
            str(row.get("name", "no data")) if pd.notna(row.get("name")) else "no data"
        )
        count = int(test_counts.get(inv_id, 0))
        score_val = round(count * weight_sum, 2)
        rows.append(
            {
                "id": inv_id,
                "name": inv_name,
                "score": score_val,
                "why": f"Stub score for {environment}: {count} test conditions (weight sum={weight_sum:.2f})",
            }
        )

    result_df = pd.DataFrame(rows)
    result_df = result_df.sort_values(by=["score", "id"], ascending=[False, True]).reset_index(
        drop=True
    )
    return result_df
