from __future__ import annotations

from krheritage.codes.area import CityCode
from krheritage.codes.district import Seoul
from krheritage.codes.domain import TYPE_TO_DOMAIN, HeritageDomain, domain_for_type
from krheritage.codes.heritage_type import HeritageType
from krheritage.codes.lang import Lang
from krheritage.codes.license import KoglLicense

__all__ = [
    "TYPE_TO_DOMAIN",
    "CityCode",
    "HeritageDomain",
    "HeritageType",
    "KoglLicense",
    "Lang",
    "Seoul",
    "domain_for_type",
]

