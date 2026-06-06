from __future__ import annotations

from typing import Any

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
