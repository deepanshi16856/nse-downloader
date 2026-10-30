from dataclasses import replace
from pathlib import Path

import pytest

from nse_downloader.config import load_settings

CONFIG = Path(__file__).resolve().parent.parent / "config" / "datasets.yaml"


@pytest.fixture
def settings(tmp_path):
    s = load_settings(str(CONFIG), output_dir=str(tmp_path / "out"))
    return replace(s, max_retries=3, backoff_factor=0, request_delay=0, log_dir=tmp_path / "logs")


PAYLOADS = {
    "top-gainers-losers:gainers": {"NIFTY": {"data": [
        {"symbol": "TRENT", "ltp": 3040.2, "net_price": 6.24},
        {"symbol": "TCS", "ltp": 4000.0, "net_price": 2.1}]}},
    "top-gainers-losers:losers": {"NIFTY": {"data": [
        {"symbol": "INFY", "ltp": 1500.0, "net_price": -3.2}]}},
    "upper-band-hitters": {"upper": {"AllSec": {"data": [
        {"symbol": "BOROLTD", "ltp": "285.9", "change": "47.2", "pChange": "  19.77", "priceBand": "20"},
        {"symbol": "MARSONS", "ltp": "148.02", "change": "23.97", "pChange": "  19.32", "priceBand": "20"}]}}},
    "volume-gainers-spurts": {"data": [
        {"symbol": "BOROLTD", "volume": 15570899, "ltp": 285.95, "pChange": 19.79}]},
    "52-week-high": {"data": [
        {"symbol": "21STCENMGM", "ltp": 57.82, "new52WHL": 57.82, "prev52WHL": 55.07, "pChange": 4.99}]},
}


class FakeFetcher:
    """Stands in for NSEFetcher so pipeline tests need no network."""

    def __init__(self, fail=(), overrides=None):
        self.fail = set(fail)
        self.overrides = overrides or {}

    def fetch_json(self, ds, params=None):
        if ds.name in self.fail:
            raise RuntimeError("simulated network failure")
        if ds.name in self.overrides:
            return self.overrides[ds.name]
        if ds.name == "top-gainers-losers":
            key = "losers" if (params or {}).get("index") == "losers" else "gainers"
            return PAYLOADS[f"{ds.name}:{key}"]
        return PAYLOADS[ds.name]
