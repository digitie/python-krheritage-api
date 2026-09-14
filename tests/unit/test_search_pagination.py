"""Termination rules for ``SearchService.iter_pages``.

A page comes back short for two very different reasons: upstream ran out of
rows, or a full upstream page lost rows to row-level validation. Only the
declared ``total`` tells them apart, and guessing wrong truncates the
caller's data without ever raising.
"""

from __future__ import annotations

from typing import Any

from krheritage.models import PaginatedResult
from krheritage.services.search import SearchService


class _StubSearchService(SearchService):
    """Drives ``iter_pages`` off canned pages instead of a transport."""

    def __init__(self, pages: list[PaginatedResult[Any]]) -> None:
        self._pages = pages
        self.requested: list[int] = []

    async def list(self, *, page_size: int = 100, page: int = 1, **_filters: Any) -> Any:
        self.requested.append(page)
        return self._pages[page - 1]


def _page(count: int, *, total: int, page_no: int, size: int) -> PaginatedResult[Any]:
    return PaginatedResult(
        total=total,
        page=page_no,
        size=size,
        items=[object() for _ in range(count)],
    )


async def test_a_filtered_full_page_does_not_end_the_stream() -> None:
    # 30 rows upstream, 10 per page, page 1 lost one row to validation.
    service = _StubSearchService(
        [
            _page(9, total=30, page_no=1, size=10),
            _page(10, total=30, page_no=2, size=10),
            _page(10, total=30, page_no=3, size=10),
        ]
    )

    pages = [item async for item in service.iter_pages(page_size=10)]

    assert service.requested == [1, 2, 3]
    assert sum(len(page.items) for page in pages) == 29


async def test_a_short_page_that_accounts_for_the_total_ends_the_stream() -> None:
    service = _StubSearchService(
        [
            _page(10, total=14, page_no=1, size=10),
            _page(4, total=14, page_no=2, size=10),
        ]
    )

    pages = [item async for item in service.iter_pages(page_size=10)]

    assert service.requested == [1, 2]
    assert sum(len(page.items) for page in pages) == 14


async def test_without_a_total_an_empty_page_ends_the_stream() -> None:
    service = _StubSearchService(
        [
            _page(9, total=0, page_no=1, size=10),
            _page(9, total=0, page_no=2, size=10),
            _page(0, total=0, page_no=3, size=10),
        ]
    )

    pages = [item async for item in service.iter_pages(page_size=10)]

    assert service.requested == [1, 2, 3]
    assert sum(len(page.items) for page in pages) == 18


async def test_max_pages_still_caps_the_walk() -> None:
    service = _StubSearchService(
        [
            _page(9, total=100, page_no=1, size=10),
            _page(9, total=100, page_no=2, size=10),
            _page(9, total=100, page_no=3, size=10),
        ]
    )

    [item async for item in service.iter_pages(page_size=10, max_pages=2)]

    assert service.requested == [1, 2]
