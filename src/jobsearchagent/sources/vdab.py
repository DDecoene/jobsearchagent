"""VDAB Open Services vacancy source.

The exact request/response contract sits behind a registered account on
https://developer.vdab.be/openservices/ (Vacatures API), so the endpoint
path, auth header, and search parameters are all configurable via .env.

The response mapping in `parse_vacancy` is written defensively against
the field names commonly used in VDAB payloads (Dutch keys). On the first
real run, use `jobsearch ingest --dump-raw raw.json` to capture an actual
response and adjust FIELD_MAP if needed.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Iterator

import httpx

from ..config import Config
from ..models import Job

log = logging.getLogger(__name__)

# Candidate key names per canonical field, tried in order.
FIELD_MAP: dict[str, list[str]] = {
    "title": ["functienaam", "titel", "title", "naam"],
    "company": ["bedrijfsnaam", "werkgever", "bedrijf", "company"],
    "location": ["gemeente", "plaats", "locatie", "location", "tewerkstellingsplaats"],
    "description": ["omschrijving", "beschrijving", "functieomschrijving", "description"],
    "url": ["url", "vacatureUrl", "link"],
    "published_date": ["publicatieDatum", "publicatiedatum", "creatieDatum", "publishedDate"],
    "source_id": ["vacatureId", "id", "vacatureNummer"],
}

# Keys under which the vacancy list may sit in the response envelope.
LIST_KEYS = ["vacatures", "items", "results", "content"]


def _pick(record: dict[str, Any], field: str) -> Any:
    for key in FIELD_MAP[field]:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):  # epoch millis
        return datetime.fromtimestamp(value / 1000).date()
    text = str(value)
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        log.warning("Unparseable published date: %r", value)
        return None


def parse_vacancy(record: dict[str, Any]) -> Job | None:
    title = _pick(record, "title")
    company = _pick(record, "company")
    if not title or not company:
        log.warning("Skipping vacancy without title/company: keys=%s", sorted(record))
        return None
    return Job(
        title=str(title),
        company=str(company),
        location=str(_pick(record, "location") or ""),
        description=str(_pick(record, "description") or ""),
        url=str(_pick(record, "url") or ""),
        source="vdab",
        published_date=_parse_date(_pick(record, "published_date")),
        source_id=str(_pick(record, "source_id") or ""),
    )


def extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in LIST_KEYS:
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError(
        f"Could not find vacancy list in response (top-level keys: "
        f"{sorted(payload) if isinstance(payload, dict) else type(payload)}). "
        "Dump the raw response with --dump-raw and adjust LIST_KEYS/FIELD_MAP."
    )


class VdabSource:
    name = "vdab"

    def __init__(self, config: Config, dump_raw: Path | None = None):
        if not config.vdab_api_key:
            raise RuntimeError(
                "VDAB_API_KEY is not set. Register at "
                "https://developer.vdab.be/openservices/, subscribe to the "
                "Vacatures API, and put the key in .env (see .env.example)."
            )
        self.config = config
        self.dump_raw = dump_raw

    def _headers(self) -> dict[str, str]:
        c = self.config
        return {c.vdab_auth_header: f"{c.vdab_auth_prefix}{c.vdab_api_key}"}

    def fetch(self) -> Iterator[Job]:
        terms = self.config.vdab_search_terms or [""]
        seen_ids: set[str] = set()
        with httpx.Client(
            base_url=self.config.vdab_api_base,
            headers=self._headers(),
            timeout=30,
        ) as client:
            for term in terms:
                for job in self._search(client, term):
                    key = job.source_id or job.fingerprint
                    if key in seen_ids:
                        continue
                    seen_ids.add(key)
                    yield job

    def _search(self, client: httpx.Client, term: str) -> Iterable[Job]:
        params = {"q": term} if term else {}
        resp = client.get(self.config.vdab_search_path, params=params)
        resp.raise_for_status()
        payload = resp.json()
        if self.dump_raw:
            self.dump_raw.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            log.info("Raw response written to %s", self.dump_raw)
        for record in extract_records(payload):
            job = parse_vacancy(record)
            if job:
                yield job
