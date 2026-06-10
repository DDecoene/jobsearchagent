"""SQLite storage: seen-fingerprint dedup, job records, and run-mode state."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from .models import Job

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    fingerprint     TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    location        TEXT NOT NULL,
    description     TEXT NOT NULL,
    url             TEXT NOT NULL,
    source          TEXT NOT NULL,
    source_id       TEXT NOT NULL DEFAULT '',
    published_date  TEXT,
    first_seen_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

BACKFILL_KEY = "backfill_completed_at"


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- run mode -----------------------------------------------------

    def backfill_completed(self) -> bool:
        row = self.conn.execute(
            "SELECT value FROM meta WHERE key = ?", (BACKFILL_KEY,)
        ).fetchone()
        return row is not None

    def mark_backfill_completed(self) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (BACKFILL_KEY, datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    # --- jobs ---------------------------------------------------------

    def is_seen(self, fingerprint: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM jobs WHERE fingerprint = ?", (fingerprint,)
        ).fetchone()
        return row is not None

    def insert_job(self, job: Job) -> bool:
        """Insert a job; returns False if its fingerprint was already seen."""
        cur = self.conn.execute(
            """
            INSERT OR IGNORE INTO jobs
                (fingerprint, title, company, location, description, url,
                 source, source_id, published_date, first_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.fingerprint,
                job.title,
                job.company,
                job.location,
                job.description,
                job.url,
                job.source,
                job.source_id,
                job.published_date.isoformat() if job.published_date else None,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def list_jobs(self, limit: int = 50) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT title, company, location, url, source, published_date, first_seen_at
            FROM jobs
            ORDER BY COALESCE(published_date, first_seen_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def count_jobs(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
