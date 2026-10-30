import logging
import time
from dataclasses import dataclass

import pandas as pd

from .config import DatasetConfig, Settings
from .fetcher import NSEFetcher
from .parser import parse
from .storage import save_csv
from .validator import validate

log = logging.getLogger(__name__)


@dataclass
class Result:
    name: str
    ok: bool
    rows: int = 0
    path: str = ""
    error: str = ""


def acquire(ds: DatasetConfig, fetcher) -> pd.DataFrame:
    """Fetch + parse one dataset. Datasets with variants (gainers/losers) are combined."""
    variants = ds.variants or [{"label": None, "params": ds.params}]
    frames = []
    for v in variants:
        payload = fetcher.fetch_json(ds, params={**ds.params, **v["params"]})
        df = parse(payload, ds)
        if v["label"]:
            df[ds.label_column] = v["label"]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def run(settings: Settings, only: str | None = None, fetcher=None, sleep=time.sleep) -> list:
    fetcher = fetcher or NSEFetcher(settings)
    names = [only] if only else list(settings.datasets)
    results = []

    for i, name in enumerate(names):
        ds = settings.datasets[name]
        log.info("=== Starting dataset: %s ===", name)
        try:
            df = validate(acquire(ds, fetcher), ds)
            path = save_csv(df, name, settings.output_dir)
            results.append(Result(name, True, len(df), str(path)))
            log.info("[%s] SUCCESS: %d records", name, len(df))
        except Exception as exc:  # one dataset failing must not stop the others
            log.error("[%s] FAILED: %s", name, exc)
            results.append(Result(name, False, error=str(exc)))
        if i < len(names) - 1:
            sleep(settings.request_delay)

    ok = sum(r.ok for r in results)
    log.info("SUMMARY: %d/%d datasets succeeded", ok, len(results))
    for r in results:
        log.info("  %-24s %-4s %s", r.name, "OK" if r.ok else "FAIL",
                 f"{r.rows} rows -> {r.path}" if r.ok else r.error)
    return results
