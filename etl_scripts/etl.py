from pathlib import Path
from typing import List, Optional, Any
from datetime import time as dtime

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
            "date": [
                "Date",
                "DATE",
                "Report Date",
                "Reported Date",
                "ReportDate",
                "Incident Date",
                "Occurrence Date",
                "Occurence Date",
            ],
            "time": ["Time"],
            "day": ["Day"],
            "station": ["Station", "Stop", "Location"],
            "code": [
                "Code",
                "CODE",
                "Delay Code",
                "DelayCode",
                "Reason Code",
                "Cause Code",
                "Incident Code",
                "Incident",
                "Reason",
                "Cause",
            ],
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

    # Normalize time to a consistent string HH:MM (handles Excel times, numbers, and strings)
    if "time" in df.columns:
        def to_hhmm(v: Any) -> Optional[str]:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return None
            # Already a time object
            if isinstance(v, dtime):
                return f"{v.hour:02d}:{v.minute:02d}"
            # Numeric values: Excel time fraction (0..1) or HHMM integers
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if 0 <= float(v) < 1.0:
                    total_minutes = int(round(float(v) * 24 * 60))
                    hh = (total_minutes // 60) % 24
                    mm = total_minutes % 60
                    return f"{hh:02d}:{mm:02d}"
                # Treat large integers like 0..2359 in HHMM format
                ival = int(round(float(v)))
                if 0 <= ival <= 2359:
                    hh, mm = divmod(ival, 100)
                    if 0 <= hh <= 23 and 0 <= mm <= 59:
                        return f"{hh:02d}:{mm:02d}"
            # String inputs: try multiple patterns
            if isinstance(v, str):
                s = v.strip()
                if s == "":
                    return None
                # Common forms: HH:MM[:SS]
                if pd.Series([s]).str.match(r"^[0-9]{1,2}:[0-9]{2}(:[0-9]{2})?$").iloc[0]:
                    parts = s.split(":")
                    hh = int(parts[0])
                    mm = int(parts[1])
                    if 0 <= hh <= 23 and 0 <= mm <= 59:
                        return f"{hh:02d}:{mm:02d}"
                # Compact numeric string HHMM / HMM
                if s.isdigit() and 3 <= len(s) <= 4:
                    ival = int(s)
                    hh, mm = divmod(ival, 100)
                    if 0 <= hh <= 23 and 0 <= mm <= 59:
                        return f"{hh:02d}:{mm:02d}"
            # Fallback: pandas parse
            ts = pd.to_datetime(pd.Series([v]), errors="coerce").iloc[0]
            if pd.notna(ts):
                return f"{ts.hour:02d}:{ts.minute:02d}"
            return None

        df["time"] = df["time"].apply(to_hhmm).astype("string")

    # Normalize strings (strip; make code uppercase for consistent joining)
    for col in ["day", "station", "bound", "line"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .where(df[col].notna())
            )
    if "code" in df.columns:
        df["code"] = (
            df["code"].astype("string").str.strip().str.upper().where(df["code"].notna())
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
    # Enforce non-negative durations; set negatives to null to satisfy DB constraints
    for col in ["min_delay", "min_gap"]:
        if col in df.columns:
            df.loc[df[col].notna() & (df[col] < 0), col] = pd.NA

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
    df["code"] = df["code"].astype("string").str.strip().str.upper()
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
    # Helper to derive a dictionary from facts if official dictionary is missing
    def derive_dict_from_facts(df: pd.DataFrame) -> Optional[pd.DataFrame]:
        if df is None or df.empty or "code" not in df.columns:
            return None
        s = df["code"].dropna().astype("string").str.strip().str.upper().drop_duplicates()
        if s.empty:
            return None
        # Build a simple description by title-casing the token (replace underscores with space)
        desc = s.str.replace("_", " ", regex=False).str.title()
        out = pd.DataFrame({"code": s, "description": desc})
        return out

    if subway_codes is not None and not subway_codes.empty:
        sc = subway_codes.copy()
        sc["source"] = "subway"
        sc_out = PROCESSED_DIR / "codes_subway.csv"
        sc[["source", "code", "description"]].drop_duplicates(["source", "code"]).to_csv(sc_out, index=False)
        print(f"Wrote: {sc_out}")
        code_parts.append(sc[["source", "code", "description"]])
    else:
        scd = derive_dict_from_facts(subway_df)
        if scd is not None and not scd.empty:
            scd["source"] = "subway"
            sc_out = PROCESSED_DIR / "codes_subway.csv"
            scd[["source", "code", "description"]].to_csv(sc_out, index=False)
            print(f"Wrote (derived): {sc_out}")
            code_parts.append(scd[["source", "code", "description"]])

    if streetcar_codes is not None and not streetcar_codes.empty:
        st = streetcar_codes.copy()
        st["source"] = "streetcar"
        st_out = PROCESSED_DIR / "codes_streetcar.csv"
        st[["source", "code", "description"]].drop_duplicates(["source", "code"]).to_csv(st_out, index=False)
        print(f"Wrote: {st_out}")
        code_parts.append(st[["source", "code", "description"]])
    else:
        std = derive_dict_from_facts(streetcar_df)
        if std is not None and not std.empty:
            std["source"] = "streetcar"
            st_out = PROCESSED_DIR / "codes_streetcar.csv"
            std[["source", "code", "description"]].to_csv(st_out, index=False)
            print(f"Wrote (derived): {st_out}")
            code_parts.append(std[["source", "code", "description"]])

    if bus_codes is not None and not bus_codes.empty:
        bs = bus_codes.copy()
        bs["source"] = "bus"
        bs_out = PROCESSED_DIR / "codes_bus.csv"
        bs[["source", "code", "description"]].drop_duplicates(["source", "code"]).to_csv(bs_out, index=False)
        print(f"Wrote: {bs_out}")
        code_parts.append(bs[["source", "code", "description"]])
    else:
        bsd = derive_dict_from_facts(bus_df)
        if bsd is not None and not bsd.empty:
            bsd["source"] = "bus"
            bs_out = PROCESSED_DIR / "codes_bus.csv"
            bsd[["source", "code", "description"]].to_csv(bs_out, index=False)
            print(f"Wrote (derived): {bs_out}")
            code_parts.append(bsd[["source", "code", "description"]])
    if code_parts:
        all_codes = pd.concat(code_parts, ignore_index=True).drop_duplicates(["source", "code"])
        all_out = PROCESSED_DIR / "codes_all.csv"
        all_codes.to_csv(all_out, index=False)
        print(f"Wrote: {all_out}")


if __name__ == "__main__":
    main()
