from __future__ import annotations

from datetime import datetime

from pydantic import Field

from krheritage.models.base import KrHeritageModel


class HeritageSyncCursor(KrHeritageModel):
    dataset: str
    last_seen_at: datetime | None = None
    page: int = Field(default=1, ge=1)
    raw: dict[str, object] = Field(default_factory=dict)

