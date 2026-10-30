import pandas as pd

from nse_downloader.storage import save_csv


def test_filename_contains_dataset_and_date(tmp_path):
    path = save_csv(pd.DataFrame({"a": [1]}), "52-week-high", tmp_path, date="2026-10-30")
    assert path.name == "52-week-high_2026-10-30.csv"
    assert path.exists()


def test_rerun_same_day_overwrites_not_duplicates(tmp_path):
    save_csv(pd.DataFrame({"a": [1]}), "x", tmp_path, date="2026-10-30")
    save_csv(pd.DataFrame({"a": [1, 2, 3]}), "x", tmp_path, date="2026-10-30")
    files = list(tmp_path.glob("*.csv"))
    assert len(files) == 1
    assert len(pd.read_csv(files[0])) == 3
    assert not list(tmp_path.glob("*.tmp"))  # no leftover temp files
