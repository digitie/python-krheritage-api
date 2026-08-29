from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from krheritage.models import HeritageDetail, HeritageSummary, PaginatedResult
from krheritage.services._payload import (
    clean_html_text,
    heritage_model_mapping,
    int_value,
    parsed_result,
    result_items,
)
from krheritage.transport import SyncTransport

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SearchService:
    """Public 국가유산 search/detail service."""

    transport: SyncTransport
    base_url: str

    def list(
        self,
        *,
        page_size: int = 100,
        page: int = 1,
        ccba_kdcd: str | None = None,
        ccba_ctcd: str | None = None,
        ccba_asno: str | None = None,
        st_ccba_asdt: str | int | None = None,
        st_ccba_aedt: str | int | None = None,
        ccba_cndt: str | int | None = None,
        ccba_mnm1: str | None = None,
    ) -> PaginatedResult[HeritageSummary]:
        params = _without_none(
            {
                "pageUnit": page_size,
                "pageIndex": page,
                "ccbaKdcd": ccba_kdcd,
                "ccbaCtcd": ccba_ctcd,
                "ccbaAsno": ccba_asno,
                "stCcbaAsdt": st_ccba_asdt,
                "stCcbaAedt": st_ccba_aedt,
                "ccbaCndt": ccba_cndt,
                "ccbaMnm1": ccba_mnm1,
            }
        )
        result = parsed_result(
            self.transport.get(f"{self.base_url}/SearchKindOpenapiList.do", params=params)
        )
        items = [
            HeritageSummary.model_validate(heritage_model_mapping(item))
            for item in result_items(result)
        ]
        return PaginatedResult[HeritageSummary](
            total=int_value(result.get("totalCnt"), len(items)),
            page=int_value(result.get("pageIndex"), page),
            size=int_value(result.get("pageUnit"), page_size),
            items=items,
        )

    def details(
        self,
        ccba_kdcd: str,
        ccba_asno: str,
        ccba_ctcd: str,
    ) -> HeritageDetail:
        params = {
            "ccbaKdcd": ccba_kdcd,
            "ccbaAsno": ccba_asno,
            "ccbaCtcd": ccba_ctcd,
        }
        result = parsed_result(
            self.transport.get(f"{self.base_url}/SearchKindOpenapiDt.do", params=params)
        )
        raw = _first_item_or_result(result)
        mapped = heritage_model_mapping(raw)
        content = raw.get("content")
        # content_html is the provider's raw, unsanitized HTML — callers must
        # sanitize it (e.g. with bleach) before rendering; never inject it
        # directly into a page (XSS risk).
        mapped["content_html"] = str(content) if content not in (None, "") else None
        mapped["content"] = clean_html_text(content)
        return HeritageDetail.model_validate(mapped)

    def iter_pages(
        self,
        *,
        page_size: int = 100,
        max_pages: int | None = None,
        **filters: Any,
    ) -> Iterator[PaginatedResult[HeritageSummary]]:
        page = 1
        while True:
            result = self.list(page_size=page_size, page=page, **filters)
            if not result.items:
                return
            yield result
            if max_pages is not None and page >= max_pages:
                return
            if len(result.items) < page_size:
                return
            page += 1

    def iter_all_details(
        self,
        *,
        page_size: int = 100,
        max_pages: int | None = None,
        **filters: Any,
    ) -> Iterator[HeritageDetail]:
        accepted_filters = {
            key: filters[key]
            for key in (
                "ccba_kdcd",
                "ccba_ctcd",
                "ccba_asno",
                "st_ccba_asdt",
                "st_ccba_aedt",
                "ccba_cndt",
                "ccba_mnm1",
            )
            if key in filters
        }
        for page in self.iter_pages(
            page_size=page_size,
            max_pages=max_pages,
            **accepted_filters,
        ):
            for summary in page.items:
                ccba_kdcd = summary.key.ccba_kdcd
                ccba_asno = summary.key.ccba_asno
                ccba_ctcd = summary.key.ccba_ctcd
                if not ccba_kdcd or not ccba_asno or not ccba_ctcd:
                    # detail 조회는 복합키 3요소가 모두 있어야 가능하다 — 결측
                    # row는 조용히 버리지 않고 식별 정보와 함께 경고를 남긴다.
                    logger.warning(
                        "Skipping heritage list row without a complete composite key: "
                        "ccbaKdcd=%r, ccbaAsno=%r, ccbaCtcd=%r, ccbaMnm1=%r (page=%s)",
                        ccba_kdcd,
                        ccba_asno,
                        ccba_ctcd,
                        summary.name_ko,
                        page.page,
                    )
                    continue
                yield self.details(ccba_kdcd, ccba_asno, ccba_ctcd)


def _first_item_or_result(result: Mapping[str, Any]) -> dict[str, Any]:
    items = result_items(result)
    if not items:
        return dict(result)
    # live SearchKindOpenapiDt 응답은 복합키(ccbaKdcd/ccbaAsno/ccbaCtcd)와
    # longitude/latitude를 <result> 레벨에만 두고 본문은 <item>에 중첩하므로,
    # result 레벨 leaf 필드를 먼저 깔고 item 필드로 덮어쓴다.
    merged: dict[str, Any] = {
        key: value
        for key, value in result.items()
        if not isinstance(value, Mapping | list | tuple)
    }
    merged.update(items[0])
    return merged


def _without_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}
