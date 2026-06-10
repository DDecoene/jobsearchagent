"""Canonical job schema and fingerprinting (CLAUDE.md sections 4 and 5)."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

# Legal-form suffixes that vary between sources for the same company.
_COMPANY_SUFFIXES = re.compile(
    r"\b(nv|bv|bvba|cvba|cv|vzw|sa|sprl|srl|gmbh|ltd|inc|plc|vof|comm\.?v)\b\.?",
)
_NON_ALNUM = re.compile(r"[^a-z0-9 ]+")
_WS = re.compile(r"\s+")
# Belgian postal codes in locations ("9000 Gent" vs "Gent").
_POSTAL_CODE = re.compile(r"\b\d{4}\b")


def _basic_normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = _NON_ALNUM.sub(" ", value.lower())
    return _WS.sub(" ", value).strip()


def normalize_title(title: str) -> str:
    return _basic_normalize(title)


def normalize_company(company: str) -> str:
    return _WS.sub(" ", _COMPANY_SUFFIXES.sub(" ", _basic_normalize(company))).strip()


def normalize_location(location: str) -> str:
    return _WS.sub(" ", _POSTAL_CODE.sub(" ", _basic_normalize(location))).strip()


def fingerprint(title: str, company: str, location: str) -> str:
    raw = "|".join(
        (normalize_title(title), normalize_company(company), normalize_location(location))
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class Job:
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    published_date: date | None = None
    source_id: str = ""
    fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        self.fingerprint = fingerprint(self.title, self.company, self.location)
