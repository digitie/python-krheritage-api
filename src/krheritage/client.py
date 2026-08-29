from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Any

from krheritage.catalog import EndpointCatalogRow, get_api_catalog_entry
from krheritage.config import HeritageConfig
from krheritage.debug import DebugRun, debug_error, redact_sensitive
from krheritage.models import HeritageDetail, HeritageSummary
from krheritage.services import EventService, GisService, HeritageDetailService, SearchService
from krheritage.services._payload import (
    clean_html_text,
    heritage_model_mapping,
    result_items,
    unwrap_result,
)
from krheritage.transport import SyncHttpxTransport, parse_payload

_DEBUG_MODEL_REGISTRY: dict[str, type[HeritageSummary]] = {
    "HeritageSummary": HeritageSummary,
    "HeritageDetail": HeritageDetail,
}


class HeritageClient:
    """Synchronous facade for Korea Heritage open data services."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        cache_dir: str | None = None,
        max_rps: float | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.config = HeritageConfig.from_env(
            api_key=api_key,
            cache_dir=cache_dir,
            max_rps=max_rps,
        )
        self._transport = SyncHttpxTransport(self.config, timeout=timeout)
        self.search = SearchService(
            transport=self._transport,
            base_url=self.config.heritage_base_url,
        )
        self.heritage = HeritageDetailService(search=self.search)
        self.event = EventService(
            transport=self._transport,
            base_url=self.config.heritage_base_url,
        )
        self.gis = GisService(
            transport=self._transport,
            base_url=self.config.gis_base_url,
        )
        self.closed = False

    def __enter__(self) -> HeritageClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._transport.close()
        self.closed = True

    def debug_fetch(
        self,
        entry_id: str,
        params: Mapping[str, Any] | None = None,
        *,
        custom_path: str = "",
    ) -> DebugRun:
        """Run any :mod:`krheritage.catalog` entry and capture full request/response detail.

        This is the single generic entry point the Streamlit debug UI (and
        fixture recording) use to call *any* catalog row — routing is driven
        entirely by fields on the resolved ``EndpointCatalogRow``
        (``base_url_attr``/``path``/``response_format``/``model_hint``/
        ``requires_custom_path``), never by comparing ``entry_id`` strings.
        """

        entry = get_api_catalog_entry(entry_id)
        request_params = dict(params or {})
        input_data = redact_sensitive(
            {"entry_id": entry_id, "params": request_params, "custom_path": custom_path}
        )
        catalog_snapshot = entry.asdict()
        trace: list[str] = [
            f"catalog lookup: {entry.id} ({entry.dataset_name})",
            f"gateway={entry.gateway} path={entry.path}",
        ]

        try:
            url = _resolve_debug_url(entry, self.config, custom_path=custom_path)
        except ValueError as exc:
            trace.append(f"URL resolution failed: {exc}")
            return DebugRun(
                function="debug_fetch",
                input=input_data,
                request={},
                response={},
                parsed=None,
                processed=None,
                trace=trace,
                error=debug_error(exc),
                catalog=catalog_snapshot,
            )

        outgoing_params = dict(request_params)
        if entry.credential_param and self.config.api_key:
            outgoing_params.setdefault(entry.credential_param, self.config.api_key)
        request_info = {
            "method": "GET",
            "url": url,
            "params": redact_sensitive(outgoing_params),
        }
        trace.append(f"request URL: {url}")

        try:
            body = self._transport.get(url, params=outgoing_params or None)
        except Exception as exc:  # transport/rate-limit failures before any response exists
            trace.append(f"request failed: {exc.__class__.__name__}")
            return DebugRun(
                function="debug_fetch",
                input=input_data,
                request=request_info,
                response={},
                parsed=None,
                processed=None,
                trace=trace,
                error=debug_error(exc),
                catalog=catalog_snapshot,
            )
        trace.append(f"response received: {len(body)} bytes")

        if entry.response_format == "html":
            raw_payload: Any = {"html": body.decode("utf-8", errors="replace")}
            response_info = {"status_code": 200, "headers": {}, "body": raw_payload}
            return DebugRun(
                function="debug_fetch",
                input=input_data,
                request=request_info,
                response=response_info,
                parsed=raw_payload,
                processed=raw_payload,
                trace=trace,
                catalog=catalog_snapshot,
            )

        try:
            raw_payload = parse_payload(body)
        except Exception as exc:
            trace.append(f"payload parse failed: {exc.__class__.__name__}")
            return DebugRun(
                function="debug_fetch",
                input=input_data,
                request=request_info,
                response={"status_code": 200, "headers": {}, "body": None},
                parsed=None,
                processed=None,
                trace=trace,
                error=debug_error(exc),
                catalog=catalog_snapshot,
            )
        response_info = {"status_code": 200, "headers": {}, "body": raw_payload}

        try:
            result = unwrap_result(raw_payload)
        except Exception as exc:
            trace.append(f"provider returned an error envelope: {exc.__class__.__name__}")
            return DebugRun(
                function="debug_fetch",
                input=input_data,
                request=request_info,
                response=response_info,
                parsed=None,
                processed=None,
                trace=trace,
                error=debug_error(exc),
                catalog=catalog_snapshot,
            )

        rows = _debug_rows(result)
        trace.append(f"extracted {len(rows)} row(s)")

        parsed_payload: Any = raw_payload
        validation_errors: list[dict[str, Any]] = []
        model_cls = _DEBUG_MODEL_REGISTRY.get(entry.model_hint or "")
        if model_cls is not None:
            models: list[dict[str, Any]] = []
            for index, row in enumerate(rows):
                try:
                    models.append(_validate_heritage_row(model_cls, row).model_dump(mode="json"))
                except Exception as exc:
                    validation_errors.append({"row_index": index, **debug_error(exc)})
            parsed_payload = models
            trace.append(
                f"{entry.model_hint} validation: {len(models)} ok, "
                f"{len(validation_errors)} failed"
            )

        return DebugRun(
            function="debug_fetch",
            input=input_data,
            request=request_info,
            response=response_info,
            parsed=parsed_payload,
            processed=rows,
            trace=trace,
            validation_errors=tuple(validation_errors),
            catalog=catalog_snapshot,
        )

    @classmethod
    def aio(
        cls,
        *,
        api_key: str | None = None,
        cache_dir: str | None = None,
        max_rps: float | None = None,
    ) -> AsyncHeritageClient:
        return AsyncHeritageClient(api_key=api_key, cache_dir=cache_dir, max_rps=max_rps)


class AsyncHeritageClient:
    """Asynchronous facade placeholder for service-layer expansion."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        cache_dir: str | None = None,
        max_rps: float | None = None,
    ) -> None:
        raise NotImplementedError(
            "AsyncHeritageClient has no async service layer yet; use HeritageClient instead."
        )

    async def __aenter__(self) -> AsyncHeritageClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        self.closed = True


def _resolve_debug_url(
    entry: EndpointCatalogRow,
    config: HeritageConfig,
    *,
    custom_path: str,
) -> str:
    """Build a request URL purely from catalog fields (no id comparisons)."""

    if entry.requires_custom_path:
        path = custom_path.strip()
        if not path:
            raise ValueError(f"{entry.id} requires a custom path or URL")
        if path.startswith(("http://", "https://")):
            return path
        return _join_url(config.data_go_kr_base_url, path)
    if entry.base_url_attr == "absolute":
        return entry.path
    base_url = getattr(config, entry.base_url_attr)
    return _join_url(str(base_url), entry.path)


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _debug_rows(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract row dicts from a parsed ``result`` node, uniformly for every entry.

    Mirrors ``SearchService``'s own detail-payload handling: when there is
    exactly one item, scalar fields living at the ``result`` level (e.g. a
    detail endpoint's composite key) are merged into it so nothing gets
    silently dropped.
    """

    items = result_items(result)
    if not items:
        return [dict(result)] if result else []
    if len(items) == 1:
        scalar_fields = {
            key: value
            for key, value in result.items()
            if not isinstance(value, Mapping | list | tuple)
        }
        return [{**scalar_fields, **items[0]}]
    return [dict(item) for item in items]


def _validate_heritage_row(
    model_cls: type[HeritageSummary],
    row: dict[str, Any],
) -> HeritageSummary:
    payload = heritage_model_mapping(row)
    if "content" in payload:
        content = payload.get("content")
        payload["content_html"] = str(content) if content not in (None, "") else None
        payload["content"] = clean_html_text(content)
    return model_cls.model_validate(payload)
