from __future__ import annotations

from typing import Literal

from krheritage.models.base import KrHeritageModel

GeometryType = Literal["Point", "Polygon", "MultiPolygon", "LineString", "MultiLineString"]


class GeoGeometry(KrHeritageModel):
    type: GeometryType
    coordinates: object


class GeoFeature(KrHeritageModel):
    type: Literal["Feature"] = "Feature"
    geometry: GeoGeometry | None = None
    properties: dict[str, object]


class GeoFeatureCollection(KrHeritageModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[GeoFeature]

