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
  python analysis/visualize.py --mode subway --all-years  # aggregate across all years
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


def _load_data_flexible(processed_root: Path) -> pd.DataFrame:
    """Load data from unified CSV if present, otherwise concat per-mode CSVs.

    Ensures a `source` column exists for downstream grouping/plotting.
    """
    unified = processed_root / "ttc_delays.csv"
    if unified.exists():
        df = pd.read_csv(unified, low_memory=False)
        # Guarantee source column even in older outputs
        if "source" not in df.columns:
            # Infer from raw_file if possible, else leave empty
            df["source"] = pd.NA
        # Normalize types
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "time" in df.columns:
            t = pd.to_datetime(df["time"], errors="coerce")
            df["hour"] = t.dt.hour
        for c in ["min_delay", "min_gap", "vehicle"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        for c in ["source", "station"]:
            if c in df.columns:
                df[c] = df[c].astype("string").str.strip()
        if "code" in df.columns:
            df["code"] = df["code"].astype("string").str.strip().str.upper()
        return df
    # Fallback: per-mode
    frames = []
    for mode, name in [("subway", "subway_delays.csv"), ("streetcar", "streetcar_delays.csv"), ("bus", "bus_delays.csv")]:
        p = processed_root / name
        if not p.exists():
            continue
        f = pd.read_csv(p, low_memory=False)
        if "source" not in f.columns:
            f["source"] = mode
        # Normalize types
        if "date" in f.columns:
            f["date"] = pd.to_datetime(f["date"], errors="coerce")
        if "time" in f.columns:
            t = pd.to_datetime(f["time"], errors="coerce")
            f["hour"] = t.dt.hour
        for c in ["min_delay", "min_gap", "vehicle"]:
            if c in f.columns:
                f[c] = pd.to_numeric(f[c], errors="coerce")
        for c in ["source", "station"]:
            if c in f.columns:
                f[c] = f[c].astype("string").str.strip()
        if "code" in f.columns:
            f["code"] = f["code"].astype("string").str.strip().str.upper()
        frames.append(f)
    if not frames:
        raise FileNotFoundError("No processed CSVs found. Run etl_scripts/etl.py first.")
    return pd.concat(frames, ignore_index=True)


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


def _filter(df: pd.DataFrame, mode: str, year: Optional[int]) -> pd.DataFrame:
    if year is not None:
        start, end = _daterange_of_year(year)
        m = (df["date"] >= start) & (df["date"] < end)
    else:
        # No year filter (aggregate across all years)
        m = pd.Series(True, index=df.index)
    if mode != "all" and "source" in df.columns:
        m &= (df["source"] == mode)
    return df.loc[m].copy()


def fig_top_stations(df: pd.DataFrame, out_dir: Path, mode: str, year: Optional[int], topn: int = 20) -> Optional[Path]:
    if "station" not in df.columns:
        return None
    tmp = _filter(df, mode, year)
    if tmp.empty:
        return None
    top = tmp.groupby("station").size().sort_values(ascending=False).head(topn)
    yr_label = str(year) if year is not None else "all years"
    ax = top.sort_values().plot(kind="barh", figsize=(10, 6))
    ax.set_title(f"Top {topn} Stations by Count ({mode}, {yr_label})")
    ax.set_xlabel("Count")
    ax.set_ylabel("Station")
    plt.tight_layout()
    out_path = out_dir / f"top_stations_{mode}_{(year if year is not None else 'all')}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def _load_code_dict(dict_csv: Path) -> Optional[pd.DataFrame]:
    if not dict_csv.exists():
        return None
    df = pd.read_csv(dict_csv)
    # Expect columns: source, code, description
    needed = {"source", "code", "description"}
    if not needed.issubset(set(df.columns)):
        return None
    # Normalize
    for c in ["source", "code", "description"]:
        df[c] = df[c].astype("string").str.strip()
    return df.dropna(subset=["source", "code"]).drop_duplicates(["source", "code"])


def _load_code_dict_fallback(raw_root: Path = Path("data/raw")) -> Optional[pd.DataFrame]:
    """Build a dictionary by reading per-mode raw folders directly when unified file is missing.

    Looks for common filenames and flexible column names (CSV/Excel)."""
    import pandas as pd
    modes = {
        "subway": raw_root / "raw_subway",
        "streetcar": raw_root / "raw_streetcar",
        "bus": raw_root / "raw_bus",
    }
    parts = []
    for mode, d in modes.items():
        if not d.exists():
            continue
        # Try multiple candidates
        cands = [
            d / "Code Descriptions.csv",
            d / "code_descriptions.csv",
            d / "codes.csv",
            d / "code_description.csv",
        ]
        # Heuristic scan
        for p in list(cands) + list(d.glob("*.*")):
            if not p.exists():
                continue
            if p.suffix.lower() not in {".csv", ".xlsx", ".xls"}:
                continue
            name = p.name.lower()
            if "readme" in name:
                continue
            if ("code" not in name) or ("desc" not in name and "meaning" not in name and p.name not in {"codes.csv", "codes.xlsx"}):
                # must at least look like a code list
                continue
            try:
                df = pd.read_csv(p) if p.suffix.lower() == ".csv" else pd.read_excel(p)
            except Exception:
                continue
            # Coalesce columns
            cols = {c.lower(): c for c in df.columns}
            def pick(names):
                for n in names:
                    if n.lower() in cols:
                        return cols[n.lower()]
                return None
            code_col = pick(["CODE", "Code", "code", "Delay Code", "DelayCode", "Reason Code", "Cause Code"]) 
            desc_col = pick(["DESCRIPTION", "Description", "desc", "Desc", "Reason", "Cause", "Details", "Meaning"]) 
            if not code_col or not desc_col:
                continue
            df = df[[code_col, desc_col]].rename(columns={code_col: "code", desc_col: "description"})
            df["code"] = df["code"].astype("string").str.strip().str.upper()
            df["description"] = df["description"].astype("string").str.strip()
            df = df.dropna(subset=["code"]).drop_duplicates()
            if not df.empty:
                df.insert(0, "source", mode)
                parts.append(df[["source", "code", "description"]])
                break  # one good file per mode is enough
    if not parts:
        return None
    out = pd.concat(parts, ignore_index=True)
    return out.drop_duplicates(["source", "code"])


def fig_causes(
    df: pd.DataFrame,
    out_dir: Path,
    mode: str,
    year: Optional[int],
    topn: int = 20,
    dict_df: Optional[pd.DataFrame] = None,
) -> Optional[Path]:
    if "code" not in df.columns:
        return None
    tmp = _filter(df, mode, year)
    if tmp.empty:
        return None
    codes = tmp["code"].fillna("UNKNOWN")
    counts = codes.groupby(codes).size().sort_values(ascending=False).head(topn)
    yr_label = str(year) if year is not None else "all years"

    # Map codes to human-friendly labels using per-mode dictionary
    if dict_df is not None and not dict_df.empty:
        dmap = (
            dict_df.loc[dict_df["source"] == mode, ["code", "description"]]
            .set_index("code")["description"]
            .to_dict()
        )
    else:
        dmap = {}

    labeled_index = []
    for code_token in counts.index.tolist():
        desc = dmap.get(str(code_token))
        if desc and desc.upper() != "UNKNOWN":
            label = f"{desc} ({code_token})"
        else:
            label = str(code_token)
        labeled_index.append(label)

    counts.index = labeled_index
    ax = counts.sort_values().plot(kind="barh", figsize=(12, 7))
    ax.set_title(f"Top {topn} Delay Causes ({mode}, {yr_label})")
    ax.set_xlabel("Count")
    ax.set_ylabel("Cause")
    plt.tight_layout()
    out_path = out_dir / f"causes_{mode}_{(year if year is not None else 'all')}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def fig_peak_hour(df: pd.DataFrame, out_dir: Path, mode: str, year: Optional[int]) -> Optional[Path]:
    if "hour" not in df.columns:
        return None
    tmp = _filter(df, mode, year)
    if tmp.empty:
        return None
    hours = tmp["hour"].dropna().astype(int)
    counts = hours.value_counts().reindex(range(0, 24), fill_value=0).sort_index()
    yr_label = str(year) if year is not None else "all years"
    ax = counts.plot(kind="bar", figsize=(10, 4))
    ax.set_title(f"Events by Hour ({mode}, {yr_label})")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Count")
    plt.tight_layout()
    out_path = out_dir / f"peak_hour_{mode}_{(year if year is not None else 'all')}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def fig_delay_hist(df: pd.DataFrame, out_dir: Path, mode: str, year: Optional[int]) -> Optional[Path]:
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
    yr_label = str(year) if year is not None else "all years"
    plt.figure(figsize=(10, 4))
    plt.hist(s, bins=40, color="#4C78A8")
    plt.title(f"Delay Duration Distribution (0–120 min) ({mode}, {yr_label})")
    plt.xlabel("Minutes of Delay")
    plt.ylabel("Frequency")
    plt.tight_layout()
    out_path = out_dir / f"delay_hist_{mode}_{(year if year is not None else 'all')}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate TTC delay visualizations from cleaned CSV")
    ap.add_argument("--csv", type=Path, default=Path("data/processed/ttc_delays.csv"), help="Path to unified cleaned CSV (ignored if per-mode files are used)")
    ap.add_argument("--out", type=Path, default=Path("reports/figures"), help="Output directory for PNGs")
    ap.add_argument("--mode", choices=["all", "subway", "streetcar", "bus"], default="all", help="Generate charts for a specific mode or all")
    ap.add_argument("--year", type=int, default=None, help="Year for filtered charts (defaults to max year in data)")
    ap.add_argument("--all-years", action="store_true", help="Aggregate figures across all years (ignores --year)")
    ap.add_argument("--dict", type=Path, default=Path("data/processed/codes_all.csv"), help="Path to unified code dictionary CSV (source, code, description)")
    args = ap.parse_args()

    _ensure_out(args.out)
    # Prefer flexible loading to support split-by-mode design
    df = _load_data_flexible(Path("data/processed").resolve())
    dict_df = _load_code_dict(args.dict)
    if dict_df is None or dict_df.empty:
        # Try raw folder fallback
        dict_df = _load_code_dict_fallback()

    outputs = []
    # Always produce the overall monthly trend by mode
    outputs.append(fig_monthly_by_mode(df, args.out))

    modes = [args.mode] if args.mode != "all" else ["subway", "streetcar", "bus"]
    for m in modes:
        year = None if args.all_years else (args.year or _pick_year(df[df["source"] == m]))
        outputs.append(fig_top_stations(df, args.out, m, year))
        outputs.append(fig_causes(df, args.out, m, year, dict_df=dict_df))
        outputs.append(fig_peak_hour(df, args.out, m, year))
        outputs.append(fig_delay_hist(df, args.out, m, year))

    for p in outputs:
        if isinstance(p, Path):
            print(f"Saved: {p}")


if __name__ == "__main__":
    main()
