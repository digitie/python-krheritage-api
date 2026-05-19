from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from krheritage.models import GeoFeature, GeoFeatureCollection, GeoGeometry
from krheritage.services._payload import parsed_result, result_items
from krheritage.transport import SyncTransport


@dataclass(slots=True)
class GisService:
    """Public GIS service for heritage coordinate/boundary data."""

    transport: SyncTransport
    base_url: str

    def spca(
        self,
        *,
        min_lng: float | None = None,
        min_lat: float | None = None,
        max_lng: float | None = None,
        max_lat: float | None = None,
    ) -> GeoFeatureCollection:
        params = _without_none(
            {
                "minLng": min_lng,
                "minLat": min_lat,
                "maxLng": max_lng,
                "maxLat": max_lat,
            }
        )
        result = parsed_result(
            self.transport.get(f"{self.base_url}/xmlService/spca.do", params=params)
        )
        features = [_geo_feature_from_mapping(item) for item in result_items(result)]
        return GeoFeatureCollection(
            features=[feature for feature in features if feature is not None]
        )


def _geo_feature_from_mapping(raw: Mapping[str, Any]) -> GeoFeature | None:
    geometry = raw.get("geometry") or raw.get("geojson")
    if isinstance(geometry, Mapping):
        geo = GeoGeometry.model_validate(geometry)
    else:
        lon = _float_or_none(
            raw.get("longitude")
            or raw.get("lon")
            or raw.get("lng")
            or raw.get("x")
            or raw.get("mapX")
        )
        lat = _float_or_none(
            raw.get("latitude") or raw.get("lat") or raw.get("y") or raw.get("mapY")
        )
        if lon is None or lat is None:
            geo = None
        else:
            geo = GeoGeometry(type="Point", coordinates=[lon, lat])
    return GeoFeature(geometry=geo, properties=dict(raw))


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _without_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}
