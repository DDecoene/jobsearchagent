"""CLI entry point: `jobsearch ingest` and `jobsearch list`."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .db import Database
from .pipeline import ingest
from .sources.vdab import VdabSource


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jobsearch", description="Career discovery agent")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Fetch new jobs from all sources")
    p_ingest.add_argument(
        "--dump-raw",
        type=Path,
        metavar="FILE",
        help="Write the raw VDAB API response to FILE (for adjusting the field mapping)",
    )

    p_list = sub.add_parser("list", help="Show stored jobs, newest first")
    p_list.add_argument("-n", "--limit", type=int, default=25)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config = Config.from_env()
    with Database(config.db_path) as db:
        if args.command == "ingest":
            return _cmd_ingest(config, db, args)
        if args.command == "list":
            return _cmd_list(db, args)
    return 0


def _cmd_ingest(config: Config, db: Database, args: argparse.Namespace) -> int:
    try:
        sources = [VdabSource(config, dump_raw=args.dump_raw)]
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    stats = ingest(db, sources, backfill_days=config.backfill_days)
    print(
        f"[{stats.mode}] fetched {stats.fetched}, inserted {stats.inserted} new "
        f"(already seen: {stats.skipped_seen}, outside window: {stats.skipped_stale}, "
        f"no date: {stats.skipped_undated}). Total stored: {db.count_jobs()}"
    )
    return 0


def _cmd_list(db: Database, args: argparse.Namespace) -> int:
    rows = db.list_jobs(limit=args.limit)
    if not rows:
        print("No jobs stored yet — run `jobsearch ingest` first.")
        return 0
    for row in rows:
        pub = row["published_date"] or "????-??-??"
        print(f"{pub}  {row['title']} — {row['company']} ({row['location']})")
        if row["url"]:
            print(f"            {row['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
