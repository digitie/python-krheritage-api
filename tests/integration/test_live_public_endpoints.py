from __future__ import annotations

import os
from typing import Any

import pytest

from krheritage.config import HeritageConfig
from krheritage.transport import AsyncHttpxTransport, parse_payload

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("KHERITAGE_RUN_LIVE") != "1",
        reason="set KHERITAGE_RUN_LIVE=1 to run public endpoint live tests",
    ),
]


async def test_live_khs_list_detail_and_media_endpoints() -> None:
    config = HeritageConfig.from_env(max_rps=2)
    transport = AsyncHttpxTransport(config)
    try:
        list_payload = await transport.get(
            f"{config.heritage_base_url}/SearchKindOpenapiList.do",
            {"pageUnit": "1", "pageIndex": "1"},
        )
        list_result = parse_payload(list_payload)["result"]
        list_item = _single_item(list_result["item"])

        assert int(list_result["totalCnt"]) > 1_000
        assert list_item["ccmaName"] == "국보"
        assert list_item["ccbaMnm1"]

        key_params = {
            "ccbaKdcd": list_item["ccbaKdcd"],
            "ccbaAsno": list_item["ccbaAsno"],
            "ccbaCtcd": list_item["ccbaCtcd"],
        }

        detail_payload = await transport.get(
            f"{config.heritage_base_url}/SearchKindOpenapiDt.do",
            key_params,
        )
        detail_result = parse_payload(detail_payload)["result"]
        detail_item = _single_item(detail_result["item"])

        assert detail_result["ccbaKdcd"] == key_params["ccbaKdcd"]
        assert detail_item["ccbaMnm1"] == list_item["ccbaMnm1"]
        assert float(detail_result["longitude"]) > 0
        assert float(detail_result["latitude"]) > 0

        image_payload = await transport.get(
            f"{config.heritage_base_url}/SearchImageOpenapi.do",
            key_params,
        )
        image_result = parse_payload(image_payload)["result"]
        assert int(image_result["totalCnt"]) >= 1
        assert _first_string(_single_item(image_result["item"])["imageUrl"]).startswith("http")

        video_payload = await transport.get(
            f"{config.heritage_base_url}/SearchVideoOpenapi.do",
            key_params,
        )
        video_result = parse_payload(video_payload)["result"]
        assert int(video_result["totalCnt"]) >= 0
    finally:
        await transport.aclose()


async def test_live_transport_follows_legacy_http_redirect() -> None:
    config = HeritageConfig.from_env(max_rps=2)
    transport = AsyncHttpxTransport(config)
    try:
        payload = await transport.get(
            "http://www.khs.go.kr/cha/SearchKindOpenapiList.do",
            {"pageUnit": "1", "pageIndex": "1"},
        )
        result = parse_payload(payload)["result"]
        assert _single_item(result["item"])["ccbaMnm1"]
    finally:
        await transport.aclose()


async def test_live_gis_endpoint_returns_xml_response() -> None:
    config = HeritageConfig.from_env(max_rps=2)
    transport = AsyncHttpxTransport(config)
    try:
        payload = await transport.get(f"{config.gis_base_url}/xmlService/spca.do")
        parsed = parse_payload(payload)
        root_name, response = next(iter(parsed.items()))

        assert root_name.endswith("response")
        assert response["message"]["code"] == "500"
        assert "totalCnt" in response
    finally:
        await transport.aclose()


def _single_item(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        first = value[0]
    else:
        first = value
    assert isinstance(first, dict)
    return first


def _first_string(value: Any) -> str:
    if isinstance(value, list):
        first = value[0]
    else:
        first = value
    assert isinstance(first, str)
    return first
