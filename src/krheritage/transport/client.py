from __future__ import annotations

from typing import Any, Protocol

import httpx

from krheritage.config import HeritageConfig
from krheritage.exceptions import TransportError
from krheritage.transport._aliases import resolve
from krheritage.transport.ratelimit import TokenBucket
from krheritage.transport.retry import retry_transport


class Transport(Protocol):
    async def get(self, url: str, params: dict[str, Any] | None = None) -> bytes: ...

    async def aclose(self) -> None: ...


class SyncTransport(Protocol):
    def get(self, url: str, params: dict[str, Any] | None = None) -> bytes: ...

    def close(self) -> None: ...


class SyncHttpxTransport:
    """httpx-backed synchronous transport for public service clients."""

    def __init__(self, config: HeritageConfig) -> None:
        self._client = httpx.Client(timeout=30.0, follow_redirects=True)
        self._api_key = config.api_key

    def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        resolved_url = resolve(url)
        request_params = _with_service_key(resolved_url, params, self._api_key)
        try:
            response = self._client.get(resolved_url, params=request_params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc
        return response.content

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
            response = await self._client.get(resolved_url, params=request_params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TransportError(str(exc)) from exc
        return response.content

    async def aclose(self) -> None:
        await self._client.aclose()


def _with_service_key(
    url: str,
    params: dict[str, Any] | None,
    api_key: str | None,
) -> dict[str, Any] | None:
    request_params = dict(params or {})
    if api_key and "apis.data.go.kr" in url and "serviceKey" not in request_params:
        request_params["serviceKey"] = api_key
    return request_params or None
