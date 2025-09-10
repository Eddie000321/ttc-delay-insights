import os
from datetime import date, timedelta
from typing import List, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://ttc:ttc@localhost:5433/ttc"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


app = FastAPI(title="TTC Delay Insights API")

# CORS for local dev (Vite default at 5173)
origins = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthOut(BaseModel):
    status: str
    db: bool


@app.get("/api/health", response_model=HealthOut)
def health() -> HealthOut:
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return HealthOut(status="ok", db=True)
    except Exception:
        return HealthOut(status="degraded", db=False)


class MonthlyPoint(BaseModel):
    month: date
    source: str
    n: int


@app.get("/api/monthly-by-mode", response_model=List[MonthlyPoint])
def monthly_by_mode() -> List[MonthlyPoint]:
    sql = text(
        """
        SELECT
          date_trunc('month', date)::date AS month,
          source,
          COUNT(*) AS n
        FROM ttc_delays
        GROUP BY 1, 2
        ORDER BY 1, 2;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    return [MonthlyPoint(**dict(r)) for r in rows]


class TopStation(BaseModel):
    station: Optional[str]
    n: int


@app.get("/api/top-stations", response_model=List[TopStation])
def top_stations(
    source: str = Query(..., pattern="^(subway|streetcar|bus)$"),
    from_date: date = Query(..., description="inclusive start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="inclusive end date (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100),
) -> List[TopStation]:
    # Make end exclusive by adding 1 day
    end_exclusive = to_date + timedelta(days=1)
    sql = text(
        """
        SELECT station, COUNT(*) AS n
        FROM ttc_delays
        WHERE source = :source
          AND date >= :from_date
          AND date <  :end_exclusive
        GROUP BY station
        ORDER BY n DESC
        LIMIT :limit;
        """
    )
    params = {
        "source": source,
        "from_date": from_date,
        "end_exclusive": end_exclusive,
        "limit": limit,
    }
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [TopStation(**dict(r)) for r in rows]


class CausePoint(BaseModel):
    label: str
    code: Optional[str]
    n: int


@app.get("/api/causes", response_model=List[CausePoint])
def causes(
    source: str = Query(..., pattern="^(subway|streetcar|bus)$"),
    year: int = Query(..., ge=2000, le=2100),
    limit: int = Query(20, ge=1, le=100),
) -> List[CausePoint]:
    # Prefer per-mode description join when available via split tables
    # Fallback to code only if dictionary not present
    sql = text(
        """
        WITH rng AS (
          SELECT make_date(:year, 1, 1) AS start_d,
                 make_date(:year + 1, 1, 1) AS end_d
        )
        SELECT
          COALESCE(d.description, 'UNKNOWN') AS label,
          t.code AS code,
          COUNT(*) AS n
        FROM ttc_delays t
        CROSS JOIN rng
        LEFT JOIN (
          SELECT source, code, description FROM ttc_code_dictionary_subway
          UNION ALL
          SELECT source, code, description FROM ttc_code_dictionary_streetcar
          UNION ALL
          SELECT source, code, description FROM ttc_code_dictionary_bus
        ) d
          ON d.source = t.source AND d.code = t.code
        WHERE t.source = :source
          AND t.date >= rng.start_d
          AND t.date <  rng.end_d
        GROUP BY label, t.code
        ORDER BY n DESC
        LIMIT :limit;
        """
    )
    params = {"source": source, "year": year, "limit": limit}
    with engine.connect() as conn:
        rows = conn.execute(sql, params).mappings().all()
    return [CausePoint(label=r["label"], code=r["code"], n=r["n"]) for r in rows]


class HourPoint(BaseModel):
    hour: int
    n: int


@app.get("/api/peak-hour", response_model=List[HourPoint])
def peak_hour(
    source: str = Query(..., pattern="^(subway|streetcar|bus)$"),
    year: int = Query(..., ge=2000, le=2100),
) -> List[HourPoint]:
    # Use `time` column if parseable; fallback to hour extracted in DB if present
    sql = text(
        """
        WITH rng AS (
          SELECT make_date(:year, 1, 1) AS start_d,
                 make_date(:year + 1, 1, 1) AS end_d
        )
        SELECT EXTRACT(HOUR FROM to_timestamp(NULLIF(time, '') , 'HH24:MI'))::int AS hour,
               COUNT(*) AS n
        FROM ttc_delays t
        CROSS JOIN rng
        WHERE t.source = :source
          AND t.date >= rng.start_d
          AND t.date <  rng.end_d
        GROUP BY 1
        ORDER BY 1;
        """
    )
    params = {"source": source, "year": year}
    with engine.connect() as conn:
        rows = conn.execute(sql, params).all()
    # Fill missing hours 0..23 with 0 for chart friendliness
    got = {int(h or 0): int(n or 0) for h, n in rows if h is not None}
    return [HourPoint(hour=h, n=got.get(h, 0)) for h in range(24)]

