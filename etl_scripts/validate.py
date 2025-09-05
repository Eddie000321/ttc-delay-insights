from pathlib import Path
from typing import List

import pandas as pd


PROCESSED = Path("data/processed")
REQUIRED_COLS: List[str] = [
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


def load(name: str) -> pd.DataFrame:
    p = PROCESSED / name
    df = pd.read_csv(p)
    return df


def check_required_columns(df: pd.DataFrame) -> List[str]:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    return missing


def main() -> None:
    print("== Basic file presence ==")
    files = [
        "subway_delays.csv",
        "streetcar_delays.csv",
        "bus_delays.csv",
        "ttc_delays.csv",
    ]
    for f in files:
        p = PROCESSED / f
        print(f"{f}: {'OK' if p.exists() else 'MISSING'}")

    all_df = load("ttc_delays.csv")
    miss = check_required_columns(all_df)
    if miss:
        print("\n[FAIL] Missing required columns:", ", ".join(miss))
    else:
        print("\n[OK] All required columns present")

    print("\n== Row counts ==")
    sub = load("subway_delays.csv")
    strc = load("streetcar_delays.csv")
    bus = load("bus_delays.csv")
    print("subway:", len(sub))
    print("streetcar:", len(strc))
    print("bus    :", len(bus))
    print("all    :", len(all_df))
    print("sum(parts):", len(sub) + len(strc) + len(bus))

    print("\n== Nulls in critical columns (ttc_delays.csv) ==")
    for c in ["date", "station", "source"]:
        print(c, all_df[c].isna().sum())

    print("\n== Value range checks ==")
    for c in ["min_delay", "min_gap"]:
        s = pd.to_numeric(all_df[c], errors="coerce")
        out_of_range = ((s < 0) | (s > 720)).sum()
        print(f"{c}: out_of_range={out_of_range}")

    print("\n== Category checks ==")
    b = all_df["bound"].astype("string")
    bad_bound = b.notna() & ~b.isin(["N", "E", "S", "W"])
    print("bound invalid:", int(bad_bound.sum()))

    print("\n== Duplicate key candidates ==")
    key_cols = ["date", "time", "station", "line", "source", "vehicle"]
    avail = [c for c in key_cols if c in all_df.columns]
    dups = (
        all_df.groupby(avail, dropna=False)
        .size()
        .reset_index(name="n")
        .query("n > 1")
    )
    print("dup_groups:", len(dups))
    if len(dups) > 0:
        print(dups.head(5).to_string(index=False))


if __name__ == "__main__":
    main()

