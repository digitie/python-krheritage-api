from __future__ import annotations

from collections.abc import Iterable

from krheritage.models import HeritageDetail


def iter_training_text(records: Iterable[HeritageDetail]) -> Iterable[str]:
    for record in records:
        if record.license is not None and record.license.allows_ai_training and record.content:
            yield record.content

