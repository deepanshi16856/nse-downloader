import pytest
import requests

from nse_downloader.fetcher import BlockedError, FetchError, InvalidResponseError, NSEFetcher

API = "https://www.nseindia.com/api/live-analysis-volume-gainers"
HOME = "https://www.nseindia.com"


def make(settings):
    waits = []
    return NSEFetcher(settings, sleep=waits.append), waits


def test_successful_download(settings, requests_mock):
    requests_mock.get(HOME, text="ok")
    requests_mock.get(API, json={"data": [{"symbol": "A"}]})
    fetcher, _ = make(settings)
    assert fetcher.fetch_json(settings.datasets["volume-gainers-spurts"]) == {"data": [{"symbol": "A"}]}


def test_retries_on_server_error_then_succeeds(settings, requests_mock):
    requests_mock.get(HOME, text="ok")
    requests_mock.get(API, [{"status_code": 500}, {"status_code": 503}, {"json": {"data": [1]}}])
    fetcher, waits = make(settings)
    assert fetcher.fetch_json(settings.datasets["volume-gainers-spurts"]) == {"data": [1]}
    assert len(waits) == 2  # backed off twice


def test_gives_up_after_max_retries(settings, requests_mock):
    requests_mock.get(HOME, text="ok")
    requests_mock.get(API, status_code=500)
    fetcher, _ = make(settings)
    with pytest.raises(FetchError, match="failed after 3 attempts"):
        fetcher.fetch_json(settings.datasets["volume-gainers-spurts"])


def test_timeout_is_retried_then_fails(settings, requests_mock):
    requests_mock.get(HOME, text="ok")
    requests_mock.get(API, exc=requests.exceptions.ConnectTimeout)
    fetcher, _ = make(settings)
    with pytest.raises(FetchError):
        fetcher.fetch_json(settings.datasets["volume-gainers-spurts"])
    assert requests_mock.call_count == 1 + 3  # warm-up + 3 attempts


def test_403_is_not_retried_or_bypassed(settings, requests_mock):
    requests_mock.get(HOME, text="ok")
    requests_mock.get(API, status_code=403)
    fetcher, waits = make(settings)
    with pytest.raises(BlockedError):
        fetcher.fetch_json(settings.datasets["volume-gainers-spurts"])
    assert waits == []


def test_404_fails_immediately(settings, requests_mock):
    requests_mock.get(HOME, text="ok")
    requests_mock.get(API, status_code=404)
    fetcher, waits = make(settings)
    with pytest.raises(FetchError):
        fetcher.fetch_json(settings.datasets["volume-gainers-spurts"])
    assert waits == []


def test_invalid_json(settings, requests_mock):
    requests_mock.get(HOME, text="ok")
    requests_mock.get(API, text="<html>not json</html>")
    fetcher, _ = make(settings)
    with pytest.raises(InvalidResponseError, match="not valid JSON"):
        fetcher.fetch_json(settings.datasets["volume-gainers-spurts"])


def test_empty_json(settings, requests_mock):
    requests_mock.get(HOME, text="ok")
    requests_mock.get(API, json={})
    fetcher, _ = make(settings)
    with pytest.raises(InvalidResponseError, match="empty"):
        fetcher.fetch_json(settings.datasets["volume-gainers-spurts"])
