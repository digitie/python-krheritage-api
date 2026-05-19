from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree as stdlib_etree

try:
    from lxml import etree as lxml_etree
except ImportError:  # pragma: no cover - depends on local optional wheel availability
    lxml_etree = None


def parse_payload(content: bytes, content_type: str | None = None) -> dict[str, Any]:
    """Parse JSON or XML response bytes into a normalized dictionary."""

    if _is_json(content, content_type):
        loaded = json.loads(content.decode("utf-8-sig"))
        return dict(loaded) if isinstance(loaded, Mapping) else {"items": loaded}
    return xml_to_dict(content)


def xml_to_dict(content: bytes) -> dict[str, Any]:
    if lxml_etree is not None:
        parser = lxml_etree.XMLParser(recover=True, resolve_entities=False)
        root = lxml_etree.fromstring(content, parser=parser)
    else:
        root = stdlib_etree.fromstring(content)
    return {root.tag: _element_to_value(root)}


def _element_to_value(element: Any) -> Any:
    children = list(element)
    text = (element.text or "").strip()
    if not children:
        return text

    grouped: dict[str, Any] = {}
    for child in children:
        value = _element_to_value(child)
        existing = grouped.get(child.tag)
        if existing is None:
            grouped[child.tag] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            grouped[child.tag] = [existing, value]
    return grouped


def _is_json(content: bytes, content_type: str | None) -> bool:
    if content_type and "json" in content_type.lower():
        return True
    stripped = content.lstrip()
    return stripped.startswith(b"{") or stripped.startswith(b"[")
