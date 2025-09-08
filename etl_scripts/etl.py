import os
from pathlib import Path
from typing import List, Optional

import pandas as pd


RAW_DIR = Path("data/raw")
RAW_BUS = RAW_DIR / "raw_bus"
RAW_SUBWAY = RAW_DIR / "raw_subway"
RAW_STREETCAR = RAW_DIR / "raw_streetcar"

PROCESSED_DIR = Path("data/processed")


STANDARD_COLS = [
    "date",
    "time",
    "day",
    "station",
    "line",
    "bound",
    "code",
    "min_delay",
    "min_gap",
    "vehicle",
    "source",
    "raw_file",
]


def _read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    # default to Excel for .xlsx, .xls
    return pd.read_excel(path)


def _coalesce_columns(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Rename columns using first match among possible variants.

    mapping: { target: [variants...] }
    """
    rename = {}
    lower_cols = {c.lower(): c for c in df.columns}
    for target, variants in mapping.items():
        for v in variants:
            key = v.lower()
            if key in lower_cols:
                rename[lower_cols[key]] = target
                break
    if rename:
        df = df.rename(columns=rename)
    return df


def _normalize_common(df: pd.DataFrame, source: str, raw_path: Path) -> pd.DataFrame:
    # Flexible rename to standard names
    df = _coalesce_columns(
        df,
        {
            "date": ["Date", "DATE"],
            "time": ["Time"],
            "day": ["Day"],
            "station": ["Station", "Stop", "Location"],
            "code": ["Code", "CODE"],
            "min_delay": ["Min Delay", "Mins Delay", "Delay"],
            "min_gap": ["Min Gap", "Mins Gap", "Gap"],
            "bound": ["Bound", "Direction"],
            "line": ["Line", "Route"],
            "vehicle": ["Vehicle", "Run", "Car", "Train", "Bus"],
        },
    )

    # Ensure required columns exist
    for col in [
        "date",
        "time",
        "day",
        "station",
        "code",
        "min_delay",
        "min_gap",
        "bound",
        "line",
        "vehicle",
    ]:
        if col not in df.columns:
            df[col] = pd.NA

    # Parse date and normalize formats
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    # Normalize strings (strip/upper where appropriate)
    for col in ["day", "station", "bound", "line", "code"]:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
            .where(df[col].notna())
        )

    # Try to keep bound in a compact set
    bound_map = {
        "north": "N",
        "south": "S",
        "east": "E",
        "west": "W",
        "none": None,
        "n": "N",
        "s": "S",
        "e": "E",
        "w": "W",
    }
    # Normalize bound strictly to {N,E,S,W} or NA (so DB CHECK passes)
    orig_bound = df["bound"].astype("string").str.strip()
    lower = orig_bound.str.lower()
    mapped = lower.map(bound_map)
    # Fallback: if original is already a single letter like 'N','E','S','W'
    fallback_letter = orig_bound.str.upper().where(orig_bound.str.upper().isin(["N", "E", "S", "W"]))
    df["bound"] = mapped.fillna(fallback_letter)

    # Numeric coercion for durations
    for col in ["min_delay", "min_gap", "vehicle"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["source"] = source
    df["raw_file"] = str(raw_path.relative_to(Path.cwd())) if raw_path.is_absolute() else str(raw_path)

    # Restrict to standard columns and order
    df = df[[c for c in STANDARD_COLS if c in df.columns]]
    # Ensure all columns present
    for c in STANDARD_COLS:
        if c not in df.columns:
            df[c] = pd.NA
    return df[STANDARD_COLS]


def _find_code_desc_file(dir_path: Path) -> Optional[Path]:
    """Find a plausible code-description file in a raw mode directory."""
    # Hard-coded common names first (highest priority)
    preferred = [
        dir_path / "Code Descriptions.csv",
        dir_path / "code_descriptions.csv",
        dir_path / "codes.csv",
        dir_path / "code_description.csv",
    ]
    for p in preferred:
        if p.exists():
            return p
    # Fallback: scan for files that look like code-description lists
    for p in dir_path.glob("*.*"):
        name = p.name.lower()
        if p.suffix.lower() not in {".csv", ".xlsx", ".xls"}:
            continue
        if "readme" in name:
            continue
        if ("code" in name and "desc" in name) or ("code" in name and "meaning" in name):
            return p
    return None


def _read_table_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def _load_code_descriptions(dir_path: Path) -> Optional[pd.DataFrame]:
    """Load a mode-specific code description file if present.

    Tries multiple filenames and formats, returns columns [code, description].
    """
    f = _find_code_desc_file(dir_path)
    if f is None:
        return None
    try:
        df = _read_table_any(f)
    except Exception:
        return None
    df = _coalesce_columns(
        df,
        {
            "code": [
                "CODE",
                "Code",
                "code",
                "Delay Code",
                "DelayCode",
                "Reason Code",
                "Cause Code",
            ],
            "description": [
                "DESCRIPTION",
                "Description",
                "desc",
                "Desc",
                "Reason",
                "Cause",
                "Details",
                "Meaning",
            ],
        },
    )
    for col in ["code", "description"]:
        if col not in df.columns:
            return None
    df["code"] = df["code"].astype("string").str.strip()
    df["description"] = df["description"].astype("string").str.strip()
    df = df[["code", "description"]].dropna(subset=["code"]).drop_duplicates()
    return df


def _gather_files(root: Path) -> List[Path]:
    exts = {".csv", ".xlsx", ".xls"}
    files = []
    for p in root.glob("*.*"):
        if p.suffix.lower() not in exts:
            continue
        name_l = p.name.lower()
        # Skip meta files that should not be ingested as data rows
        if name_l == "code descriptions.csv":
            continue
        if "readme" in name_l:
            continue
        files.append(p)
    return sorted(files)


def process_mode(dir_path: Path, source: str, codes_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for p in _gather_files(dir_path):
        try:
            raw = _read_any(p)
        except Exception as e:
            print(f"[WARN] Skipping {p} due to read error: {e}")
            continue
        df = _normalize_common(raw, source, p)
        if codes_df is not None and "code" in df.columns:
            df = df.merge(codes_df, on="code", how="left")
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=STANDARD_COLS)
    out = pd.concat(frames, ignore_index=True)
    # basic cleanup: drop rows with no date or station
    out = out.dropna(subset=["date", "station"], how="any")
    # Sort for stability
    out = out.sort_values(["date", "source", "line", "station", "time"], na_position="last")
    return out


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    subway_codes = _load_code_descriptions(RAW_SUBWAY)
    streetcar_codes = _load_code_descriptions(RAW_STREETCAR)
    bus_codes = _load_code_descriptions(RAW_BUS)

    subway_df = process_mode(RAW_SUBWAY, "subway", subway_codes)
    streetcar_df = process_mode(RAW_STREETCAR, "streetcar", streetcar_codes)
    bus_df = process_mode(RAW_BUS, "bus", bus_codes)

    # Write per-mode
    subway_out = PROCESSED_DIR / "subway_delays.csv"
    streetcar_out = PROCESSED_DIR / "streetcar_delays.csv"
    bus_out = PROCESSED_DIR / "bus_delays.csv"

    subway_df.to_csv(subway_out, index=False)
    streetcar_df.to_csv(streetcar_out, index=False)
    bus_df.to_csv(bus_out, index=False)

    # Unified
    unified = pd.concat([subway_df, streetcar_df, bus_df], ignore_index=True)
    unified_out = PROCESSED_DIR / "ttc_delays.csv"
    unified.to_csv(unified_out, index=False)

    print(f"Wrote: {subway_out}")
    print(f"Wrote: {streetcar_out}")
    print(f"Wrote: {bus_out}")
    print(f"Wrote: {unified_out}")

    # Code dictionaries per mode + unified
    code_parts = []
    if subway_codes is not None and not subway_codes.empty:
        sc = subway_codes.copy()
        sc["source"] = "subway"
        sc_out = PROCESSED_DIR / "codes_subway.csv"
        sc[["source", "code", "description"]].drop_duplicates(["source", "code"]).to_csv(sc_out, index=False)
        print(f"Wrote: {sc_out}")
        code_parts.append(sc[["source", "code", "description"]])
    if streetcar_codes is not None and not streetcar_codes.empty:
        st = streetcar_codes.copy()
        st["source"] = "streetcar"
        st_out = PROCESSED_DIR / "codes_streetcar.csv"
        st[["source", "code", "description"]].drop_duplicates(["source", "code"]).to_csv(st_out, index=False)
        print(f"Wrote: {st_out}")
        code_parts.append(st[["source", "code", "description"]])
    if bus_codes is not None and not bus_codes.empty:
        bs = bus_codes.copy()
        bs["source"] = "bus"
        bs_out = PROCESSED_DIR / "codes_bus.csv"
        bs[["source", "code", "description"]].drop_duplicates(["source", "code"]).to_csv(bs_out, index=False)
        print(f"Wrote: {bs_out}")
        code_parts.append(bs[["source", "code", "description"]])
    if code_parts:
        all_codes = pd.concat(code_parts, ignore_index=True).drop_duplicates(["source", "code"])
        all_out = PROCESSED_DIR / "codes_all.csv"
        all_codes.to_csv(all_out, index=False)
        print(f"Wrote: {all_out}")


if __name__ == "__main__":
    main()
