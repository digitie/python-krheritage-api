"""Shared helpers for the Streamlit debug UI and fixture generation.

These are deliberately package-level (not inlined in the Streamlit script)
so they stay reusable and testable outside of Streamlit: fixture recording,
error redaction, and the ``DebugRun`` shape used by
``HeritageClient.debug_fetch``.
"""

from __future__ import annotations

import json
import re
import traceback as _traceback
from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from os import PathLike
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from krheritage.exceptions import (
    ApiErrorResponse,
    ConfigError,
    KrHeritageError,
    PayloadParseError,
    RateLimitError,
    TransportError,
)

SENSITIVE_KEYS = {
    "authorization",
    "x-api-key",
    "api_key",
    "apikey",
    "service_key",
    "servicekey",
    "service-key",
    "access_token",
    "refresh_token",
}
DEFAULT_ASSERTION = {
    "mode": "snapshot",
    "exclude_fields": ["fetched_at", "request_id", "updated_at"],
    "required_fields": [],
}

_HTTP_STATUS_RE = re.compile(r"HTTP (\d{3})")
_TRACEBACK_CHAR_LIMIT = 4000


@dataclass(frozen=True)
class DebugRun:
    """The input/request/response/parsed/processed bundle of one debug run."""

    function: str
    input: dict[str, Any]
    request: dict[str, Any]
    response: dict[str, Any]
    parsed: Any
    processed: Any
    trace: list[str]
    error: dict[str, Any] | None = None
    validation_errors: tuple[dict[str, Any], ...] = ()
    catalog: dict[str, Any] | None = None


def jsonable(obj: Any) -> Any:
    """Convert Pydantic models, dataclasses, and date values into JSON-safe values."""

    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if is_dataclass(obj) and not isinstance(obj, type):
        return jsonable(asdict(obj))
    if isinstance(obj, Mapping):
        return {str(key): jsonable(value) for key, value in obj.items()}
    if isinstance(obj, list | tuple | set | frozenset):
        return [jsonable(item) for item in obj]
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    return obj


def redact_sensitive(obj: Any) -> Any:
    """Mask API-key/token-shaped values anywhere in a dict/list structure."""

    if isinstance(obj, Mapping):
        redacted: dict[str, Any] = {}
        for key, value in obj.items():
            text_key = str(key)
            if text_key.lower() in SENSITIVE_KEYS:
                redacted[text_key] = "<REDACTED>"
            else:
                redacted[text_key] = redact_sensitive(value)
        return redacted
    if isinstance(obj, list | tuple):
        return [redact_sensitive(item) for item in obj]
    return obj


def debug_error(exc: BaseException) -> dict[str, Any]:
    """Turn an exception into a structured, redacted dict for the debug UI.

    Every error carries ``type``/``message``/``traceback``. Package
    exceptions (``KrHeritageError`` subclasses) additionally carry
    provider-shaped fields (``failure_kind``/``retryable``/``status_code``/
    ``result_code``) so the Validation Errors and Debug Trace tabs can show
    more than a single flattened string.
    """

    payload: dict[str, Any] = {
        "type": exc.__class__.__name__,
        "message": str(exc),
        "traceback": "".join(
            _traceback.format_exception(type(exc), exc, exc.__traceback__)
        )[-_TRACEBACK_CHAR_LIMIT:],
    }
    if isinstance(exc, ApiErrorResponse):
        payload.update(
            {
                "failure_kind": "api_error",
                "result_code": exc.code,
                "retryable": False,
            }
        )
    elif isinstance(exc, PayloadParseError):
        payload.update(
            {
                "failure_kind": "parse",
                "reason": exc.reason,
                "length": exc.length,
                "retryable": False,
            }
        )
    elif isinstance(exc, RateLimitError):
        payload.update({"failure_kind": "rate_limit", "retryable": True})
    elif isinstance(exc, TransportError):
        match = _HTTP_STATUS_RE.search(str(exc))
        status_code = int(match.group(1)) if match else None
        payload.update(
            {
                "failure_kind": "transport",
                "status_code": status_code,
                "retryable": status_code is None or status_code >= 500,
            }
        )
    elif isinstance(exc, ConfigError):
        payload.update({"failure_kind": "config", "retryable": False})
    elif isinstance(exc, KrHeritageError):
        payload.update({"failure_kind": "unknown", "retryable": None})
    return cast(dict[str, Any], redact_sensitive(payload))


def save_fixture(
    *,
    base_dir: str | PathLike[str],
    function_name: str,
    case_name: str,
    description: str,
    input_data: Any,
    request_data: Any,
    response_data: Any,
    parsed_result: Any,
    processed_result: Any,
    assertion: Mapping[str, Any] | None = None,
    library_version: str | None = None,
    overwrite: bool = False,
) -> Path:
    """Save one debug run as a pytest-replayable fixture JSON file."""

    safe_case_name = slugify_case_name(case_name)
    fixture_dir = Path(base_dir) / function_name
    fixture_dir.mkdir(parents=True, exist_ok=True)
    fixture_path = fixture_dir / f"{safe_case_name}.json"
    if fixture_path.exists() and not overwrite:
        raise FileExistsError(f"Fixture already exists: {fixture_path}")

    fixture = {
        "name": safe_case_name,
        "function": function_name,
        "description": description,
        "input": redact_sensitive(jsonable(input_data)),
        "request": redact_sensitive(jsonable(request_data)),
        "response": redact_sensitive(jsonable(response_data)),
        "parsed": jsonable(parsed_result),
        "processed": jsonable(processed_result),
        "assertion": dict(assertion or DEFAULT_ASSERTION),
        "meta": {
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(),
            "library_version": library_version,
            "source": "debug_ui",
        },
    }
    with fixture_path.open("w", encoding="utf-8") as handle:
        json.dump(fixture, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return fixture_path


def slugify_case_name(value: str) -> str:
    """Loosely normalize a case name so it is safe to use as a filename."""

    cleaned = value.strip().lower()
    slug = re.sub(r"[^\w.-]+", "-", cleaned, flags=re.UNICODE)
    slug = re.sub(r"-{2,}", "-", slug).strip("-._")
    return slug or "case"
