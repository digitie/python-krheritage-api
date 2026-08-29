from __future__ import annotations

from typing import Any

from krheritage.client import HeritageClient


class _FakeTransport:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        self.calls.append((url, params))
        return self.response

    def close(self) -> None:
        pass


_LIST_XML = b"""
<result>
  <totalCnt>1</totalCnt>
  <pageUnit>10</pageUnit>
  <pageIndex>1</pageIndex>
  <item>
    <ccbaKdcd>11</ccbaKdcd>
    <ccbaAsno>0000010000000</ccbaAsno>
    <ccbaCtcd>11</ccbaCtcd>
    <ccbaMnm1>Sungnyemun</ccbaMnm1>
  </item>
</result>
"""

_DETAIL_XML_INCOMPLETE = b"""
<result>
  <ccbaKdcd>99</ccbaKdcd>
  <ccbaAsno></ccbaAsno>
  <ccbaCtcd>99</ccbaCtcd>
  <item>
    <ccbaMnm1>Broken</ccbaMnm1>
  </item>
</result>
"""

_ERROR_XML = b"""
<cmmMsgHeader>
  <returnReasonCode>30</returnReasonCode>
  <returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>
  <errMsg>SERVICE KEY IS NOT REGISTERED ERROR.</errMsg>
</cmmMsgHeader>
"""


def _client_with_fake_transport(response: bytes) -> tuple[HeritageClient, _FakeTransport]:
    client = HeritageClient(api_key="dummy-key")
    fake = _FakeTransport(response)
    client._transport = fake  # type: ignore[assignment]
    return client, fake


def test_debug_fetch_routes_by_catalog_metadata_and_validates_model() -> None:
    client, fake = _client_with_fake_transport(_LIST_XML)

    run = client.debug_fetch("khs-search-list", params={"pageUnit": "10", "pageIndex": "1"})

    assert run.error is None
    assert run.validation_errors == ()
    assert len(run.processed) == 1
    assert run.processed[0]["ccbaMnm1"] == "Sungnyemun"
    assert run.parsed[0]["name_ko"] == "Sungnyemun"
    assert fake.calls[0][0].endswith("/SearchKindOpenapiList.do")
    assert fake.calls[0][1] == {"pageUnit": "10", "pageIndex": "1"}


def test_debug_fetch_reports_row_level_validation_errors_structurally() -> None:
    client, _fake = _client_with_fake_transport(_DETAIL_XML_INCOMPLETE)

    run = client.debug_fetch(
        "khs-search-detail",
        params={"ccbaKdcd": "99", "ccbaAsno": "9999999999999", "ccbaCtcd": "99"},
    )

    assert run.error is None
    assert len(run.validation_errors) == 1
    error = run.validation_errors[0]
    assert error["row_index"] == 0
    assert error["type"] == "ValidationError"
    assert error["traceback"]


def test_debug_fetch_structures_provider_error_envelopes() -> None:
    client, _fake = _client_with_fake_transport(_ERROR_XML)

    run = client.debug_fetch("khs-search-list", params={})

    assert run.error is not None
    assert run.error["type"] == "ApiErrorResponse"
    assert run.error["failure_kind"] == "api_error"
    assert run.error["result_code"] == "30"
    assert run.processed is None


def test_debug_fetch_redacts_the_service_key_from_request_preview() -> None:
    client, _fake = _client_with_fake_transport(b'{"resultCode":"00"}')

    run = client.debug_fetch(
        "data-go-kr-custom",
        params={},
        custom_path="/some/service/op",
    )

    assert run.request["params"]["serviceKey"] == "<REDACTED>"


def test_debug_fetch_requires_a_custom_path_for_the_custom_entry() -> None:
    client, fake = _client_with_fake_transport(b"{}")

    run = client.debug_fetch("data-go-kr-custom", params={}, custom_path="")

    assert run.error is not None
    assert run.error["type"] == "ValueError"
    assert fake.calls == []


def test_timeout_is_threaded_through_to_the_httpx_client() -> None:
    client = HeritageClient(api_key="dummy-key", timeout=5.0)
    try:
        assert client._transport._client.timeout.connect == 5.0
    finally:
        client.close()
