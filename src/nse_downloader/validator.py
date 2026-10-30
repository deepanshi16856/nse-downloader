import logging

import pandas as pd

from .config import DatasetConfig

log = logging.getLogger(__name__)


class ValidationError(Exception):
    """Data failed a quality check and must not be saved."""


def validate(df: pd.DataFrame, ds: DatasetConfig) -> pd.DataFrame:
    if df is None or df.empty:
        raise ValidationError(f"[{ds.name}] dataset is empty")
    df = df.copy()

    missing = [c for c in ds.required_columns if c not in df.columns]
    if missing:
        raise ValidationError(f"[{ds.name}] missing expected columns: {missing}")

    # NSE sometimes sends numbers as strings like "  19.77" -> convert to real numbers
    for col in ds.numeric_columns:
        if col in df.columns:
            cleaned = df[col].astype(str).str.strip().str.replace(",", "", regex=False)
            df[col] = pd.to_numeric(cleaned, errors="coerce")
            bad = int(df[col].isna().sum())
            if bad == len(df):
                raise ValidationError(f"[{ds.name}] numeric column '{col}' has no valid numbers")
            if bad:
                log.warning("[%s] %d non-numeric values in '%s' set to NaN", ds.name, bad, col)

    for col in ds.required_columns:
        if df[col].isna().all():
            raise ValidationError(f"[{ds.name}] required column '{col}' is entirely empty")

    if ds.dedupe_key:
        before = len(df)
        df = df.dropna(subset=ds.dedupe_key)
        df = df.drop_duplicates(subset=ds.dedupe_key, keep="first")
        removed = before - len(df)
        if removed:
            log.warning("[%s] removed %d duplicate/invalid-key rows (key=%s)",
                        ds.name, removed, ds.dedupe_key)

    if df.empty:
        raise ValidationError(f"[{ds.name}] no valid rows after cleaning")
    return df.reset_index(drop=True)
