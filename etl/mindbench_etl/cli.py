"""Command line: python -m mindbench_etl {download,load,init-db}. Data stays in the gitignored data/ folder."""
import argparse
import os
import sys

from .db import connect, init_db
from .download import ConfigError, download_new_files, get_config, make_session
from .load import PILOT_SESSIONS, load_directory


def _print_report(title, report):
    print(title)
    for key, items in report.items():
        for item in items:
            print(f"  {key}: {item[0] + ': ' + item[1] if isinstance(item, tuple) else item}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="mindbench_etl")
    sub = p.add_subparsers(dest="command", required=True)
    d = sub.add_parser("download", help="download new session files from Google Drive (needs credentials in the environment)")
    d.add_argument("--dest", default="data/raw")
    ld = sub.add_parser("load", help="validate and load downloaded files into SQLite (idempotent)")
    ld.add_argument("--raw", default="data/raw")
    ld.add_argument("--db", default="data/mindbench.sqlite")
    ld.add_argument("--pilot-sessions", type=int, default=PILOT_SESSIONS, help="sessions 1..N are flagged is_pilot (smoke-test runs); default 2")
    i = sub.add_parser("init-db", help="create an empty database")
    i.add_argument("--db", default="data/mindbench.sqlite")
    args = p.parse_args(argv)

    if args.command == "download":
        try:
            folder, key = get_config(os.environ)
        except ConfigError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2
        report = download_new_files(make_session(key), folder, args.dest)
        _print_report(f"Downloaded {len(report['downloaded'])} new file(s)", report)
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(args.db)), exist_ok=True)
    conn = connect(args.db)
    init_db(conn)
    if args.command == "init-db":
        print(f"Database ready: {args.db}")
        return 0
    report = load_directory(conn, args.raw, pilot_sessions=args.pilot_sessions)
    print(f"Loaded {len(report['loaded'])} file(s), {len(report['failed'])} failed, {len(report['skipped_partial'])} partial skipped")
    for name in report["loaded"]:
        print(f"  loaded: {name}")
    for name in report["skipped_partial"]:
        print(f"  skipped (partial upload): {name}")
    for name, message in report["failed"]:
        print(f"  FAILED: {name}: {message}")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
