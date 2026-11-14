#!/usr/bin/env python3
"""Validate investigations.csv and test_conditions.csv.

Usage:
    python validate.py [folder]          # normal check (dummy/unverified rows = warnings)
    python validate.py [folder] --final  # submission check (anything not verified=yes is an error)

Exit code 0 = no errors, 1 = errors found. Standard library only.
"""
import csv
import os
import sys

INV_COLS = [
    "id", "name", "project_family", "safety_role", "fuel_phase", "fuel_description",
    "sample_geometry", "hardware", "o2_min_pct", "o2_max_pct", "pressure_min_kpa",
    "pressure_max_kpa", "airflow_min_cm_s", "airflow_max_cm_s", "diluents", "sensors",
    "psi_url", "source_doc", "source_page", "verified", "notes",
]
TEST_COLS = [
    "investigation_id", "test_id", "fuel", "o2_pct", "pressure_kpa", "flow_cm_s",
    "diluent", "outcome", "metric_name", "metric_value", "metric_unit",
    "source_doc", "source_page", "verified", "notes",
]

ENUMS = {
    "inv": {
        "project_family": {"ACME", "BASS", "SAME", "FLEX", "Saffire", "SPICE", "SLICE", "DAFT", "other"},
        "safety_role": {"prevention", "detection", "suppression", "fundamental", "other"},
        "fuel_phase": {"solid", "liquid_droplet", "gas", "aerosol", "mixed"},
        "hardware": {"CIR", "MSG", "Saffire", "other"},
        "verified": {"yes", "no"},
    },
    "test": {
        "outcome": {"sustained", "extinguished", "no_ignition", "unknown", ""},
        "verified": {"yes", "no", "dummy"},
    },
}

# (column, low, high) -- blank is allowed (= unknown) unless listed in REQUIRED_NUM
INV_NUM = [
    ("o2_min_pct", 0, 100), ("o2_max_pct", 0, 100),
    ("pressure_min_kpa", 0, 500), ("pressure_max_kpa", 0, 500),
    ("airflow_min_cm_s", 0, 1000), ("airflow_max_cm_s", 0, 1000),
]
TEST_NUM = [
    ("o2_pct", 0, 100), ("pressure_kpa", 0, 500), ("flow_cm_s", 0, 1000),
]
TEST_REQUIRED_NUM = {"o2_pct", "pressure_kpa"}  # needed for the coverage map
INV_PAIRS = [("o2_min_pct", "o2_max_pct"), ("pressure_min_kpa", "pressure_max_kpa"),
             ("airflow_min_cm_s", "airflow_max_cm_s")]


def read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or [], list(reader)


def to_float(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def check_columns(name, found, expected, errors):
    missing = [c for c in expected if c not in found]
    extra = [c for c in found if c not in expected]
    if missing:
        errors.append(f"{name}: missing columns: {missing}")
    if extra:
        errors.append(f"{name}: unexpected columns (renamed?): {extra}")
    return not missing


def check_numbers(name, rows, spec, required, errors, warnings, label):
    for i, row in enumerate(rows, start=2):
        for col, lo, hi in spec:
            raw = (row.get(col) or "").strip()
            if raw == "":
                if col in required:
                    errors.append(f"{name} line {i} ({row.get(label)}): {col} is required")
                continue
            val = to_float(raw)
            if val is None:
                errors.append(f"{name} line {i} ({row.get(label)}): {col}='{raw}' is not a number")
            elif not (lo <= val <= hi):
                errors.append(f"{name} line {i} ({row.get(label)}): {col}={val} outside {lo}..{hi}")
            elif col.startswith("o2") and 0 < val <= 1:
                warnings.append(f"{name} line {i} ({row.get(label)}): {col}={val} looks like a fraction; "
                                "use percent (21, not 0.21)")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    final = "--final" in sys.argv
    folder = args[0] if args else os.path.dirname(os.path.abspath(__file__))
    errors, warnings = [], []

    inv_path = os.path.join(folder, "investigations.csv")
    test_path = os.path.join(folder, "test_conditions.csv")
    for p in (inv_path, test_path):
        if not os.path.exists(p):
            print(f"ERROR: {p} not found")
            return 1

    inv_cols, inv = read(inv_path)
    test_cols, tests = read(test_path)
    inv_ok = check_columns("investigations", inv_cols, INV_COLS, errors)
    test_ok = check_columns("test_conditions", test_cols, TEST_COLS, errors)

    if inv_ok:
        seen = set()
        for i, row in enumerate(inv, start=2):
            rid = (row["id"] or "").strip()
            if not rid:
                errors.append(f"investigations line {i}: id is empty")
            elif rid in seen:
                errors.append(f"investigations line {i}: duplicate id '{rid}'")
            seen.add(rid)
            for col, allowed in ENUMS["inv"].items():
                if (row[col] or "").strip() not in allowed:
                    errors.append(f"investigations line {i} ({rid}): {col}='{row[col]}' not in {sorted(allowed)}")
            if (row["verified"] or "").strip() == "yes":
                for col in ("name", "source_doc", "source_page", "fuel_phase", "hardware"):
                    if not (row[col] or "").strip():
                        errors.append(f"investigations line {i} ({rid}): verified=yes needs {col}")
        check_numbers("investigations", inv, INV_NUM, set(), errors, warnings, "id")
        for i, row in enumerate(inv, start=2):
            for lo_c, hi_c in INV_PAIRS:
                lo, hi = to_float(row[lo_c]), to_float(row[hi_c])
                if lo is not None and hi is not None and lo > hi:
                    errors.append(f"investigations line {i} ({row['id']}): {lo_c} > {hi_c}")
        inv_ids = seen
    else:
        inv_ids = set()

    if test_ok:
        keys = set()
        for i, row in enumerate(tests, start=2):
            key = (row["investigation_id"], row["test_id"])
            if key in keys:
                errors.append(f"test_conditions line {i}: duplicate (investigation_id, test_id) {key}")
            keys.add(key)
            if inv_ok and row["investigation_id"] not in inv_ids:
                errors.append(f"test_conditions line {i}: unknown investigation_id '{row['investigation_id']}'")
            for col, allowed in ENUMS["test"].items():
                if (row[col] or "").strip() not in allowed:
                    errors.append(f"test_conditions line {i}: {col}='{row[col]}' not in {sorted(allowed)}")
            if (row["verified"] or "").strip() == "yes":
                for col in ("source_doc", "source_page"):
                    if not (row[col] or "").strip():
                        errors.append(f"test_conditions line {i}: verified=yes needs {col}")
        check_numbers("test_conditions", tests, TEST_NUM, TEST_REQUIRED_NUM, errors, warnings, "test_id")

    # Verification status summary
    inv_unver = [r["id"] for r in inv if (r.get("verified") or "") != "yes"]
    test_status = {}
    for r in tests:
        test_status[r.get("verified") or ""] = test_status.get(r.get("verified") or "", 0) + 1
    msg_inv = f"{len(inv_unver)} of {len(inv)} investigations not verified"
    msg_test = f"test rows by status: {test_status or 'none'}"
    if final:
        if inv_unver:
            errors.append(f"--final: {msg_inv}: {inv_unver}")
        bad = {k: v for k, v in test_status.items() if k != "yes"}
        if bad:
            errors.append(f"--final: test rows not verified=yes: {bad}")
    else:
        if inv_unver:
            warnings.append(msg_inv)
        if test_status.get("dummy"):
            warnings.append(f"{test_status['dummy']} DUMMY test rows present; remove before submission")

    for w in warnings:
        print("WARN :", w)
    for e in errors:
        print("ERROR:", e)
    print(f"\n{len(inv)} investigations, {len(tests)} test rows | {msg_test}")
    print("FAILED" if errors else "OK", f"({len(errors)} errors, {len(warnings)} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
