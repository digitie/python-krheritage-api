from __future__ import annotations

from typing import Any, Protocol
from urllib.parse import quote

import httpx

from krheritage._httpx import send_after_token
from krheritage._ratelimit import AsyncTokenBucket
from krheritage.config import HeritageConfig
from krheritage.exceptions import TransportError
from krheritage.transport._aliases import resolve
from krheritage.transport.retry import retry_transport


class Transport(Protocol):
    async def get(self, url: str, params: dict[str, Any] | None = None) -> bytes: ...

    async def aclose(self) -> None: ...


_MAX_RESPONSE_BYTES = 50 * 1024 * 1024


def _redacted_status_message(exc: httpx.HTTPStatusError) -> str:
    safe_url = exc.request.url.copy_remove_param("serviceKey")
    return f"HTTP {exc.response.status_code} error for url '{safe_url}'"


class AsyncHttpxTransport:
    """httpx-backed asynchronous transport with aliases, retry, and rate limiting."""

    def __init__(
        self,
        config: HeritageConfig,
        *,
        timeout: float = 30.0,
        rate_limiter: AsyncTokenBucket | None = None,
        session: httpx.AsyncClient | None = None,
    ) -> None:
        self.rate_limiter = (
            rate_limiter if rate_limiter is not None else AsyncTokenBucket(config.max_rps)
        )
        if session is not None and not isinstance(session, httpx.AsyncClient):
            raise TypeError("session must be httpx.AsyncClient")
        self._owns_client = session is None
        self._client = (
            session
            if session is not None
            else httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        )
        self._closed = False
        self._api_key = config.api_key

    @retry_transport
    async def get(self, url: str, params: dict[str, Any] | None = None) -> bytes:
        if self._closed:
            raise RuntimeError("HeritageClient is closed")
        await self.rate_limiter.acquire()
        resolved_url = resolve(url)
        request_params = _with_service_key(resolved_url, params, self._api_key)
        try:
            request = self._client.build_request("GET", resolved_url, params=request_params)
            response = await send_after_token(self._client, request, self.rate_limiter, stream=True)
            try:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length is not None and int(content_length) > _MAX_RESPONSE_BYTES:
                    raise TransportError(
                        f"response body exceeds {_MAX_RESPONSE_BYTES} byte limit", retryable=False
                    )
                chunks = bytearray()
                async for chunk in response.aiter_bytes():
                    chunks += chunk
                    if len(chunks) > _MAX_RESPONSE_BYTES:
                        raise TransportError(
                            f"response body exceeds {_MAX_RESPONSE_BYTES} byte limit",
                            retryable=False,
                        )
                content = bytes(chunks)
            finally:
                await response.aclose()
        except httpx.HTTPStatusError as exc:
            raise TransportError(
                self._redact(_redacted_status_message(exc)), status_code=exc.response.status_code
            ) from None
        except httpx.HTTPError as exc:
            raise TransportError(self._redact(str(exc))) from None
        return content

    def _redact(self, text: str) -> str:
        if not self._api_key:
            return text
        return text.replace(self._api_key, "<REDACTED>").replace(
            quote(self._api_key, safe=""), "<REDACTED>"
        )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_client:
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
