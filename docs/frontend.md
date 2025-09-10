Frontend + API Integration

Overview
- Backend API: FastAPI app at `api/main.py` exposes JSON endpoints backed by Postgres.
- Frontend: Vite + React + Chart.js in `web/` consumes the API to render interactive charts.

Local Run
1) Start Postgres (existing):
   - docker-compose up -d
2) API (venv recommended):
   - python -m venv .venv && source .venv/bin/activate
   - pip install -r api/requirements.txt
   - uvicorn api.main:app --reload --port 8000
3) Frontend:
   - cd web && cp .env.example .env   # optional; proxy handles /api
   - npm install
   - npm run dev

Endpoints
- GET /api/health
- GET /api/monthly-by-mode
- GET /api/top-stations?source=subway&from_date=2024-01-01&to_date=2024-12-31&limit=20
- GET /api/causes?source=bus&year=2024&limit=20
- GET /api/peak-hour?source=streetcar&year=2024

Notes
- API uses `DATABASE_URL` env var; defaults to `postgresql+psycopg://ttc:ttc@localhost:5433/ttc`.
- Vite dev server proxies `/api` to `http://localhost:8000` by default.
- Extend with new charts by adding components in `web/src/components/` and endpoints in `api/main.py`.

