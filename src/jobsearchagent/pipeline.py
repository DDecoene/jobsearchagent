"""Time-aware ingestion: backfill on first run, incremental after (CLAUDE.md 3, 12)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

from .db import Database
from .models import Job
from .sources import JobSource

log = logging.getLogger(__name__)


@dataclass
class IngestStats:
    mode: str = ""
    fetched: int = 0
    inserted: int = 0
    skipped_seen: int = 0
    skipped_stale: int = 0
    skipped_undated: int = 0
    per_source: dict[str, int] = field(default_factory=dict)


def ingest(db: Database, sources: list[JobSource], backfill_days: int = 14) -> IngestStats:
    backfill = not db.backfill_completed()
    stats = IngestStats(mode="backfill" if backfill else "incremental")
    cutoff = date.today() - timedelta(days=backfill_days)

    for source in sources:
        for job in source.fetch():
            stats.fetched += 1
            if backfill and not _passes_backfill_window(job, cutoff, stats):
                continue
            if db.insert_job(job):
                stats.inserted += 1
                stats.per_source[job.source] = stats.per_source.get(job.source, 0) + 1
            else:
                stats.skipped_seen += 1

    if backfill:
        db.mark_backfill_completed()
    log.info(
        "%s run: fetched=%d inserted=%d seen=%d stale=%d undated=%d",
        stats.mode, stats.fetched, stats.inserted,
        stats.skipped_seen, stats.skipped_stale, stats.skipped_undated,
    )
    return stats


def _passes_backfill_window(job: Job, cutoff: date, stats: IngestStats) -> bool:
    if job.published_date is None:
        stats.skipped_undated += 1
        return False
    if job.published_date < cutoff:
        stats.skipped_stale += 1
        return False
    return True
