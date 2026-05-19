from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from krheritage.models import HeritageDetail
from krheritage.services.search import SearchService


@dataclass(slots=True)
class HeritageDetailService:
    """Detail-focused facade over the public search endpoints."""

    search: SearchService

    def details(
        self,
        ccba_kdcd: str,
        ccba_asno: str,
        ccba_ctcd: str,
    ) -> HeritageDetail:
        return self.search.details(ccba_kdcd, ccba_asno, ccba_ctcd)

    def iter_all_details(
        self,
        *,
        page_size: int = 100,
        max_pages: int | None = None,
        **filters: Any,
    ) -> Iterator[HeritageDetail]:
        return self.search.iter_all_details(
            page_size=page_size,
            max_pages=max_pages,
            **filters,
        )
