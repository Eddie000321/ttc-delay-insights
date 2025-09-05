# SQL Directory

This folder organizes reusable SQL for exploration, reporting, and schema-level views.

Structure
- exploration/: ad hoc queries for quick analysis
- reporting/: parameterized, reusable report queries
- views/: logical (non-materialized) views
- materialized/: materialized views and refresh scripts
- snippets/: psql-only includes (e.g., parameter defaults)
- utils/: maintenance or EXPLAIN templates

Usage (psql examples)
- Run a report with parameters:
  - psql -h localhost -p 5433 -U ttc -d ttc -v source='subway' -v from='2024-01-01' -v to='2024-12-31' -f sql/reporting/top_stations.sql
- Include common params:
  - psql -h localhost -p 5433 -U ttc -d ttc -f sql/snippets/date_params.psql -f sql/reporting/monthly_by_mode.sql
- Create/refresh views:
  - psql -h localhost -p 5433 -U ttc -d ttc -f sql/views/vw_daily_counts.sql
  - psql -h localhost -p 5433 -U ttc -d ttc -f sql/materialized/mv_monthly_counts.sql -f sql/materialized/refresh.sql

