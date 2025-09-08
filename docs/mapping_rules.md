# Mapping Rules – Standardization Process

This document describes how raw datasets were mapped into the unified schema.

## Column Mapping

- `Report Date` / `Date` → `date`
- `Time` / `Delay Time` → `time`
- `Day` (already present) → `day`
- `Station` / `Location` → `station`
- `Line` / `Route` → `line`
- `Bound` / `Direction` → `bound`
- `Vehicle` / `Car` / `Run` → `vehicle`
- `Code` → `code`
- `Min Delay` / `Delay (min)` → `min_delay`
- `Gap` / `Min Gap` → `min_gap`

## Source Mapping

- Subway files → subway dataset (stored in `ttc_delays_subway`)
- Streetcar files → streetcar dataset (stored in `ttc_delays_streetcar`)
- Bus files → bus dataset (stored in `ttc_delays_bus`)

## Transformation Rules

- Dates converted to ISO format (`YYYY-MM-DD`)
- Times converted to 24-hour format (`HH:MM` or `HH:MM:SS`)
- `bound` normalized to `N/E/S/W` or NULL
- Numeric fields coerced with `to_numeric(errors='coerce')`; invalids become NULL (0으로 대체하지 않음)
- Codes trimmed (whitespace); case normalization may be applied later
- Vehicle identifiers stored as numeric when applicable
- Code descriptions: Per-mode code dictionaries are loaded when available and joined on `code` at query time via split views. The same `code` token can mean different things per mode.
  - ETL writes `data/processed/codes_<mode>.csv` (and a unified `codes_all.csv` for compatibility).
  - The database loads these into `ttc_code_dictionary_subway|streetcar|bus`; prefer joining per mode for authoritative descriptions.

## Validation

- `validate.py` checks: required columns, nulls, value ranges (e.g., non-negative delays), categories, duplicates.
- Database constraints enforce non-negative `min_delay/min_gap` and valid `bound` values.
- Day-of-week vs date cross-check is not yet implemented (future work).

## File Inclusion/Exclusion

- Data files considered: `*.csv`, `*.xlsx`, `*.xls` within `data/raw/<mode>/`
- Exclusions: files containing `readme` are ignored; `Code Descriptions.csv` is excluded from row ingestion but still read separately for description join.
- Output files: `data/processed/subway_delays.csv`, `streetcar_delays.csv`, `bus_delays.csv`, and unified `ttc_delays.csv` (includes `description` where available).
