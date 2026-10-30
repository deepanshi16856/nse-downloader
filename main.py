import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from nse_downloader.config import ConfigError, load_settings  # noqa: E402
from nse_downloader.logging_setup import setup_logging  # noqa: E402
from nse_downloader.pipeline import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="NSE Market Data Downloader")
    parser.add_argument("--dataset", help="download only this dataset (default: all four)")
    parser.add_argument("--output-dir", help="override the output directory")
    parser.add_argument("--config", default=str(ROOT / "config" / "datasets.yaml"))
    args = parser.parse_args()

    try:
        settings = load_settings(args.config, args.output_dir)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    setup_logging(settings.log_dir)

    if args.dataset and args.dataset not in settings.datasets:
        parser.error(f"unknown dataset '{args.dataset}'. Choose from: {', '.join(settings.datasets)}")

    results = run(settings, only=args.dataset)
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
