"""Nightly ETL: download new files (optional), load them into SQLite, apply the automatic exclusion reasons, write a report.

Runs locally on Bharg's machine from a scheduled task (templates in dashboard/schedule/, not installed by this repo).
Credentials come from environment variables only (see docs/design/etl.md). CI never runs this against real data.
"""
import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from mindbench.exclusions import apply_exclusions
from mindbench_etl.db import connect, init_db
from mindbench_etl.download import ConfigError, download_new_files, get_config, make_session
from mindbench_etl.load import PILOT_SESSIONS, load_directory

from .config import load_config


def default_download(dest):
    """Download new session files from Google Drive into `dest` (raises ConfigError if credentials are not set)."""
    folder, key = get_config(os.environ)
    return download_new_files(make_session(key), folder, dest)


def run_nightly(db_path, raw_dir, report_path, download_fn=None, now=None, expected=None, pilot_sessions=PILOT_SESSIONS):
    """One nightly run. Download problems never stop the load; a bad file never stops the others."""
    report = {"ran_at": (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds")}
    if download_fn is None:
        report["download"] = {"status": "skipped", "message": "download not requested"}
    else:
        try:
            result = download_fn(raw_dir) or {}
            report["download"] = {"status": "ok", "downloaded": list(result.get("downloaded", []))}
        except ConfigError as e:
            report["download"] = {"status": "skipped", "message": str(e)}
        except Exception as e:  # noqa: BLE001 - reported, and the load still runs
            report["download"] = {"status": "error", "message": f"{type(e).__name__}: {e}"}

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    Path(raw_dir).mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    try:
        init_db(conn)
        loaded = load_directory(conn, raw_dir, pilot_sessions=pilot_sessions)
        report.update(loaded=loaded["loaded"], failed=[{"file": f, "message": m} for f, m in loaded["failed"]], skipped_partial=loaded["skipped_partial"])
        report["exclusions"] = apply_exclusions(conn, expected=expected)
    finally:
        conn.close()
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(json.dumps(report, indent=1) + "\n")
    return report


def main(argv=None):
    cfg = load_config(os.environ)
    p = argparse.ArgumentParser(prog="mindbench_dashboard.nightly")
    p.add_argument("--db", default=str(cfg["db"]))
    p.add_argument("--raw", default=str(cfg["raw"]))
    p.add_argument("--report", default=str(cfg["report"]))
    p.add_argument("--no-download", action="store_true", help="only load files already in the raw folder")
    p.add_argument("--pilot-sessions", type=int, default=PILOT_SESSIONS)
    args = p.parse_args(argv)
    report = run_nightly(args.db, args.raw, args.report, download_fn=None if args.no_download else default_download,
                         pilot_sessions=args.pilot_sessions)
    d = report["download"]
    print(f"download: {d['status']}" + (f" ({d['message']})" if d.get("message") else ""))
    print(f"loaded {len(report['loaded'])} file(s); {len(report['failed'])} failed; {len(report['skipped_partial'])} partial upload(s) skipped")
    for f in report["failed"]:
        print(f"  FAILED: {f['file']}: {f['message']}")
    ex = report["exclusions"]
    print(f"sessions: {ex['kept']} kept, {ex['excluded']} excluded (automatic), {len(ex['manual_kept'])} with a manual reason")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
