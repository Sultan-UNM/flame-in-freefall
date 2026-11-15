"""Mission-relevance scoring for the Flame Gap Atlas (Person A owns this file).

Usage in the app (Streamlit):
    import pandas as pd
    from scoring import score_investigations, ENVIRONMENTS, DEFAULT_WEIGHTS
    inv = pd.read_csv("investigations.csv"); tests = pd.read_csv("test_conditions.csv")
    ranked = score_investigations(inv, tests, "Moon base", weights)   # weights optional

Every score is a weighted sum of four components, each between 0 and 1:
  zone_match     how many of the investigation's tests fall inside the mission's target atmosphere
                 (70 %), plus how close its nearest test comes to that zone (30 %)
  fuel_relevance how much the fuel type resembles what burns in a crew cabin (editable table below)
  role_relevance safety role: prevention / detection / suppression count fully, fundamental half
  verified_share share of the investigation's test rows checked against PSI (verified = yes)

The weights are NOT normalised by the caller: this function divides by their sum, so the app can
pass raw slider values. Nothing here is hidden: the "why" column spells out every component.
"""
import math

import pandas as pd

# ---- target atmospheres: (o2_min %, o2_max %, p_min kPa, p_max kPa) --------------------------------
# Moon base / rover come from the challenge brief (O2 >= 30 %, pressure <= 10.2 psi = 70.3 kPa).
# ISS and Mars habitat are TEAM ASSUMPTIONS (not stated in the brief); edit them here if you disagree.
ENVIRONMENTS = {
    "ISS": {
        "box": (19.5, 24.1, 95.0, 103.0),
        "basis": "ASSUMPTION: ISS cabin air, about 1 atm and roughly 21 % O2",
    },
    "Moon base": {
        "box": (30.0, 100.0, 10.0, 70.3),
        "basis": "Challenge brief: O2 >= 30 %, pressure <= 70.3 kPa (10.2 psi)",
    },
    "Pressurized rover": {
        "box": (30.0, 100.0, 10.0, 70.3),
        "basis": "Challenge brief groups the rover with the Moon base atmosphere",
    },
    "Mars habitat": {
        "box": (30.0, 100.0, 10.0, 70.3),
        "basis": "ASSUMPTION: same reduced-pressure, O2-enriched zone as the Moon base (not in the brief)",
    },
}

DEFAULT_WEIGHTS = {"zone_match": 0.5, "fuel_relevance": 0.2, "role_relevance": 0.1, "verified_share": 0.2}

# Editable judgement tables (shown to the user as assumptions)
FUEL_RELEVANCE = {"solid": 1.0, "aerosol": 0.8, "mixed": 0.7, "liquid_droplet": 0.6, "gas": 0.5}
ROLE_RELEVANCE = {"prevention": 1.0, "detection": 1.0, "suppression": 1.0, "fundamental": 0.5}
UNKNOWN_FUEL, UNKNOWN_ROLE = 0.3, 0.3   # blank in the catalog = not stated yet

# distance scale for "how close is the nearest test to the zone": 20 O2 points ~ 100 kPa ~ 1 unit
_O2_SCALE, _P_SCALE, _DECAY = 20.0, 100.0, 0.25


def _in_box(o2, p, box):
    o2lo, o2hi, plo, phi = box
    return (o2 >= o2lo) & (o2 <= o2hi) & (p >= plo) & (p <= phi)


def _dist_to_box(o2, p, box):
    o2lo, o2hi, plo, phi = box
    d_o2 = (o2lo - o2).clip(lower=0) + (o2 - o2hi).clip(lower=0)
    d_p = (plo - p).clip(lower=0) + (p - phi).clip(lower=0)
    return ((d_o2 / _O2_SCALE) ** 2 + (d_p / _P_SCALE) ** 2) ** 0.5


def score_investigations(inv: pd.DataFrame, tests: pd.DataFrame, environment: str, weights=None) -> pd.DataFrame:
    """Return one row per investigation with component scores, total score, rank and a 'why' text."""
    if environment not in ENVIRONMENTS:
        raise ValueError(f"unknown environment {environment!r}; choose from {list(ENVIRONMENTS)}")
    w = dict(DEFAULT_WEIGHTS)
    w.update({k: float(v) for k, v in (weights or {}).items() if k in w})
    total_w = sum(w.values()) or 1.0
    box = ENVIRONMENTS[environment]["box"]

    t = tests.copy()
    t["o2_pct"] = pd.to_numeric(t["o2_pct"], errors="coerce")
    t["pressure_kpa"] = pd.to_numeric(t["pressure_kpa"], errors="coerce")
    t = t.dropna(subset=["o2_pct", "pressure_kpa"])
    t["in_zone"] = _in_box(t["o2_pct"], t["pressure_kpa"], box)
    t["dist"] = _dist_to_box(t["o2_pct"], t["pressure_kpa"], box)
    t["is_verified"] = t["verified"].astype(str).str.strip().str.lower().eq("yes")
    by_inv = {k: g for k, g in t.groupby("investigation_id")}

    rows = []
    for _, r in inv.iterrows():
        g = by_inv.get(r["id"])
        n = 0 if g is None else len(g)
        if n:
            frac = float(g["in_zone"].mean())
            n_zone = int(g["in_zone"].sum())
            prox = math.exp(-float(g["dist"].min()) / _DECAY)
            zone = 0.7 * frac + 0.3 * prox
            ver = float(g["is_verified"].mean())
            zone_txt = f"{n_zone} of {n} tests inside the {environment} zone; nearest test is {prox:.0%} as close as an in-zone test"
        else:
            n_zone, zone, ver = 0, 0.0, 0.0
            zone_txt = "no test conditions in the catalog, so zone match is 0 (not the same as 'tested and failed')"
        fuel = FUEL_RELEVANCE.get(str(r.get("fuel_phase", "")).strip(), UNKNOWN_FUEL)
        role = ROLE_RELEVANCE.get(str(r.get("safety_role", "")).strip(), UNKNOWN_ROLE)
        score = (w["zone_match"] * zone + w["fuel_relevance"] * fuel + w["role_relevance"] * role
                 + w["verified_share"] * ver) / total_w
        why = (f"{zone_txt}; fuel type '{r.get('fuel_phase') or 'not stated'}' -> {fuel:.1f}; "
               f"safety role '{r.get('safety_role') or 'not stated'}' -> {role:.1f}; "
               f"{ver:.0%} of its tests verified against PSI")
        rows.append({"id": r["id"], "name": r["name"], "zone_match": round(zone, 3),
                     "fuel_relevance": fuel, "role_relevance": role, "verified_share": round(ver, 3),
                     "tests_in_zone": n_zone, "tests_total": n, "score": round(score, 3), "why": why})
    out = pd.DataFrame(rows).sort_values(["score", "tests_in_zone"], ascending=False).reset_index(drop=True)
    out.insert(0, "rank", out.index + 1)
    return out


def environment_basis(environment: str) -> str:
    """One line the app should show next to the ranking, so the target zone is never a black box."""
    o2lo, o2hi, plo, phi = ENVIRONMENTS[environment]["box"]
    return (f"{environment} target zone: O2 {o2lo:g}-{o2hi:g} %, pressure {plo:g}-{phi:g} kPa. "
            f"{ENVIRONMENTS[environment]['basis']}")


if __name__ == "__main__":
    inv = pd.read_csv("investigations.csv")
    tests = pd.read_csv("test_conditions.csv")
    for env in ENVIRONMENTS:
        print("\n" + environment_basis(env))
        print(score_investigations(inv, tests, env).head(6)[["rank", "id", "score", "tests_in_zone", "tests_total"]].to_string(index=False))
