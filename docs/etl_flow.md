# ETL Flow – TTC Delay Project

This document outlines the Extract, Transform, Load (ETL) pipeline.

## Extract

- Source: Toronto Open Data portal
- Files: Excel (older years, monthly sheets) and CSV (recent years)
- Services: bus, subway, streetcar

## Transform

- Unify column names across modes
- Parse date/time into consistent formats
- Normalize `bound` to `N/E/S/W` or NULL
- Coerce numeric fields; missing or invalid values remain NULL
- Output: cleaned CSV files in `data/processed/`

## Load

- Target: PostgreSQL (via Docker Compose)
- Schema: single table `ttc_delays` with standardized columns
- Constraints: `NOT NULL (date, station, source)`; `CHECK` on non-negative delays and bound category
- Indexes: `(date)`, `(line)`, `(station)`, `(source, date)` to support common queries
- Additional: materialized views – not implemented (future work)

## Tools

- Python (Pandas) for transformation
- psql / COPY command for loading
- Docker for environment reproducibility

## Validation

- Run `python etl_scripts/validate.py` after ETL to check required columns, nulls, value ranges, categories, and duplicates.
- Database constraints will reject invalid rows on load; fix issues in ETL before loading.
