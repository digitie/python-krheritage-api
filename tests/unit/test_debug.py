from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import BaseModel

from krheritage.debug import (
    DebugRun,
    debug_error,
    jsonable,
    redact_sensitive,
    save_fixture,
    slugify_case_name,
)
from krheritage.exceptions import (
    ApiErrorResponse,
    ConfigError,
    PayloadParseError,
    RateLimitError,
    TransportError,
)


class _Point(BaseModel):
    x: int
    y: int


def test_jsonable_handles_models_dataclasses_dates_and_paths() -> None:
    run = DebugRun(
        function="fetch",
        input={},
        request={},
        response={},
        parsed=_Point(x=1, y=2),
        processed=[Path("a/b"), date(2026, 1, 2), datetime(2026, 1, 2, 3, 4)],
        trace=["step"],
    )

    dumped = jsonable(run)

    assert dumped["parsed"] == {"x": 1, "y": 2}
    assert dumped["processed"][0] == str(Path("a/b"))
    assert dumped["processed"][1] == "2026-01-02"
    assert dumped["processed"][2].startswith("2026-01-02T03:04:00")


def test_redact_sensitive_masks_known_keys_case_insensitively() -> None:
    payload = {
        "serviceKey": "secret",
        "ServiceKey": "secret2",
        "nested": {"api_key": "abc", "safe": "keep"},
        "list": [{"authorization": "Bearer x"}],
    }

    redacted = redact_sensitive(payload)

    assert redacted["serviceKey"] == "<REDACTED>"
    assert redacted["ServiceKey"] == "<REDACTED>"
    assert redacted["nested"]["api_key"] == "<REDACTED>"
    assert redacted["nested"]["safe"] == "keep"
    assert redacted["list"][0]["authorization"] == "<REDACTED>"


def test_debug_error_generic_exception_has_type_message_traceback() -> None:
    try:
        raise ValueError("boom")
    except ValueError as exc:
        payload = debug_error(exc)

    assert payload["type"] == "ValueError"
    assert payload["message"] == "boom"
    assert "ValueError: boom" in payload["traceback"]


def test_debug_error_api_error_response_carries_provider_fields() -> None:
    try:
        raise ApiErrorResponse(code="30", message="bad key", payload={"a": 1})
    except ApiErrorResponse as exc:
        payload = debug_error(exc)

    assert payload["failure_kind"] == "api_error"
    assert payload["result_code"] == "30"
    assert payload["retryable"] is False


def test_debug_error_payload_parse_error_carries_reason_and_length() -> None:
    try:
        raise PayloadParseError("invalid JSON payload", 12, b"not json")
    except PayloadParseError as exc:
        payload = debug_error(exc)

    assert payload["failure_kind"] == "parse"
    assert payload["reason"] == "invalid JSON payload"
    assert payload["length"] == 12


def test_debug_error_transport_error_extracts_status_code() -> None:
    try:
        raise TransportError("HTTP 404 error for url 'https://example.com'")
    except TransportError as exc:
        payload = debug_error(exc)

    assert payload["failure_kind"] == "transport"
    assert payload["status_code"] == 404
    assert payload["retryable"] is False


def test_debug_error_transport_error_treats_5xx_as_retryable() -> None:
    try:
        raise TransportError("HTTP 503 error for url 'https://example.com'")
    except TransportError as exc:
        payload = debug_error(exc)

    assert payload["status_code"] == 503
    assert payload["retryable"] is True


def test_debug_error_rate_limit_and_config_errors() -> None:
    try:
        raise RateLimitError("too fast")
    except RateLimitError as exc:
        rate_payload = debug_error(exc)
    try:
        raise ConfigError("bad config")
    except ConfigError as exc:
        config_payload = debug_error(exc)

    assert rate_payload["failure_kind"] == "rate_limit"
    assert rate_payload["retryable"] is True
    assert config_payload["failure_kind"] == "config"
    assert config_payload["retryable"] is False


def test_slugify_case_name_normalizes_and_falls_back() -> None:
    assert slugify_case_name("  Normal Case!! ") == "normal-case"
    assert slugify_case_name("") == "case"
    assert slugify_case_name("___") == "case"


def test_save_fixture_writes_json_and_redacts_secrets(tmp_path: Path) -> None:
    path = save_fixture(
        base_dir=tmp_path,
        function_name="khs-search-list",
        case_name="Normal Case",
        description="desc",
        input_data={"serviceKey": "secret", "params": {"a": 1}},
        request_data={"url": "https://x", "serviceKey": "secret"},
        response_data={"body": {"ok": True}},
        parsed_result=[{"name_ko": "A"}],
        processed_result=[{"name_ko": "A"}],
    )

    assert path == tmp_path / "khs-search-list" / "normal-case.json"
    text = path.read_text(encoding="utf-8")
    assert "secret" not in text
    assert "<REDACTED>" in text
    assert '"name_ko": "A"' in text


def test_save_fixture_refuses_overwrite_by_default(tmp_path: Path) -> None:
    def _save(*, overwrite: bool = False) -> Path:
        return save_fixture(
            base_dir=tmp_path,
            function_name="khs-search-list",
            case_name="dup",
            description="d",
            input_data={},
            request_data={},
            response_data={},
            parsed_result=None,
            processed_result=None,
            overwrite=overwrite,
        )

    _save()

    with pytest.raises(FileExistsError):
        _save()

    # overwrite=True must succeed
    _save(overwrite=True)
