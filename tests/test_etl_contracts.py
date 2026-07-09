import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from etl_scripts.etl import STANDARD_COLS, process_mode
from etl_scripts.validate import check_required_columns


class EtlContractTests(unittest.TestCase):
    def _fixture_dir(self, root: Path) -> Path:
        source_dir = root / "raw_subway"
        source_dir.mkdir()
        pd.DataFrame(
            {
                "Report Date": ["2025-01-03", None],
                "Time": [930, "10:00"],
                "Location": [" Union Station ", "Dropped Row"],
                "Line": [" 1 ", "1"],
                "Direction": ["south", "N"],
                "Delay Code": ["muis", "MUIS"],
                "Mins Delay": [5, 99],
                "Mins Gap": [7, 100],
                "Vehicle": [5010, 5011],
            }
        ).to_csv(source_dir / "z_delays.csv", index=False)
        pd.DataFrame(
            {
                "Date": ["2025-01-02"],
                "Time": [0.5],
                "Station": ["Bloor Station"],
                "Route": ["2"],
                "Bound": ["W"],
                "Code": ["SUDP"],
                "Min Delay": [-1],
                "Min Gap": [4],
                "Vehicle": [5210],
            }
        ).to_csv(source_dir / "a_delays.csv", index=False)
        return source_dir

    def _run_fixture(self, source_dir: Path) -> pd.DataFrame:
        code_dictionary = pd.DataFrame(
            {
                "code": ["MUIS", "SUDP"],
                "description": ["Injured customer", "Disorderly patron"],
            }
        )
        return process_mode(source_dir, "subway", code_dictionary).reset_index(drop=True)

    def test_fixture_matches_the_reviewed_snapshot(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            actual = self._run_fixture(self._fixture_dir(Path(temp_dir)))

        snapshot_frame = actual.copy()
        snapshot_frame["raw_file"] = snapshot_frame["raw_file"].map(
            lambda value: f"raw_subway/{Path(value).name}"
        )
        snapshot = snapshot_frame.to_csv(index=False, lineterminator="\n")
        self.assertEqual(
            snapshot,
            "date,time,day,station,line,bound,code,min_delay,min_gap,vehicle,source,raw_file,description\n"
            "2025-01-02,12:00,,Bloor Station,2,W,SUDP,,4.0,5210,subway,"
            "raw_subway/a_delays.csv,Disorderly patron\n"
            "2025-01-03,09:30,,Union Station,1,S,MUIS,5.0,7.0,5010,subway,"
            "raw_subway/z_delays.csv,Injured customer\n",
        )

    def test_same_inputs_produce_the_same_ordered_rows(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            source_dir = self._fixture_dir(Path(temp_dir))
            first = self._run_fixture(source_dir)
            second = self._run_fixture(source_dir)

        pd.testing.assert_frame_equal(first, second, check_dtype=True)

    def test_output_obeys_the_csv_data_contract(self) -> None:
        with TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            actual = self._run_fixture(self._fixture_dir(Path(temp_dir)))

        self.assertEqual(list(actual.columns), [*STANDARD_COLS, "description"])
        self.assertEqual(check_required_columns(actual), [])
        self.assertEqual(set(actual["source"]), {"subway"})
        self.assertTrue(actual["bound"].dropna().isin(["N", "E", "S", "W"]).all())
        self.assertTrue((actual["min_delay"].dropna() >= 0).all())
        self.assertTrue((actual["min_gap"].dropna() >= 0).all())
        self.assertFalse(actual["raw_file"].str.startswith("/").any())


if __name__ == "__main__":
    unittest.main()
