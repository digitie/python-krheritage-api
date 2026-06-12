from __future__ import annotations

import logging
from typing import Any

import pytest
from pydantic import ValidationError

from krheritage.services import EventService, GisService, SearchService


class FakeTransport:
    def __init__(self, *responses: bytes) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        self.calls.append((url, params))
        return self.responses.pop(0)

    def close(self) -> None:
        pass


def test_search_service_iter_all_details_uses_list_and_detail_endpoints() -> None:
    transport = FakeTransport(
        b"""
        <result>
          <totalCnt>1</totalCnt>
          <pageUnit>100</pageUnit>
          <pageIndex>1</pageIndex>
          <item>
            <ccbaKdcd>25</ccbaKdcd>
            <ccbaAsno>0000001</ccbaAsno>
            <ccbaCtcd>11</ccbaCtcd>
            <ccbaMnm1>Heritage</ccbaMnm1>
            <longitude>126.9769</longitude>
            <latitude>37.5796</latitude>
          </item>
        </result>
        """,
        b"""
        <result>
          <ccbaKdcd>25</ccbaKdcd>
          <ccbaAsno>0000001</ccbaAsno>
          <ccbaCtcd>11</ccbaCtcd>
          <ccbaMnm1>Heritage</ccbaMnm1>
          <ccbaAsdt>20260101</ccbaAsdt>
          <ccbaLcad>Seoul Jongno</ccbaLcad>
          <content>Line1&lt;br/&gt;Line2&amp;nbsp;</content>
        </result>
        """,
    )
    service = SearchService(transport=transport, base_url="http://www.khs.go.kr/cha")

    items = list(service.iter_all_details(page_size=100, max_pages=1, ccba_kdcd="25"))

    assert items[0].key.natural_key == "25-0000001-11"
    assert items[0].content == "Line1\nLine2"
    assert transport.calls[0] == (
        "http://www.khs.go.kr/cha/SearchKindOpenapiList.do",
        {"pageUnit": 100, "pageIndex": 1, "ccbaKdcd": "25"},
    )
    assert transport.calls[1] == (
        "http://www.khs.go.kr/cha/SearchKindOpenapiDt.do",
        {"ccbaKdcd": "25", "ccbaAsno": "0000001", "ccbaCtcd": "11"},
    )


def test_search_service_iter_all_details_skips_rows_with_incomplete_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # live 목록에는 복합키 구성요소가 결측(빈 element/누락)인 row가 간헐적으로
    # 존재한다 — 결측 row는 detail 조회 없이 경고 로그와 함께 skip해야 한다 (#5).
    transport = FakeTransport(
        b"""
        <result>
          <totalCnt>2</totalCnt>
          <pageUnit>100</pageUnit>
          <pageIndex>1</pageIndex>
          <item>
            <ccbaKdcd>25</ccbaKdcd>
            <ccbaAsno></ccbaAsno>
            <ccbaMnm1>Broken Row</ccbaMnm1>
          </item>
          <item>
            <ccbaKdcd>25</ccbaKdcd>
            <ccbaAsno>0000001</ccbaAsno>
            <ccbaCtcd>11</ccbaCtcd>
            <ccbaMnm1>Heritage</ccbaMnm1>
          </item>
        </result>
        """,
        b"""
        <result>
          <ccbaKdcd>25</ccbaKdcd>
          <ccbaAsno>0000001</ccbaAsno>
          <ccbaCtcd>11</ccbaCtcd>
          <ccbaMnm1>Heritage</ccbaMnm1>
        </result>
        """,
    )
    service = SearchService(transport=transport, base_url="http://www.khs.go.kr/cha")

    with caplog.at_level(logging.WARNING, logger="krheritage.services.search"):
        items = list(service.iter_all_details(page_size=100, max_pages=1))

    # 정상 row 1건만 detail 조회: list 1콜 + detail 1콜.
    assert [item.key.natural_key for item in items] == ["25-0000001-11"]
    assert len(transport.calls) == 2
    assert transport.calls[1] == (
        "http://www.khs.go.kr/cha/SearchKindOpenapiDt.do",
        {"ccbaKdcd": "25", "ccbaAsno": "0000001", "ccbaCtcd": "11"},
    )
    # 결측 row는 조용히 버리지 않는다 — 식별 가능한 정보가 경고에 남아야 한다.
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "Broken Row" in warnings[0].getMessage()
    assert "ccbaAsno=None" in warnings[0].getMessage()


def test_search_service_details_merges_result_level_identifiers() -> None:
    # live SearchKindOpenapiDt 응답은 복합키/좌표를 <result> 레벨에 두고 본문을
    # <item>에 중첩한다 — item만 취하면 key가 유실되어 검증이 터진다 (#5).
    transport = FakeTransport(
        b"""
        <result>
          <ccbaKdcd>11</ccbaKdcd>
          <ccbaAsno>0000010000000</ccbaAsno>
          <ccbaCtcd>11</ccbaCtcd>
          <ccbaCpno>1111100010000</ccbaCpno>
          <longitude>126.975312652739</longitude>
          <latitude>37.559975221378</latitude>
          <item>
            <ccmaName><![CDATA[\xea\xb5\xad\xeb\xb3\xb4]]></ccmaName>
            <ccbaMnm1><![CDATA[Seoul Sungnyemun]]></ccbaMnm1>
            <ccbaQuan><![CDATA[1\xeb\x8f\x99]]></ccbaQuan>
            <ccbaAsdt><![CDATA[19621220]]></ccbaAsdt>
            <content><![CDATA[Sungnyemun]]></content>
          </item>
        </result>
        """,
    )
    service = SearchService(transport=transport, base_url="http://www.khs.go.kr/cha")

    detail = service.details("11", "0000010000000", "11")

    assert detail.key.natural_key == "11-0000010000000-11"
    assert detail.name_ko == "Seoul Sungnyemun"
    assert detail.category == "국보"
    assert detail.longitude == pytest.approx(126.975312652739)
    assert detail.latitude == pytest.approx(37.559975221378)
    assert detail.content == "Sungnyemun"


def test_search_service_details_rejects_identifier_less_payload() -> None:
    # 빈/불일치 key로 조회하면 live 응답은 식별자 없는 빈 payload를 돌려준다 —
    # 조용히 통과시키지 않고 fail-loud 해야 한다 (#5).
    transport = FakeTransport(
        b"""
        <result>
          <ccbaKdcd></ccbaKdcd>
          <ccbaAsno></ccbaAsno>
          <ccbaCtcd></ccbaCtcd>
          <longitude></longitude>
          <latitude></latitude>
          <item>
            <ccbaMnm1><![CDATA[]]></ccbaMnm1>
            <content><![CDATA[]]></content>
          </item>
        </result>
        """,
    )
    service = SearchService(transport=transport, base_url="http://www.khs.go.kr/cha")

    with pytest.raises(ValidationError, match="missing composite key"):
        service.details("99", "9999999999999", "99")


def test_event_service_iter_months_parses_legacy_and_split_titles() -> None:
    transport = FakeTransport(
        b"""
        <result>
          <item>
            <sn>EVT-1</sn>
            <subTitle1>Festival</subTitle1>
            <subTitle2>Night</subTitle2>
            <startDate>20260501</startDate>
            <endDate>20260503</endDate>
            <siteName>Palace</siteName>
          </item>
        </result>
        """
    )
    service = EventService(transport=transport, base_url="http://www.khs.go.kr/cha")

    events = list(service.iter_months(search_year=2026, search_month=5))

    assert events[0].display_title == "Festival Night"
    assert events[0].starts_on is not None
    assert events[0].starts_on.isoformat() == "2026-05-01"
    # 원천 payload 보존 (intangible/legacy/research 모델과 동일).
    assert events[0].raw["sn"] == "EVT-1"
    assert events[0].raw["startDate"] == "20260501"
    assert transport.calls[0] == (
        "http://www.khs.go.kr/cha/openapi/selectEventListOpenapi.do",
        {"searchYear": "2026", "searchMonth": "05"},
    )


def test_gis_service_spca_returns_geo_feature_collection() -> None:
    transport = FakeTransport(
        b"""
        <result>
          <item>
            <gid>AREA-1</gid>
            <longitude>126.9769</longitude>
            <latitude>37.5796</latitude>
          </item>
        </result>
        """
    )
    service = GisService(transport=transport, base_url="https://gis-heritage.go.kr/openapi")

    collection = service.spca(min_lng=126.0, min_lat=37.0, max_lng=127.0, max_lat=38.0)

    assert collection.features[0].geometry is not None
    assert collection.features[0].geometry.type == "Point"
    assert collection.features[0].properties["gid"] == "AREA-1"
