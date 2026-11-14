# Flame in Freefall: team context (paste this into BOTH AI chats)

NASA Space Apps 2026, Kuala Lumpur (virtual). Hackathon 14-15 Nov, submit before 23:59 on 15 Nov.
Challenge: "Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data".

## What we are building
A Streamlit dashboard that summarizes, ranks and interprets NASA combustion investigations
(from the PSI repository: https://psi.nasa.gov/physci/repo/search?q=combustion) for crew fire safety.
Four pages:
1. **Catalog + comparison**: table of investigations, filters, side-by-side view of two investigations.
2. **Mission relevance ranking**: user picks ISS / Moon base / pressurized rover / Mars habitat; investigations are ranked with transparent, adjustable weights.
3. **Coverage map + gaps**: scatter of tested conditions (O2 % vs pressure kPa) with the Moon-base target zone shaded.
4. **AI assistant**: answers questions ONLY from our catalog, always cites the investigation, says "not in the data" otherwise.

Key facts from the brief: Moon base / rover atmosphere is expected at O2 >= 30 % with pressure <= 10.2 psi (= 70.3 kPa).
No partial-gravity data exists in PSI yet. Highest-O2 microgravity tests (up to 85 %) were ACME CFI-G, which burned gases, not solids.

## Who owns what (one owner per file)
| Files | Owner | AI |
|---|---|---|
| `investigations.csv`, `test_conditions.csv`, `scoring.py`, findings text | Person A | Claude |
| `app.py`, `pages/*`, `requirements.txt`, deployment, video | Person B | Gemini |
| `README.md`, `validate.py` | frozen; change only if BOTH agree | - |

## Rules
1. **Column names are frozen.** Never rename, add or remove columns without telling the other person. Run `python validate.py` before every commit.
2. **The app never contains data values typed by hand.** Every number comes from the two CSVs.
3. **No invented data.** Every value in the CSVs needs `source_doc` + `source_page` before `verified=yes`. Unknown = leave blank, never guess.
4. `verified=dummy` rows are only for building the UI. `python validate.py --final` must pass before submission (it fails on any dummy/unverified row).
5. Units: O2 in **percent** (21, not 0.21); pressure in **kPa** (1 psi = 6.89476 kPa); airflow in **cm/s**.
6. Commit to GitHub at least once an hour.

## Schema: investigations.csv (one row per investigation)
`id` (snake_case slug, unique) | `name` | `project_family` (ACME, BASS, SAME, FLEX, Saffire, SPICE, SLICE, DAFT, other) |
`safety_role` (prevention, detection, suppression, fundamental, other) | `fuel_phase` (solid, liquid_droplet, gas, aerosol, mixed) |
`fuel_description` | `sample_geometry` | `hardware` (CIR, MSG, Saffire, other) |
`o2_min_pct`, `o2_max_pct` | `pressure_min_kpa`, `pressure_max_kpa` | `airflow_min_cm_s`, `airflow_max_cm_s` |
`diluents` | `sensors` | `psi_url` | `source_doc` | `source_page` | `verified` (yes/no) | `notes`

## Schema: test_conditions.csv (one row per test, used for the coverage map)
`investigation_id` (must exist in investigations.csv) | `test_id` | `fuel` | `o2_pct` (required) | `pressure_kpa` (required) |
`flow_cm_s` | `diluent` | `outcome` (sustained, extinguished, no_ignition, unknown, or blank) |
`metric_name` | `metric_value` | `metric_unit` | `source_doc` | `source_page` | `verified` (yes/no/dummy) | `notes`

Blank numeric cells mean "unknown". The app must handle blanks without crashing.

## Moon-base target zone (constants for the app)
`MOON_O2_MIN_PCT = 30`, `MOON_P_MAX_KPA = 70.3`
