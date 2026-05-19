from __future__ import annotations

from krheritage.models.base import KrHeritageModel


class LegacyRecord(KrHeritageModel):
    dataset_id: str
    title: str | None = None
    raw: dict[str, object]

