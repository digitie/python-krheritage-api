from __future__ import annotations

from krheritage import PROVIDER_NAME
from krheritage.integrations.krtour_map import (
    GIS_3070426_DATASET_KEY,
    HERITAGE_DATASET_KEY,
    gis_source_identity,
    source_identity,
    source_natural_key,
)
from krheritage.models import GeoFeature, GeoGeometry, HeritageKey, HeritageSummary


def test_source_identity_uses_public_model_without_feature_adapter() -> None:
    summary = HeritageSummary.model_validate(
        {
            "key": {"ccbaKdcd": "25", "ccbaAsno": "0000001", "ccbaCtcd": "11"},
            "ccbaMnm1": "Heritage",
        }
    )

    assert source_natural_key(summary) == "25-0000001-11"
    assert source_identity(summary) == {
        "provider": PROVIDER_NAME,
        "dataset_key": HERITAGE_DATASET_KEY,
        "source_entity_type": "heritage",
        "source_entity_id": "25-0000001-11",
    }


def test_source_identity_accepts_key_model_directly() -> None:
    key = HeritageKey.model_validate(
        {"ccbaKdcd": "27", "ccbaAsno": "0000002", "ccbaCtcd": "35"}
    )

    assert source_natural_key(key) == "27-0000002-35"
    assert source_identity(key)["source_entity_id"] == "27-0000002-35"


def test_gis_source_identity_preserves_area_dataset_identity() -> None:
    feature = GeoFeature(
        geometry=GeoGeometry(type="Polygon", coordinates=[]),
        properties={"gid": "AREA-1"},
    )

    assert gis_source_identity(feature) == {
        "provider": PROVIDER_NAME,
        "dataset_key": GIS_3070426_DATASET_KEY,
        "source_entity_type": "heritage_area",
        "source_entity_id": "AREA-1",
    }
