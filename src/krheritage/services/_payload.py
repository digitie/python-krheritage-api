from __future__ import annotations

import re
from collections.abc import Mapping
from html import unescape
from typing import Any

from krheritage.exceptions import ApiErrorResponse
from krheritage.transport import parse_payload


def parsed_result(content: bytes) -> Mapping[str, Any]:
    return unwrap_result(parse_payload(content))


def unwrap_result(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Raise on a provider error envelope, then return the ``result`` node.

    Split out from :func:`parsed_result` so callers that already hold a
    parsed payload (e.g. the debug UI's raw-response inspector) can reuse
    the same error-envelope check without re-parsing the response bytes.
    """

    _raise_for_error_envelope(payload)
    result = payload.get("result", payload)
    return result if isinstance(result, Mapping) else {"items": result}


def _raise_for_error_envelope(payload: Mapping[str, Any]) -> None:
    candidates = [payload]
    if len(payload) == 1:
        nested = next(iter(payload.values()))
        if isinstance(nested, Mapping):
            candidates.append(nested)
    for node in candidates:
        header = node.get("cmmMsgHeader")
        if isinstance(header, Mapping) and header.get("returnAuthMsg"):
            code = str(header.get("returnReasonCode") or header["returnAuthMsg"])
            message = str(header.get("errMsg") or header["returnAuthMsg"])
            raise ApiErrorResponse(code=code, message=message, payload=dict(payload))
        message_obj = node.get("message")
        if isinstance(message_obj, Mapping) and _is_error_code(message_obj.get("code")):
            code = str(message_obj.get("code"))
            message = str(message_obj.get("text") or message_obj.get("msg") or code)
            raise ApiErrorResponse(code=code, message=message, payload=dict(payload))


def _is_error_code(code: Any) -> bool:
    try:
        return int(str(code).strip()) >= 400
    except (TypeError, ValueError):
        return False


def result_items(result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    value = (
        result.get("item")
        or result.get("items")
        or result.get("list")
        or result.get("data")
        or result.get("row")
    )
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list | tuple):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def int_value(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def clean_html_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() or None


def heritage_model_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    mapped = dict(raw)
    mapped.setdefault(
        "key",
        {
            "ccbaKdcd": raw.get("ccbaKdcd") or raw.get("ccba_kdcd"),
            "ccbaAsno": raw.get("ccbaAsno") or raw.get("ccba_asno"),
            "ccbaCtcd": raw.get("ccbaCtcd") or raw.get("ccba_ctcd"),
        },
    )
    return mapped
