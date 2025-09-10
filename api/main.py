import os
from datetime import date, timedelta
from typing import List, Optional, Dict, Tuple

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import logging
from pathlib import Path
import csv


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
    # Try split dictionaries; fallback to unified; then code-only.
    sql_split = text(
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
          SELECT 'subway'::text AS source, code, description FROM ttc_code_dictionary_subway
          UNION ALL
          SELECT 'streetcar'::text AS source, code, description FROM ttc_code_dictionary_streetcar
          UNION ALL
          SELECT 'bus'::text AS source, code, description FROM ttc_code_dictionary_bus
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
    sql_unified = text(
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
        LEFT JOIN ttc_code_dictionary d
          ON d.code = t.code
        WHERE t.source = :source
          AND t.date >= rng.start_d
          AND t.date <  rng.end_d
        GROUP BY label, t.code
        ORDER BY n DESC
        LIMIT :limit;
        """
    )
    sql_code_only = text(
        """
        WITH rng AS (
          SELECT make_date(:year, 1, 1) AS start_d,
                 make_date(:year + 1, 1, 1) AS end_d
        )
        SELECT
          COALESCE(t.code, 'UNKNOWN') AS label,
          t.code AS code,
          COUNT(*) AS n
        FROM ttc_delays t
        CROSS JOIN rng
        WHERE t.source = :source
          AND t.date >= rng.start_d
          AND t.date <  rng.end_d
        GROUP BY label, t.code
        ORDER BY n DESC
        LIMIT :limit;
        """
    )
    params = {"source": source, "year": year, "limit": limit}
    # Try each strategy in a fresh connection to avoid aborted transactions
    attempts = [("split_dict", sql_split), ("unified_dict", sql_unified), ("code_only", sql_code_only)]
    last_err: Optional[Exception] = None
    for name, stmt in attempts:
        try:
            with engine.connect() as conn:
                rows = conn.execute(stmt, params).mappings().all()
                items = [dict(r) for r in rows]
                if name == "code_only":
                    # Post-process with local CSV dictionaries if available
                    code_map = _load_code_dict_files()
                    if code_map:
                        mapped: List[CausePoint] = []
                        for r in items:
                            code = r.get("code")
                            desc = code_map.get((source, str(code) if code is not None else ""))
                            label = f"{desc} ({code})" if desc else (r.get("label") or str(code) or "UNKNOWN")
                            mapped.append(CausePoint(label=label, code=code, n=r["n"]))
                        return mapped
                # Default: use label provided by SQL
                return [CausePoint(label=r.get("label"), code=r.get("code"), n=r["n"]) for r in items]
        except Exception as e:
            last_err = e
            logging.warning("/api/causes attempt %s failed: %s", name, e)
            continue
    # As a final guard, avoid 500s: return empty list when nothing works
    logging.error("/api/causes failed all attempts: %s", last_err)
    return []


def _load_code_dict_files() -> Dict[Tuple[str, str], str]:
    """Load code→description mapping from local CSV files.

    Priority:
      1) data/processed/codes_all.csv with columns [source, code, description]
      2) data/raw/raw_<mode>/* files whose name suggests code descriptions (CSV only)
    Returns dict keyed by (source, code_upper) → description
    """
    mapping: Dict[Tuple[str, str], str] = {}

    def up(s: Optional[str]) -> str:
        return (s or "").strip().upper()

    # 1) Unified processed dictionary
    p = Path("data/processed/codes_all.csv")
    if p.exists():
        try:
            with p.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                # normalize headers
                field_map = {k.lower(): k for k in (reader.fieldnames or [])}
                src_k = field_map.get("source")
                code_k = field_map.get("code")
                desc_k = field_map.get("description")
                if src_k and code_k and desc_k:
                    for row in reader:
                        src = up(row.get(src_k))
                        code = up(row.get(code_k))
                        desc = (row.get(desc_k) or "").strip()
                        if src and code and desc:
                            mapping[(src.lower(), code)] = desc
        except Exception as e:
            logging.warning("Failed reading %s: %s", p, e)

    # 2) Per-mode raw folders
    modes = {
        "subway": Path("data/raw/raw_subway"),
        "streetcar": Path("data/raw/raw_streetcar"),
        "bus": Path("data/raw/raw_bus"),
    }
    for mode, root in modes.items():
        if not root.exists():
            continue
        candidates = [
            root / "Code Descriptions.csv",
            root / "code_descriptions.csv",
            root / "codes.csv",
            root / "code_description.csv",
        ] + [p for p in root.glob("*.csv") if ("code" in p.name.lower() and ("desc" in p.name.lower() or "meaning" in p.name.lower()))]
        for fp in candidates:
            if not fp.exists():
                continue
            try:
                with fp.open("r", encoding="utf-8-sig", newline="") as f:
                    reader = csv.DictReader(f)
                    field_map = {k.lower(): k for k in (reader.fieldnames or [])}
                    # try flexible names
                    code_k = None
                    for k in ["code", "delay code", "delaycode", "reason code", "cause code", "incident code", "incident", "reason", "cause"]:
                        if k in field_map:
                            code_k = field_map[k]
                            break
                    desc_k = None
                    for k in ["description", "desc", "reason", "cause", "details", "meaning"]:
                        if k in field_map:
                            desc_k = field_map[k]
                            break
                    if not code_k or not desc_k:
                        continue
                    for row in reader:
                        code = up(row.get(code_k))
                        desc = (row.get(desc_k) or "").strip()
                        if code and desc:
                            mapping[(mode, code)] = desc
                    break  # one file per mode is enough
            except Exception as e:
                logging.warning("Failed reading %s: %s", fp, e)
                continue
    return mapping


class HourPoint(BaseModel):
    hour: int
    n: int


@app.get("/api/peak-hour", response_model=List[HourPoint])
def peak_hour(
    source: str = Query(..., pattern="^(subway|streetcar|bus)$"),
    year: int = Query(..., ge=2000, le=2100),
) -> List[HourPoint]:
    # Robust hour extraction from time TEXT/TIME values; ignore unparsable rows.
    sql = text(
        """
        WITH rng AS (
          SELECT make_date(:year, 1, 1) AS start_d,
                 make_date(:year + 1, 1, 1) AS end_d
        ), base AS (
          SELECT
            CASE
              WHEN t.time IS NULL THEN NULL
              WHEN t.time::text ~ '^[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?$' THEN split_part(t.time::text, ':', 1)::int
              WHEN t.time::text ~ '^[0-9]{3,4}$' THEN (substring(t.time::text from 1 for length(t.time::text)-2))::int
              ELSE NULL
            END AS hour
          FROM ttc_delays t
          CROSS JOIN rng
          WHERE t.source = :source
            AND t.date >= rng.start_d
            AND t.date <  rng.end_d
        )
        SELECT hour, COUNT(*) AS n
        FROM base
        WHERE hour BETWEEN 0 AND 23
        GROUP BY hour
        ORDER BY hour;
        """
    )
    params = {"source": source, "year": year}
    with engine.connect() as conn:
        rows = conn.execute(sql, params).all()
    got = {int(h or 0): int(n or 0) for h, n in rows if h is not None}
    return [HourPoint(hour=h, n=got.get(h, 0)) for h in range(24)]
