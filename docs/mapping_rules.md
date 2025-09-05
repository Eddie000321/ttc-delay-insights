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

- Subway files → `source = 'subway'`
- Streetcar files → `source = 'streetcar'`
- Bus files → `source = 'bus'`

## Transformation Rules

- Dates converted to ISO format (`YYYY-MM-DD`)
- Times converted to 24-hour format (`HH:MM` or `HH:MM:SS`)
- `bound` normalized to `N/E/S/W` or NULL
- Numeric fields coerced with `to_numeric(errors='coerce')`; invalids become NULL (0으로 대체하지 않음)
- Codes trimmed (whitespace); case normalization may be applied later
- Vehicle identifiers stored as numeric when applicable

## Validation

- `validate.py` checks: required columns, nulls, value ranges (e.g., non-negative delays), categories, duplicates.
- Database constraints enforce non-negative `min_delay/min_gap` and valid `bound` values.
- Day-of-week vs date cross-check is not yet implemented (future work).
