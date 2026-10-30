import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


def trading_date() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def save_csv(df: pd.DataFrame, name: str, output_dir, date: str | None = None) -> Path:
    """One file per dataset per day. Re-running the same day overwrites it
    (atomically), so there are never confusing duplicate files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    final = output_dir / f"{name}_{date or trading_date()}.csv"
    tmp = final.with_suffix(".csv.tmp")
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, final)
    log.info("[%s] saved %d rows -> %s", name, len(df), final)
    return final
