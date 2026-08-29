from __future__ import annotations

from types import TracebackType

from krheritage.config import HeritageConfig
from krheritage.services import EventService, GisService, HeritageDetailService, SearchService
from krheritage.transport import SyncHttpxTransport


class HeritageClient:
    """Synchronous facade for Korea Heritage open data services."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        cache_dir: str | None = None,
        max_rps: float | None = None,
    ) -> None:
        self.config = HeritageConfig.from_env(
            api_key=api_key,
            cache_dir=cache_dir,
            max_rps=max_rps,
        )
        self._transport = SyncHttpxTransport(self.config)
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
