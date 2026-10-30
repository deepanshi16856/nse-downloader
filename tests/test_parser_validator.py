import pandas as pd
import pytest

from nse_downloader.parser import ParseError, parse
from nse_downloader.validator import ValidationError, validate


def test_parse_follows_records_path(settings):
    ds = settings.datasets["upper-band-hitters"]
    payload = {"upper": {"AllSec": {"data": [{"symbol": "A", "ltp": "1", "pChange": "2"}]}}}
    assert list(parse(payload, ds)["symbol"]) == ["A"]


def test_parse_wrong_structure(settings):
    with pytest.raises(ParseError, match="missing"):
        parse({"unexpected": 1}, settings.datasets["volume-gainers-spurts"])


def test_parse_not_a_list(settings):
    with pytest.raises(ParseError, match="list"):
        parse({"data": {"a": 1}}, settings.datasets["volume-gainers-spurts"])


def test_empty_dataframe_rejected(settings):
    with pytest.raises(ValidationError, match="empty"):
        validate(pd.DataFrame(), settings.datasets["volume-gainers-spurts"])


def test_missing_columns_rejected(settings):
    df = pd.DataFrame([{"symbol": "A"}])
    with pytest.raises(ValidationError, match="missing expected columns"):
        validate(df, settings.datasets["volume-gainers-spurts"])


def test_duplicates_removed(settings):
    df = pd.DataFrame([
        {"symbol": "A", "volume": 1, "ltp": 1.0},
        {"symbol": "A", "volume": 1, "ltp": 1.0},
        {"symbol": "B", "volume": 2, "ltp": 2.0}])
    out = validate(df, settings.datasets["volume-gainers-spurts"])
    assert list(out["symbol"]) == ["A", "B"]


def test_string_numbers_converted(settings):
    df = pd.DataFrame([{"symbol": "A", "ltp": "285.9", "change": "47.2", "pChange": "  19.77", "priceBand": "20"}])
    out = validate(df, settings.datasets["upper-band-hitters"])
    assert out["pChange"].iloc[0] == 19.77
    assert pd.api.types.is_numeric_dtype(out["ltp"])


def test_all_invalid_numbers_rejected(settings):
    df = pd.DataFrame([{"symbol": "A", "volume": "abc", "ltp": 1.0}])
    with pytest.raises(ValidationError):
        validate(df, settings.datasets["volume-gainers-spurts"])
