from __future__ import annotations

import hashlib
import json
from typing import Any

from krheritage import PROVIDER_NAME
from krheritage.models import GeoFeature, HeritageDetail, HeritageKey, HeritageSummary

HERITAGE_DATASET_KEY = "search_list"
EVENT_DATASET_KEY = "event_list"
GIS_SPCA_DATASET_KEY = "gis_spca"
GIS_3070426_DATASET_KEY = "gis_3070426"


def source_natural_key(record: HeritageDetail | HeritageSummary | HeritageKey) -> str:
    """Return the official heritage source key without creating a feature."""

    if isinstance(record, HeritageKey):
        return record.natural_key
    return record.key.natural_key


def source_identity(
    record: HeritageDetail | HeritageSummary | HeritageKey,
    *,
    dataset_key: str = HERITAGE_DATASET_KEY,
    source_entity_type: str = "heritage",
) -> dict[str, str]:
    return {
        "provider": PROVIDER_NAME,
        "dataset_key": dataset_key,
        "source_entity_type": source_entity_type,
        "source_entity_id": source_natural_key(record),
    }


def gis_source_identity(
    feature: GeoFeature,
    *,
    dataset_key: str = GIS_3070426_DATASET_KEY,
) -> dict[str, str]:
    properties = feature.properties
    source_id = _first_text(properties, "gid", "id", "fid", "pnu", "mnum", "objectid")
    if source_id is None:
        digest = json.dumps(properties, sort_keys=True, default=str).encode()
        source_id = hashlib.sha256(digest).hexdigest()
    return {
        "provider": PROVIDER_NAME,
        "dataset_key": dataset_key,
        "source_entity_type": "heritage_area",
        "source_entity_id": source_id,
    }


def _first_text(values: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = values.get(key)
        if value not in (None, ""):
            return str(value)
    return None
