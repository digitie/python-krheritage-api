from __future__ import annotations

from krheritage.codes._compat import StrEnum
from krheritage.codes.heritage_type import HeritageType


class HeritageDomain(StrEnum):
    """Top-level 2024 national heritage domain classification."""

    CULTURAL = "cultural"
    NATURAL = "natural"
    INTANGIBLE = "intangible"

    @property
    def korean(self) -> str:
        return _DOMAIN_KO[self]


TYPE_TO_DOMAIN: dict[HeritageType, HeritageDomain] = {
    HeritageType.NATIONAL_TREASURE: HeritageDomain.CULTURAL,
    HeritageType.TREASURE: HeritageDomain.CULTURAL,
    HeritageType.HISTORIC_SITE: HeritageDomain.CULTURAL,
    HeritageType.HISTORIC_SCENIC: HeritageDomain.NATURAL,
    HeritageType.SCENIC_SITE: HeritageDomain.NATURAL,
    HeritageType.NATURAL_MONUMENT: HeritageDomain.NATURAL,
    HeritageType.INTANGIBLE_NATIONAL: HeritageDomain.INTANGIBLE,
    HeritageType.FOLKLORE_NATIONAL: HeritageDomain.CULTURAL,
    HeritageType.TANGIBLE_LOCAL: HeritageDomain.CULTURAL,
    HeritageType.INTANGIBLE_LOCAL: HeritageDomain.INTANGIBLE,
    HeritageType.MEMORIAL_LOCAL: HeritageDomain.NATURAL,
    HeritageType.FOLKLORE_LOCAL: HeritageDomain.CULTURAL,
    HeritageType.HERITAGE_MATERIAL: HeritageDomain.CULTURAL,
    HeritageType.REGISTERED: HeritageDomain.CULTURAL,
    HeritageType.MOVABLE_GENERAL: HeritageDomain.CULTURAL,
    HeritageType.BURIED: HeritageDomain.CULTURAL,
    HeritageType.OVERSEAS_HERITAGE: HeritageDomain.CULTURAL,
    HeritageType.UNDESIGNATED_RUIN: HeritageDomain.CULTURAL,
    HeritageType.UNDESIGNATED_ARTIFACT: HeritageDomain.CULTURAL,
}

_DOMAIN_KO: dict[HeritageDomain, str] = {
    HeritageDomain.CULTURAL: "문화유산",
    HeritageDomain.NATURAL: "자연유산",
    HeritageDomain.INTANGIBLE: "무형유산",
}


def domain_for_type(heritage_type: HeritageType) -> HeritageDomain:
    return TYPE_TO_DOMAIN[heritage_type]

