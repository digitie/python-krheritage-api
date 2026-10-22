from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from krheritage.models import HeritageEvent
from krheritage.services import EventService, GisService, SearchService
from krheritage.services.event import _event_mapping


class FakeTransport:
    def __init__(self, *responses: bytes) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    async def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        self.calls.append((url, params))
        return self.responses.pop(0)

    async def aclose(self) -> None:
        pass


async def test_search_service_iter_all_details_uses_list_and_detail_endpoints() -> None:
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

    items = [
        item async for item in service.iter_all_details(page_size=100, max_pages=1, ccba_kdcd="25")
    ]

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


async def test_search_service_iter_all_details_skips_rows_with_incomplete_key(
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
        items = [item async for item in service.iter_all_details(page_size=100, max_pages=1)]

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


async def test_search_service_details_merges_result_level_identifiers() -> None:
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

    detail = await service.details("11", "0000010000000", "11")

    assert detail.key.natural_key == "11-0000010000000-11"
    assert detail.name_ko == "Seoul Sungnyemun"
    assert detail.category == "국보"
    assert detail.longitude == pytest.approx(126.975312652739)
    assert detail.latitude == pytest.approx(37.559975221378)
    assert detail.content == "Sungnyemun"


async def test_search_service_details_rejects_identifier_less_payload() -> None:
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
        (await service.details("99", "9999999999999", "99"))


EVENT_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "event_list_2026_10.xml"


async def test_event_service_parses_live_event_list_payload() -> None:
    # live selectEventListOpenapi.do(searchYear=2026&searchMonth=10, 2026-10-22 캡처)의
    # <item> 4건을 원문 그대로 담은 fixture — 이전 fixture(sn/startDate/siteName)는 실제
    # 응답과 달라 운영에서 sn·기간·장소·주소가 전부 None이었다.
    transport = FakeTransport(EVENT_FIXTURE.read_bytes())
    service = EventService(transport=transport, base_url="http://www.khs.go.kr/cha")

    events = [item async for item in service.iter_months(search_year=2026, search_month=10)]

    assert transport.calls[0] == (
        "http://www.khs.go.kr/cha/openapi/selectEventListOpenapi.do",
        {"searchYear": "2026", "searchMonth": "10"},
    )
    assert len(events) == 4
    first = events[0]
    assert first.sn == "15720"
    assert first.site_code == "09"
    assert first.title == "허선구 고가에서 나누는 특별한 하루"
    assert first.display_title == "허선구 고가에서 나누는 특별한 하루"
    assert first.contents is not None and first.contents.startswith("고가에서 펼치는")
    assert first.starts_on == date(2026, 8, 29)
    assert first.ends_on == date(2029, 8, 29)  # 원천 값 그대로(상류 오기 추정)
    assert first.group_name == "불휘기픈남간"
    assert first.tel_name == "010-5438-4331"
    assert first.place == "허선구고가"
    assert first.url == "https://mynolto.com/program/1004"  # 선행 공백 제거
    assert first.target_audience == "청소년,일반인,외국인등"
    assert first.fee == "무료"
    assert first.main_image is None  # 빈 CDATA
    assert first.sido == "경상남도"
    assert first.gugun == "진주시"
    assert first.address == "경상남도 진주시"
    assert first.schedule_text is not None and first.schedule_text.startswith("5월23일")
    assert first.longitude is None
    assert first.latitude is None
    # 원천 payload 보존.
    assert first.raw["seqNo"] == "15720"
    assert first.raw["sDate"] == "20260829"

    # seqNo는 프로그램 식별자라 회차마다 반복된다 — 회차 키로 구분한다.
    second = events[1]
    assert second.sn == first.sn
    assert (second.starts_on, second.ends_on) == (date(2026, 10, 17), date(2026, 10, 17))
    assert first.occurrence_key == "15720::2026-08-29::2029-08-29"
    assert second.occurrence_key == "15720::2026-10-17::2026-10-17"

    # 빈 CDATA 장소/연락처는 None.
    assert events[2].place is None
    assert events[2].address == "충청북도 음성군"
    assert events[3].tel_name is None
    assert events[3].place == "곡성제호정, 몽심재, 죽산박씨 종가"


def test_heritage_event_address_and_dates_are_best_effort() -> None:
    only_sido = HeritageEvent.model_validate({"seqNo": "1", "sido": "서울특별시", "gugun": ""})
    assert only_sido.address == "서울특별시"
    assert HeritageEvent.model_validate({"seqNo": "1"}).address is None
    explicit = HeritageEvent.model_validate({"sido": "A", "gugun": "B", "address": "직접 주소"})
    assert explicit.address == "직접 주소"

    dated = HeritageEvent.model_validate({"sDate": "2026-10-01", "eDate": "20261399"})
    assert dated.starts_on == date(2026, 10, 1)
    assert dated.ends_on is None  # 달력상 불가능한 값은 None (raw에 원문 보존)
    assert HeritageEvent.model_validate({"sDate": ""}).starts_on is None
    assert HeritageEvent.model_validate({"sDate": "2026"}).starts_on is None
    assert HeritageEvent.model_validate({"sDate": "20261001"}).occurrence_key is None
    # JSON 응답처럼 숫자가 와도 row 하나로 월 전체가 깨지지 않는다.
    numeric = HeritageEvent.model_validate({"seqNo": 15720, "sDate": 20261001})
    assert numeric.sn == "15720"
    assert numeric.starts_on == date(2026, 10, 1)
    assert HeritageEvent.model_validate({"sDate": "2026-10-01T09:00:00"}).starts_on == date(
        2026, 10, 1
    )


def test_heritage_event_keeps_split_title_compat() -> None:
    event = HeritageEvent.model_validate({"title": "Festival", "subTitle2": "Night"})
    assert event.display_title == "Festival Night"
    legacy = HeritageEvent.model_validate(_event_mapping({"subTitle1": "A", "subTitle2": "B"}))
    assert legacy.display_title == "A B"


async def test_gis_service_spca_returns_geo_feature_collection() -> None:
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

    collection = await service.spca(min_lng=126.0, min_lat=37.0, max_lng=127.0, max_lat=38.0)

    assert collection.features[0].geometry is not None
    assert collection.features[0].geometry.type == "Point"
    assert collection.features[0].properties["gid"] == "AREA-1"
