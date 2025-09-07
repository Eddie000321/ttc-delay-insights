"""
Generate simple visualizations from cleaned TTC delay data.

Inputs
- CSV (default: data/processed/ttc_delays.csv)

Outputs (default: reports/figures)
- monthly_by_mode.png
- top_stations_<mode>_<year>.png
- causes_<mode>_<year>.png
- peak_hour_<mode>_<year>.png
- delay_hist_<mode>_<year>.png

Usage examples
  python analysis/visualize.py
  python analysis/visualize.py --mode subway --year 2024
  python analysis/visualize.py --csv data/processed/ttc_delays.csv --out reports/figures
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt


def _ensure_out(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)


def _load_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path} (run etl_scripts/etl.py first)")
    df = pd.read_csv(csv_path)
    # Robust parsing for date/time/numerics
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "time" in df.columns:
        # Parse to datetime; we'll use hour for peak charts
        t = pd.to_datetime(df["time"], errors="coerce")
        df["hour"] = t.dt.hour
    for c in ["min_delay", "min_gap"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # Normalize text columns for grouping
    for c in ["source", "station", "code"]:
        if c in df.columns:
            df[c] = df[c].astype("string").str.strip()
    return df


def _pick_year(df: pd.DataFrame) -> int:
    if "date" not in df.columns or df["date"].isna().all():
        # Fallback: current year if dates missing
        return pd.Timestamp.today().year
    years = df["date"].dt.year.dropna().astype(int)
    return int(years.max())


def _daterange_of_year(year: int) -> Tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(year=year, month=1, day=1)
    end = pd.Timestamp(year=year + 1, month=1, day=1)
    return start, end


def fig_monthly_by_mode(df: pd.DataFrame, out_dir: Path) -> Path:
    if "date" not in df.columns or "source" not in df.columns:
        raise ValueError("Required columns missing: date, source")
    tmp = df.copy()
    tmp = tmp.dropna(subset=["date"]).copy()
    tmp["month"] = tmp["date"].dt.to_period("M").dt.to_timestamp()
    monthly = tmp.groupby(["month", "source"]).size().unstack(fill_value=0)

    ax = monthly.plot(figsize=(10, 4))
    ax.set_title("Monthly Delay Events by Mode")
    ax.set_ylabel("Count")
    ax.set_xlabel("Month")
    plt.tight_layout()
    out_path = out_dir / "monthly_by_mode.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def _filter(df: pd.DataFrame, mode: str, year: int) -> pd.DataFrame:
    start, end = _daterange_of_year(year)
    m = (df["date"] >= start) & (df["date"] < end)
    if mode != "all" and "source" in df.columns:
        m &= (df["source"] == mode)
    return df.loc[m].copy()


def fig_top_stations(df: pd.DataFrame, out_dir: Path, mode: str, year: int, topn: int = 20) -> Optional[Path]:
    if "station" not in df.columns:
        return None
    tmp = _filter(df, mode, year)
    if tmp.empty:
        return None
    top = tmp.groupby("station").size().sort_values(ascending=False).head(topn)
    ax = top.sort_values().plot(kind="barh", figsize=(10, 6))
    ax.set_title(f"Top {topn} Stations by Count ({mode}, {year})")
    ax.set_xlabel("Count")
    ax.set_ylabel("Station")
    plt.tight_layout()
    out_path = out_dir / f"top_stations_{mode}_{year}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def fig_causes(df: pd.DataFrame, out_dir: Path, mode: str, year: int, topn: int = 20) -> Optional[Path]:
    if "code" not in df.columns:
        return None
    tmp = _filter(df, mode, year)
    if tmp.empty:
        return None
    codes = tmp["code"].fillna("UNKNOWN")
    top = codes.groupby(codes).size().sort_values(ascending=False).head(topn)
    ax = top.sort_values().plot(kind="barh", figsize=(10, 6))
    ax.set_title(f"Top {topn} Delay Causes ({mode}, {year})")
    ax.set_xlabel("Count")
    ax.set_ylabel("Code")
    plt.tight_layout()
    out_path = out_dir / f"causes_{mode}_{year}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def fig_peak_hour(df: pd.DataFrame, out_dir: Path, mode: str, year: int) -> Optional[Path]:
    if "hour" not in df.columns:
        return None
    tmp = _filter(df, mode, year)
    if tmp.empty:
        return None
    hours = tmp["hour"].dropna().astype(int)
    counts = hours.value_counts().reindex(range(0, 24), fill_value=0).sort_index()
    ax = counts.plot(kind="bar", figsize=(10, 4))
    ax.set_title(f"Events by Hour ({mode}, {year})")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Count")
    plt.tight_layout()
    out_path = out_dir / f"peak_hour_{mode}_{year}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def fig_delay_hist(df: pd.DataFrame, out_dir: Path, mode: str, year: int) -> Optional[Path]:
    if "min_delay" not in df.columns:
        return None
    tmp = _filter(df, mode, year)
    if tmp.empty:
        return None
    s = tmp["min_delay"].dropna()
    if s.empty:
        return None
    # Cap extreme outliers for readability
    s = s.clip(lower=0, upper=120)
    plt.figure(figsize=(10, 4))
    plt.hist(s, bins=40, color="#4C78A8")
    plt.title(f"Delay Duration Distribution (0–120 min) ({mode}, {year})")
    plt.xlabel("Minutes of Delay")
    plt.ylabel("Frequency")
    plt.tight_layout()
    out_path = out_dir / f"delay_hist_{mode}_{year}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate TTC delay visualizations from cleaned CSV")
    ap.add_argument("--csv", type=Path, default=Path("data/processed/ttc_delays.csv"), help="Path to unified cleaned CSV")
    ap.add_argument("--out", type=Path, default=Path("reports/figures"), help="Output directory for PNGs")
    ap.add_argument("--mode", choices=["all", "subway", "streetcar", "bus"], default="subway", help="Mode to filter for station/causes/hour/hist charts")
    ap.add_argument("--year", type=int, default=None, help="Year for filtered charts (defaults to max year in data)")
    args = ap.parse_args()

    _ensure_out(args.out)
    df = _load_csv(args.csv)
    year = args.year or _pick_year(df)

    outputs = []
    outputs.append(fig_monthly_by_mode(df, args.out))
    outputs.append(fig_top_stations(df, args.out, args.mode, year))
    outputs.append(fig_causes(df, args.out, args.mode, year))
    outputs.append(fig_peak_hour(df, args.out, args.mode, year))
    outputs.append(fig_delay_hist(df, args.out, args.mode, year))

    for p in outputs:
        if isinstance(p, Path):
            print(f"Saved: {p}")


if __name__ == "__main__":
    main()

