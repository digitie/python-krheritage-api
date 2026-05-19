from __future__ import annotations

import warnings

from krheritage.transport import parse_payload, resolve


def test_alias_resolution_warns_for_recode_url() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        resolved = resolve("https://apis.data.go.kr/1550246/recodeImageView")

    assert resolved == "https://apis.data.go.kr/1550246/recordImageView"
    assert any(issubclass(item.category, DeprecationWarning) for item in caught)


def test_parse_json_payload() -> None:
    assert parse_payload(b'{"resultCode":"00"}') == {"resultCode": "00"}


def test_parse_xml_payload() -> None:
    parsed = parse_payload(b"<result><item><name>A</name></item></result>")

    assert parsed == {"result": {"item": {"name": "A"}}}

