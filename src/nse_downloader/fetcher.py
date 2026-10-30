import logging
import time

import requests

from .config import DatasetConfig, Settings

log = logging.getLogger(__name__)


class FetchError(Exception):
    """Acquisition failed."""


class BlockedError(FetchError):
    """Server refused access (HTTP 403). We do NOT try to bypass this."""


class InvalidResponseError(FetchError):
    """Response was empty or not valid JSON."""


class _Retryable(Exception):
    """Internal: transient failure worth retrying."""


class NSEFetcher:
    def __init__(self, settings: Settings, sleep=time.sleep):
        self.s = settings
        self._sleep = sleep  # injectable so tests don't really wait
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": settings.base_url + "/",
        })
        self._warmed = False

    def _check_status(self, resp, label: str) -> None:
        if resp.status_code == 403:
            raise BlockedError(f"[{label}] HTTP 403 - access refused; not retrying or bypassing")
        if resp.status_code == 429 or resp.status_code >= 500:
            raise _Retryable(f"HTTP {resp.status_code}")
        if not resp.ok:
            raise FetchError(f"[{label}] HTTP {resp.status_code}")

    def _warm_up(self, label: str) -> None:
        """Open the homepage once, like a normal browser visit, to get session cookies."""
        if self._warmed:
            return
        log.info("Warming up session: GET %s", self.s.base_url)
        resp = self.session.get(self.s.base_url, timeout=self.s.timeout)
        self._check_status(resp, label)
        self._warmed = True

    def fetch_json(self, ds: DatasetConfig, params: dict | None = None):
        params = ds.params if params is None else params
        for attempt in range(1, self.s.max_retries + 1):
            log.info("[%s] attempt %d/%d: GET %s params=%s",
                     ds.name, attempt, self.s.max_retries, ds.api_url, params)
            try:
                self._warm_up(ds.name)
                resp = self.session.get(ds.api_url, params=params, timeout=self.s.timeout)
                self._check_status(resp, ds.name)

                try:
                    payload = resp.json()
                except ValueError as exc:
                    raise InvalidResponseError(f"[{ds.name}] response is not valid JSON") from exc
                if not payload:
                    raise InvalidResponseError(f"[{ds.name}] empty JSON payload")

                log.info("[%s] fetched OK (%d bytes)", ds.name, len(resp.content))
                return payload

            except (requests.Timeout, requests.ConnectionError, _Retryable) as exc:
                if attempt == self.s.max_retries:
                    raise FetchError(f"[{ds.name}] failed after {attempt} attempts: {exc}") from exc
                wait = self.s.backoff_factor * 2 ** (attempt - 1)
                log.warning("[%s] transient error (%s); retrying in %.1fs", ds.name, exc, wait)
                self._sleep(wait)
            except requests.RequestException as exc:
                raise FetchError(f"[{ds.name}] request error: {exc}") from exc
