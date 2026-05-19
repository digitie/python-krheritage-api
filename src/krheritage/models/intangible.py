from __future__ import annotations

from krheritage.models.base import KrHeritageModel


class IntangibleRecord(KrHeritageModel):
    dataset_id: str
    title: str | None = None
    raw: dict[str, object]

