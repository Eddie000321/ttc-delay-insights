import sys
from pathlib import Path

import pandas as pd


def peek(path: Path) -> None:
    try:
        df = pd.read_excel(path, nrows=5)
        print(f"FILE: {path}")
        print("COLUMNS:", list(df.columns))
        if len(df.index):
            print("ROW1:", df.iloc[0].to_dict())
            # Try to detect a time-like column and show value types
            cols = {c.lower(): c for c in df.columns}
            for key in ["time", "report time"]:
                if key in cols:
                    col = cols[key]
                    vals = df[col].head(5).tolist()
                    types = [type(v).__name__ for v in vals]
                    print(f"TIME SAMPLE ({col}):", vals)
                    print(f"TIME TYPES ({col}):", types)
                    break
    except Exception as e:
        print(f"FILE: {path} ERR: {e}")


def main(argv):
    if len(argv) < 2:
        print("Usage: python scripts/peek_columns.py <file1> [file2 ...]")
        return 1
    for arg in argv[1:]:
        peek(Path(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
