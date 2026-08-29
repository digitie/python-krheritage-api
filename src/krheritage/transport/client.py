from __future__ import annotations

from typing import Any, Protocol

import httpx

from krheritage.config import HeritageConfig
from krheritage.exceptions import TransportError
from krheritage.transport._aliases import resolve
from krheritage.transport.ratelimit import SyncTokenBucket, TokenBucket
from krheritage.transport.retry import retry_transport


class Transport(Protocol):
    async def get(self, url: str, params: dict[str, Any] | None = None) -> bytes: ...

    async def aclose(self) -> None: ...


class SyncTransport(Protocol):
    def get(self, url: str, params: dict[str, Any] | None = None) -> bytes: ...

    def close(self) -> None: ...


_MAX_RESPONSE_BYTES = 50 * 1024 * 1024


def _redacted_status_message(exc: httpx.HTTPStatusError) -> str:
    safe_url = exc.request.url.copy_remove_param("serviceKey")
    return f"HTTP {exc.response.status_code} error for url '{safe_url}'"


class SyncHttpxTransport:
    """httpx-backed synchronous transport for public service clients."""

    def __init__(self, config: HeritageConfig) -> None:
        self._client = httpx.Client(timeout=30.0, follow_redirects=True)
        self._bucket = SyncTokenBucket(max_rps=config.max_rps)
        self._api_key = config.api_key

    @retry_transport
    def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        self._bucket.acquire()
        resolved_url = resolve(url)
        request_params = _with_service_key(resolved_url, params, self._api_key)
        try:
            with self._client.stream("GET", resolved_url, params=request_params) as response:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length is not None and int(content_length) > _MAX_RESPONSE_BYTES:
                    raise TransportError(f"response body exceeds {_MAX_RESPONSE_BYTES} byte limit")
                chunks = bytearray()
                for chunk in response.iter_bytes():
                    chunks += chunk
                    if len(chunks) > _MAX_RESPONSE_BYTES:
                        raise TransportError(
                            f"response body exceeds {_MAX_RESPONSE_BYTES} byte limit"
                        )
                content = bytes(chunks)
        except httpx.HTTPStatusError as exc:
            raise TransportError(_redacted_status_message(exc)) from None
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc
        return content

    def close(self) -> None:
        self._client.close()


class AsyncHttpxTransport:
    """httpx-backed asynchronous transport with aliases, retry, and rate limiting."""

    def __init__(self, config: HeritageConfig, *, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        self._bucket = TokenBucket(max_rps=config.max_rps)
        self._api_key = config.api_key

    @retry_transport
    async def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        await self._bucket.acquire()
        resolved_url = resolve(url)
        request_params = _with_service_key(resolved_url, params, self._api_key)
        try:
            async with self._client.stream("GET", resolved_url, params=request_params) as response:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length is not None and int(content_length) > _MAX_RESPONSE_BYTES:
                    raise TransportError(f"response body exceeds {_MAX_RESPONSE_BYTES} byte limit")
                chunks = bytearray()
                async for chunk in response.aiter_bytes():
                    chunks += chunk
                    if len(chunks) > _MAX_RESPONSE_BYTES:
                        raise TransportError(
                            f"response body exceeds {_MAX_RESPONSE_BYTES} byte limit"
                        )
                content = bytes(chunks)
        except httpx.HTTPStatusError as exc:
            raise TransportError(_redacted_status_message(exc)) from None
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc
        return content

    async def aclose(self) -> None:
        await self._client.aclose()


def _with_service_key(
    url: str,
    params: dict[str, Any] | None,
    api_key: str | None,
) -> dict[str, Any] | None:
    request_params = dict(params or {})
    if api_key and httpx.URL(url).host == "apis.data.go.kr" and "serviceKey" not in request_params:
        request_params["serviceKey"] = api_key
    return request_params or None
