import unittest
from pathlib import Path

import pandas as pd

from etl_scripts.etl import STANDARD_COLS, _gather_files, _normalize_common
from etl_scripts.validate import check_required_columns


class NormalizeCommonTests(unittest.TestCase):
    def test_normalizes_source_columns_and_rejects_invalid_values(self) -> None:
        raw = pd.DataFrame(
            {
                "Report Date": ["2025-01-02", "2025-01-03", "2025-01-04"],
                "Time": [0.5, "930", "25:00"],
                "Day": [" Thursday ", "Friday", "Saturday"],
                "Location": [" Bloor Station ", "Union Station", "Bay Station"],
                "Route": [" 2 ", "1", "2"],
                "Direction": ["north", "W", "unknown"],
                "Delay Code": ["  muis  ", "SUDP", None],
                "Mins Delay": [5, -1, "12"],
                "Mins Gap": [10, 4, "invalid"],
                "Vehicle": ["5010", "not-a-number", 5210],
            }
        )

        actual = _normalize_common(raw, "subway", Path("data/raw/sample.csv"))

        self.assertEqual(list(actual.columns), STANDARD_COLS)
        self.assertEqual(actual["source"].tolist(), ["subway"] * 3)
        self.assertEqual(actual["time"].tolist()[:2], ["12:00", "09:30"])
        self.assertTrue(pd.isna(actual.loc[2, "time"]))
        self.assertEqual(actual["bound"].tolist()[:2], ["N", "W"])
        self.assertTrue(pd.isna(actual.loc[2, "bound"]))
        self.assertEqual(actual.loc[0, "station"], "Bloor Station")
        self.assertEqual(actual.loc[0, "code"], "MUIS")
        self.assertTrue(pd.isna(actual.loc[1, "min_delay"]))
        self.assertTrue(pd.isna(actual.loc[2, "min_gap"]))
        self.assertEqual(check_required_columns(actual), [])

    def test_gather_files_excludes_metadata_and_orders_inputs(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in [
                "z_delays.xlsx",
                "a_delays.csv",
                "Code Descriptions.csv",
                "README.csv",
                "notes.txt",
            ]:
                (root / name).touch()

            self.assertEqual(
                [path.name for path in _gather_files(root)],
                ["a_delays.csv", "z_delays.xlsx"],
            )


if __name__ == "__main__":
    unittest.main()
