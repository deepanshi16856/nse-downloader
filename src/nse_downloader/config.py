from dataclasses import dataclass, field
from pathlib import Path

import yaml


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    page_url: str
    api_url: str
    records_path: list
    required_columns: list
    params: dict = field(default_factory=dict)
    variants: list = field(default_factory=list)
    label_column: str = "category"
    numeric_columns: list = field(default_factory=list)
    dedupe_key: list = field(default_factory=list)


@dataclass(frozen=True)
class Settings:
    base_url: str
    timeout: int
    max_retries: int
    backoff_factor: float
    request_delay: float
    output_dir: Path
    log_dir: Path
    user_agent: str
    datasets: dict  # name -> DatasetConfig


def load_settings(path="config/datasets.yaml", output_dir=None) -> Settings:
    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        s = raw["settings"]
        datasets = {}
        for name, d in raw["datasets"].items():
            datasets[name] = DatasetConfig(
                name=name,
                page_url=d["page_url"],
                api_url=d["api_url"],
                records_path=d["records_path"],
                required_columns=d["required_columns"],
                params=d.get("params") or {},
                variants=d.get("variants") or [],
                label_column=d.get("label_column", "category"),
                numeric_columns=d.get("numeric_columns") or [],
                dedupe_key=d.get("dedupe_key") or [],
            )
        return Settings(
            base_url=s["base_url"],
            timeout=s["timeout_seconds"],
            max_retries=s["max_retries"],
            backoff_factor=s["backoff_factor"],
            request_delay=s["delay_between_requests"],
            output_dir=Path(output_dir or s["output_dir"]),
            log_dir=Path(s["log_dir"]),
            user_agent=s["user_agent"],
            datasets=datasets,
        )
    except (OSError, KeyError, TypeError, AttributeError, yaml.YAMLError) as exc:
        raise ConfigError(f"Invalid or unreadable config '{path}': {exc!r}") from exc
