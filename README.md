TTC Delay Data Project

Goal

- Collect, clean, and load TTC Subway, Streetcar, and Bus delay data (2014–present) to explore “Why does the TTC experience frequent delays?” using a database- and SQL‑first workflow.
- Scope: BI tools (e.g., Power BI / Looker Studio) are intentionally out of scope; this project focuses on ETL, PostgreSQL, and SQL analysis.

Data Sources

- Official: Toronto Open Data Portal (TTC delays datasets)
- Formats: historical Excel (monthly sheets) and newer CSV files
- Modes: Subway, Streetcar, Bus
- Scale characteristics: Bus > Subway > Streetcar
- Typical columns: Date, Time, Day, Station, Line, Code, Min Delay, Min Gap, Bound, Vehicle

Stack

- Python + Pandas: convert and standardize raw Excel/CSV into cleaned CSV
- Docker + PostgreSQL 16: load and manage the database
- psql / DataGrip / pgAdmin: DB access and query execution
- Default connection (docker-compose): host `localhost:5433`, DB/USER/PASS `ttc`

Quickstart

- Prerequisites:
  - Docker + Docker Compose
  - Python 3.10+ with pip packages: `pandas`, `openpyxl`
- Setup:
  - Create venv and install deps:
    - `python -m venv .venv && source .venv/bin/activate`
    - `python -m pip install -U pip pandas openpyxl`
  - Place raw files:
    - Subway: `data/raw/raw_subway`
    - Streetcar: `data/raw/raw_streetcar`
    - Bus: `data/raw/raw_bus`
    - Optional: `Code Descriptions.csv` inside subway/streetcar folders for cause descriptions
- Run ETL:
  - `python etl_scripts/etl.py`
  - Outputs: `data/processed/subway_delays.csv`, `data/processed/streetcar_delays.csv`, `data/processed/bus_delays.csv`, `data/processed/ttc_delays.csv`
- Start DB:
  - `docker-compose up -d`
  - Initializes schema, imports CSV, and creates indexes automatically
  - Mounts: host `./data/processed` → container `/import`; `COPY` reads `/import/ttc_delays.csv`
- Connect and explore:
  - `psql -h localhost -p 5433 -U ttc -d ttc`
  - Example report: `psql -h localhost -p 5433 -U ttc -d ttc -v source='subway' -v from='2024-01-01' -v to='2024-12-31' -f sql/reporting/top_stations.sql`

ETL Pipeline

- Extract:
  - Download yearly/monthly TTC delay files from Toronto Open Data (Excel/CSV) for Subway, Streetcar, Bus.
- Transform:
  - Merge monthly sheets where applicable
  - Standardize columns and date/time formats
  - Normalize direction to N/E/S/W (or NULL)
  - Add `source` column (subway/streetcar/bus)
  - Join `Code Descriptions.csv` (if available) to add `description`
- Load:
  - COPY the unified CSV into PostgreSQL (Docker container mount)
  - Single fact table `ttc_delays` with indexing and constraints
- Validation:
  - `etl_scripts/validate.py` checks required columns, nulls, ranges, categories, and duplicate candidates

Files

- ETL: `etl_scripts/etl.py`
- Validation: `etl_scripts/validate.py`
- Flow & rules: `docs/etl_flow.md`, `docs/mapping_rules.md`
- Data dictionary: `docs/data_dictionary.md`
- Docker: `docker-compose.yml`

Data Model

- Table: `ttc_delays`
- Columns: `date`, `time`, `day`, `station`, `line`, `bound` (N/E/S/W), `code`, `min_delay`, `min_gap`, `vehicle`, `source` (bus/subway/streetcar), `raw_file`, `description`
- Constraints: non‑negative delay/gap; `bound` in {N,E,S,W} or NULL
- Indexes: `(date)`, `(line)`, `(station)`, `(source, date)`
- SQL definitions:
  - Schema: `db/init/001_schema.sql`
  - Import (COPY): `db/init/002_import.sql`
  - Indexes: `db/init/003_indexes.sql`

SQL Usage

- Exploration: `sql/exploration/sample_queries.sql`
- Reporting:
  - Top stations with parameters: `sql/reporting/top_stations.sql`
  - Monthly by mode: `sql/reporting/monthly_by_mode.sql`
- Views / Materialized views:
  - Logical view (daily counts): `sql/views/vw_daily_counts.sql`
  - Materialized monthly counts (+ refresh): `sql/materialized/mv_monthly_counts.sql`, `sql/materialized/refresh.sql`
- Common psql params include: `sql/snippets/date_params.psql`
- Folder overview: `sql/README.md`

Repository Structure

- `etl_scripts/`: ETL and validation scripts
- `data/raw/`: user‑provided raw inputs
- `data/processed/`: cleaned CSV outputs
- `db/init/`: schema, import, indexes for Postgres init
- `sql/`: exploration, reporting, views, materialized views, snippets
- `docs/`: data dictionary, ETL flow, mapping rules, findings
- `docker-compose.yml`: Postgres service (port 5433)

Findings (Early)

- Subway: more frequent but shorter delays
- Bus: longer delays and larger headway gaps
- Streetcar: higher variability, notably at rush hours
- Common causes: mechanical and signal issues; seasonal spikes for weather
- Details: `docs/findings.md`

Roadmap

- Orchestration: schedule ETL with Airflow or Prefect
- API: lightweight FastAPI endpoints for common stats
- Forecasting: ML for route‑level delay probability

Future: Python Visualizations (Matplotlib/Pandas)

- Intent: Code‑centric visuals (no BI tools), suitable for quick EDA or lightweight reporting.
- Data sources:
  - From CSV: `data/processed/ttc_delays.csv`
  - From DB: SQLAlchemy/psycopg with URL `postgresql+psycopg://ttc:ttc@localhost:5433/ttc`
- Example from cleaned CSV:
  ```python
  import pandas as pd
  import matplotlib.pyplot as plt

  df = pd.read_csv('data/processed/ttc_delays.csv', parse_dates=['date'])
  monthly = df.groupby([df['date'].dt.to_period('M'), 'source']).size().unstack(fill_value=0)
  monthly.index = monthly.index.to_timestamp()
  monthly.plot(kind='line', figsize=(10, 4))
  plt.title('Monthly Delay Events by Mode')
  plt.ylabel('Count')
  plt.xlabel('Month')
  plt.tight_layout()
  plt.show()
  ```
- Potential charts: monthly counts by mode; top stations bar chart; cause distribution; peak‑hour histograms

License & Attribution

- Data: Toronto Open Data Portal (TTC delays). Please attribute TTC/Open Data as required.

<!--
Portfolio Roles (hidden for portfolio use):
- Data Analyst: aggregation and SQL-based analysis
- SQL Developer: schema design and query authoring
- (Light) Data Engineer: ETL pipeline, Docker/Postgres operations
- Junior DBA: indexing, performance/capacity considerations
-->
