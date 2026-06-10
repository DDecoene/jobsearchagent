"""Configuration from environment variables, with optional .env file.

VDAB endpoint details (base URL, path, auth header) live behind your
registered account on https://developer.vdab.be/openservices/ — fill them
into .env after subscribing to the Vacatures API. See .env.example.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """Minimal .env loader; real environment variables take precedence."""
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        os.environ.setdefault(key, value)


@dataclass
class Config:
    db_path: Path
    profile_path: Path
    backfill_days: int

    vdab_api_base: str
    vdab_search_path: str
    vdab_api_key: str
    vdab_auth_header: str
    vdab_auth_prefix: str
    vdab_search_terms: list[str]

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            db_path=Path(os.environ.get("JOBSEARCH_DB", "data/jobs.sqlite3")),
            profile_path=Path(os.environ.get("JOBSEARCH_PROFILE", "PROFILE.md")),
            backfill_days=int(os.environ.get("JOBSEARCH_BACKFILL_DAYS", "14")),
            vdab_api_base=os.environ.get("VDAB_API_BASE", "https://api.vdab.be"),
            vdab_search_path=os.environ.get("VDAB_SEARCH_PATH", "/services/openservices/vacatures"),
            vdab_api_key=os.environ.get("VDAB_API_KEY", ""),
            vdab_auth_header=os.environ.get("VDAB_AUTH_HEADER", "Authorization"),
            vdab_auth_prefix=os.environ.get("VDAB_AUTH_PREFIX", "Bearer "),
            vdab_search_terms=[
                t.strip()
                for t in os.environ.get("VDAB_SEARCH_TERMS", "").split(",")
                if t.strip()
            ],
        )

    def require_profile(self) -> Path:
        """Scoring is anchored by PROFILE.md (CLAUDE.md 4b); refuse without it."""
        if not self.profile_path.is_file():
            raise FileNotFoundError(
                f"{self.profile_path} not found. Copy PROFILE.template.md to "
                f"{self.profile_path} and fill it in — scoring without a "
                "profile is noise."
            )
        return self.profile_path
