from datetime import date, timedelta

from jobsearchagent.db import Database
from jobsearchagent.models import Job
from jobsearchagent.pipeline import ingest


class FakeSource:
    name = "fake"

    def __init__(self, jobs):
        self.jobs = jobs

    def fetch(self):
        return iter(self.jobs)


def _job(title, published=None):
    return Job(title, "Acme", "Gent", "desc", "url", "fake", published_date=published)


def _db(tmp_path):
    return Database(tmp_path / "test.sqlite3")


def test_backfill_keeps_only_recent_dated_jobs(tmp_path):
    today = date.today()
    jobs = [
        _job("fresh", today - timedelta(days=3)),
        _job("stale", today - timedelta(days=30)),
        _job("undated", None),
    ]
    with _db(tmp_path) as db:
        stats = ingest(db, [FakeSource(jobs)], backfill_days=14)
        assert stats.mode == "backfill"
        assert stats.inserted == 1
        assert stats.skipped_stale == 1
        assert stats.skipped_undated == 1
        assert db.backfill_completed()


def test_incremental_accepts_undated_but_skips_seen(tmp_path):
    today = date.today()
    with _db(tmp_path) as db:
        ingest(db, [FakeSource([_job("first", today)])], backfill_days=14)

        jobs = [_job("first", today), _job("undated new", None)]
        stats = ingest(db, [FakeSource(jobs)], backfill_days=14)
        assert stats.mode == "incremental"
        assert stats.inserted == 1
        assert stats.skipped_seen == 1


def test_duplicate_across_sources_inserted_once(tmp_path):
    today = date.today()
    a = Job("ERP Beheerder", "Acme NV", "9000 Gent", "x", "u", "vdab", published_date=today)
    b = Job("ERP Beheerder", "Acme", "Gent", "y", "u2", "indeed", published_date=today)
    with _db(tmp_path) as db:
        stats = ingest(db, [FakeSource([a]), FakeSource([b])], backfill_days=14)
        assert stats.inserted == 1
        assert db.count_jobs() == 1
