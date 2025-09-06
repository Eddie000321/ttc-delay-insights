# ETL Flow – TTC Delay Project

This document outlines the Extract, Transform, Load (ETL) pipeline and the exact paths used in this repository.

## Extract

- Source: Toronto Open Data portal
- Files: Excel (older years, monthly sheets) and CSV (recent years)
- Services: bus, subway, streetcar
- Meta files handling: files containing `readme` are ignored; `Code Descriptions.csv` is not ingested as data rows and is used only for code-to-description joining.

## Transform

- Scripts: `etl_scripts/etl.py`
- Unify column names across modes
- Parse date/time into consistent formats
- Normalize `bound` to `N/E/S/W` or NULL
- Coerce numeric fields; missing or invalid values remain NULL
- Join code descriptions when available (subway/streetcar) to add `description`
- Output: cleaned CSV files in `data/processed/`

## Load

- Target: PostgreSQL (via Docker Compose)
- Compose file: `docker-compose.yml` (host port `5433` → container `5432`)
- Mounts: host `./data/processed` → container `/import` (read-only)
- Schema: single table `ttc_delays` with standardized columns (see `db/init/001_schema.sql`)
- Load: `COPY` from `/import/ttc_delays.csv` (see `db/init/002_import.sql`)
- Constraints: `NOT NULL (date, station, source)`; `CHECK` on non-negative delays and bound category
- Indexes: `(date)`, `(line)`, `(station)`, `(source, date)` (see `db/init/003_indexes.sql`)
- Additional: materialized view `mv_monthly_counts` and refresh script are provided.
  - Create (first time): `psql -h localhost -p 5433 -U ttc -d ttc -f sql/materialized/mv_monthly_counts.sql`
  - Refresh: `psql -h localhost -p 5433 -U ttc -d ttc -f sql/materialized/refresh.sql`

## Tools

- Python (Pandas) for transformation
- psql / COPY command for loading
- Docker for environment reproducibility

## Validation

- Script: `etl_scripts/validate.py`
- Checks required columns, nulls, value ranges, categories, and duplicate candidates
- Database constraints will reject invalid rows on load; fix issues in ETL before loading.
