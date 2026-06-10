"""Job sources. Each source yields normalized Job objects (CLAUDE.md section 5)."""

from __future__ import annotations

from typing import Iterable, Protocol

from ..models import Job


class JobSource(Protocol):
    name: str

    def fetch(self) -> Iterable[Job]:
        """Yield jobs from this source, normalized into the canonical schema."""
        ...
