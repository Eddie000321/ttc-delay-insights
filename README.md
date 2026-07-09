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
- FastAPI + SQLAlchemy: lightweight analytics API over Postgres
- Vite + React + Chart.js: interactive frontend consuming the API
- psql / DataGrip / pgAdmin: DB access and query execution
- Default connection (docker-compose): host `localhost:5433`, DB/USER/PASS `ttc`

Quickstart

- Prerequisites:
  - Docker + Docker Compose
  - Python 3.10+ with pip packages: `pandas`, `openpyxl`
  - Node.js 18+ for frontend (Vite + React)
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

Frontend + API (Local)

- API (FastAPI):
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r api/requirements.txt`
  - `uvicorn api.main:app --reload --port 8000`
- Frontend (Vite + React):
  - `cd web && cp .env.example .env`  # optional; Vite dev proxy handles `/api`
  - `npm install`
  - `npm run dev`
- Notes:
  - Vite dev server proxies `/api` to `http://localhost:8000` by default; or set `VITE_API_URL` in `web/.env`.
  - See `docs/frontend.md` for endpoint list and details.

Quality Checks

- ETL smoke/unit tests (uses Python's standard-library test runner plus the project runtime dependency `pandas`):
  - `python -m unittest discover -s tests -v`
- Frontend production build and TypeScript check:
  - `cd web && npm ci && npm run build`

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
- Frontend + API: `docs/frontend.md`
- Docker: `docker-compose.yml`

Data Model

- Primary (split by mode):
  - Tables: `ttc_delays_subway`, `ttc_delays_streetcar`, `ttc_delays_bus`
  - Columns (each): `date`, `time`, `day`, `station`, `line`, `bound` (N/E/S/W), `code`, `min_delay`, `min_gap`, `vehicle`, `raw_file`
  - Indexes: `(date)`, `(line)`, `(station)`
  - SQL: `db/init/006_schema_split.sql`, `db/init/007_import_split.sql`
- Code dictionaries (per mode):
  - Tables: `ttc_code_dictionary_subway`, `ttc_code_dictionary_streetcar`, `ttc_code_dictionary_bus`
  - SQL: `db/init/008_code_dictionary_split.sql`, `db/init/009_import_code_dictionary_split.sql`
- Views (with descriptions):
  - `sql/views/vw_split_with_desc.sql` → `vw_subway_with_desc`, `vw_streetcar_with_desc`, `vw_bus_with_desc`, and optional `vw_delays_all_with_desc`
- Legacy/optional unified table remains available for compatibility:
  - `ttc_delays` + `ttc_code_dictionary` (see `db/init/001_schema.sql`…`005_import_code_dictionary.sql`)

SQL Usage

- Exploration: `sql/exploration/sample_queries.sql`
- Reporting:
  - Top stations with parameters: `sql/reporting/top_stations.sql`
  - Monthly by mode: `sql/reporting/monthly_by_mode.sql`
- Views / Materialized views:
  - Split views with description: `sql/views/vw_split_with_desc.sql`
  - Daily counts (legacy unified): `sql/views/vw_daily_counts.sql`
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
- `api/`: FastAPI app exposing analytics endpoints
- `web/`: Vite + React frontend consuming the API
- `docker-compose.yml`: Postgres service (port 5433)

Findings (Early)

- Subway: more frequent but shorter delays
- Bus: longer delays and larger headway gaps
- Streetcar: higher variability, notably at rush hours
- Common causes: mechanical and signal issues; seasonal spikes for weather
- Details: `docs/findings.md`

Roadmap

- Orchestration: schedule ETL with Airflow or Prefect
- API: implemented (FastAPI + SQLAlchemy). Next: deploy and add caching/MTV refresh schedules
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

Generate Figures (script)

- Run (all modes): `python analysis/visualize.py`
- Run (specific mode/year): `python analysis/visualize.py --mode subway --year 2024`
- Run (aggregate all years):
  - All modes: `python analysis/visualize.py --mode all --all-years`
  - Single mode: `python analysis/visualize.py --mode subway --all-years`
- Defaults: reads `data/processed/ttc_delays.csv`, code dictionary from `data/processed/codes_all.csv`, writes PNGs to `reports/figures/`
- Outputs:
  - `monthly_by_mode.png`
  - `top_stations_<mode>_<year>.png` (or `<mode>_all.png` when `--all-years`)
  - `causes_<mode>_<year>.png` (uses per‑mode descriptions; `<mode>_all.png` when `--all-years`)
  - `peak_hour_<mode>_<year>.png` (or `<mode>_all.png` when `--all-years`)
  - `delay_hist_<mode>_<year>.png` (or `<mode>_all.png` when `--all-years`)

License & Attribution

- Data: Toronto Open Data Portal (TTC delays).

<!--
Portfolio Roles (hidden for portfolio use):
- Data Analyst: aggregation and SQL-based analysis
- SQL Developer: schema design and query authoring
- (Light) Data Engineer: ETL pipeline, Docker/Postgres operations
- Junior DBA: indexing, performance/capacity considerations
-->
