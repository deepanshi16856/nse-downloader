# NSE Market Data Downloader

A small, reliable pipeline that downloads four NSE India market-data datasets and saves each as a dated CSV.

| Dataset | CLI name |
|---|---|
| Top Gainers / Losers | `top-gainers-losers` |
| Upper Band Hitters | `upper-band-hitters` |
| Volume Gainers / Spurts | `volume-gainers-spurts` |
| 52-Week High (Equity) | `52-week-high` |

## Installation
```bash
python -m venv venv
venv\Scripts\activate        # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```
Requires Python 3.10+.

## Execution
```bash
python main.py                                  # all four datasets
python main.py --dataset top-gainers-losers     # one dataset
python main.py --output-dir D:\data\nse         # custom output directory
```
Exit code: `0` all succeeded, `1` at least one dataset failed, `2` configuration error.

**Scheduling:** Windows Task Scheduler (action: `python C:\path\main.py`, weekdays after 16:00 IST) or cron:
`30 16 * * 1-5 cd /path/nse-downloader && venv/bin/python main.py`

**Docker:** `docker build -t nse-downloader .` then `docker run --rm -v ./output:/app/output nse-downloader`

## Architecture
| Module | Responsibility |
|---|---|
| `config/datasets.yaml` | URLs, response paths, expected columns, retry settings (no hard-coded URLs in code) |
| `fetcher.py` | Data acquisition: session, timeouts, retries, error classification |
| `parser.py` | JSON payload -> DataFrame |
| `validator.py` | Column checks, type cleaning, empty checks, duplicates |
| `storage.py` | Atomic, idempotent CSV writing |
| `pipeline.py` | Orchestration with per-dataset failure isolation |
| `main.py` | CLI entry point |

## Data acquisition
The NSE web pages load their tables from JSON endpoints that the site itself calls. The app calls these endpoints with a normal HTTP session (browser-style headers, homepage visited first for cookies) and a polite delay between requests. Top Gainers/Losers is fetched twice (gainers and losers) and combined with a `category` column.

## File storage
`output/<dataset>_<YYYY-MM-DD>.csv`, dated in IST. Files are written to a temp file and atomically renamed.

## Error handling
- Timeouts, connection errors, HTTP 429 and 5xx: retried with exponential backoff (2s, 4s, 8s; configurable).
- HTTP 403: logged and failed; **never retried or bypassed**.
- Other HTTP errors, empty or non-JSON responses, unexpected structure: the dataset fails with a clear message.
- A failing dataset never stops the others; a final summary is logged.
- Logs: console plus rotating `logs/downloader.log` with timestamps, attempts, record counts and errors.

## Validation
Non-empty, required columns present, numeric strings converted to numbers (e.g. `"  19.77"`), required columns not entirely empty, duplicates removed on a configurable key. Invalid data is never saved.

## Duplicate handling
One file per dataset per day. Re-running on the same day overwrites that file, so there are no `_1`/`_2` copies. Rows are de-duplicated by key before saving.

## Testing
```bash
python -m pytest -v
```
Covers successful downloads, retries/backoff, timeouts, 403/404/5xx, invalid and empty responses, validation, file creation (all four CSVs), and duplicate handling. HTTP is mocked, so tests run offline.

## Limitations and assumptions
- Uses undocumented JSON endpoints behind NSE's pages; they may change without notice. Update `config/datasets.yaml` if so.
- Uses only normal, permitted access. If NSE refuses automated access (HTTP 403), the app reports it and does not attempt to evade protections. Users must respect NSE's terms of use.
- Data is a point-in-time snapshot; run after market close for end-of-day values.
- NSE's raw field names are kept as-is (e.g. `comapnyName` in the 52-week data is NSE's own spelling).
- Possible extensions: SQLite storage, email/Slack failure alerts, historical archive.
