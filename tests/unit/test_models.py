from __future__ import annotations

from krheritage.codes import HeritageDomain, KoglLicense
from krheritage.models import HeritageKey, HeritageSummary, PaginatedResult


def test_heritage_key_computed_fields() -> None:
    key = HeritageKey.model_validate(
        {"ccbaKdcd": "25", "ccbaAsno": "0000001", "ccbaCtcd": "11"}
    )

    assert key.natural_key == "25-0000001-11"
    assert key.heritage_type is not None
    assert key.heritage_type.korean == "국보"


def test_heritage_summary_aliases_and_domain() -> None:
    summary = HeritageSummary.model_validate(
        {
            "key": {"ccbaKdcd": "30", "ccbaAsno": "0000002", "ccbaCtcd": "35"},
            "ccbaMnm1": "테스트 천연기념물",
            "ccbaCtcdNm": "충청북도",
            "ccsiName": "청주시",
            "longitude": 127.0,
            "latitude": 36.0,
            "license": 3397,
        }
    )

    assert summary.domain is HeritageDomain.NATURAL
    assert summary.address == "충청북도 청주시"
    assert summary.license is KoglLicense.TYPE_AI


def test_paginated_result_iterates() -> None:
    result = PaginatedResult[int](total=2, items=[1, 2])

    assert list(result) == [1, 2]
    assert len(result) == 2
