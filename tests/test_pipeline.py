import pandas as pd

from nse_downloader.pipeline import run
from tests.conftest import FakeFetcher

ALL = ["top-gainers-losers", "upper-band-hitters", "volume-gainers-spurts", "52-week-high"]


def csvs(settings):
    return sorted(p.name for p in settings.output_dir.glob("*.csv"))


def test_all_four_csvs_are_produced(settings):
    results = run(settings, fetcher=FakeFetcher(), sleep=lambda s: None)
    assert all(r.ok for r in results)
    files = csvs(settings)
    assert len(files) == 4
    for name in ALL:
        assert any(f.startswith(name + "_") for f in files)


def test_gainers_and_losers_both_present(settings):
    run(settings, only="top-gainers-losers", fetcher=FakeFetcher(), sleep=lambda s: None)
    df = pd.read_csv(next(settings.output_dir.glob("top-gainers-losers_*.csv")))
    assert set(df["category"]) == {"gainer", "loser"}


def test_one_failure_does_not_stop_others(settings):
    results = run(settings, fetcher=FakeFetcher(fail=["upper-band-hitters"]), sleep=lambda s: None)
    by_name = {r.name: r for r in results}
    assert not by_name["upper-band-hitters"].ok
    assert sum(r.ok for r in results) == 3
    assert len(csvs(settings)) == 3


def test_invalid_response_saves_nothing_for_that_dataset(settings):
    fetcher = FakeFetcher(overrides={"52-week-high": {"unexpected": "shape"}})
    results = run(settings, fetcher=fetcher, sleep=lambda s: None)
    assert not {r.name: r for r in results}["52-week-high"].ok
    assert not any(f.startswith("52-week-high") for f in csvs(settings))


def test_single_dataset_mode(settings):
    results = run(settings, only="volume-gainers-spurts", fetcher=FakeFetcher(), sleep=lambda s: None)
    assert len(results) == 1 and len(csvs(settings)) == 1


def test_running_twice_does_not_create_extra_files(settings):
    run(settings, fetcher=FakeFetcher(), sleep=lambda s: None)
    run(settings, fetcher=FakeFetcher(), sleep=lambda s: None)
    assert len(csvs(settings)) == 4
