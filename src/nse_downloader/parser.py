import logging

import pandas as pd

from .config import DatasetConfig

log = logging.getLogger(__name__)


class ParseError(Exception):
    """Payload did not have the expected structure."""


def parse(payload, ds: DatasetConfig) -> pd.DataFrame:
    node = payload
    for key in ds.records_path:
        if not isinstance(node, dict) or key not in node:
            raise ParseError(f"[{ds.name}] expected path {ds.records_path}, missing '{key}'")
        node = node[key]
    if not isinstance(node, list):
        raise ParseError(f"[{ds.name}] expected a list of records, got {type(node).__name__}")
    df = pd.json_normalize(node)
    log.info("[%s] parsed %d raw records, %d columns", ds.name, len(df), len(df.columns))
    return df
