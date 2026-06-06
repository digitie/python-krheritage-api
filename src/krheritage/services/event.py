from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from krheritage.models import HeritageEvent, PaginatedResult
from krheritage.services._payload import int_value, parsed_result, result_items
from krheritage.transport import SyncTransport


@dataclass(slots=True)
class EventService:
    """Public 국가유산 event service."""

    transport: SyncTransport
    base_url: str

    def by_month(self, *, year: int, month: int) -> tuple[HeritageEvent, ...]:
        params = {
            "searchYear": f"{year:04d}",
            "searchMonth": f"{month:02d}",
        }
        result = parsed_result(
            self.transport.get(
                f"{self.base_url}/openapi/selectEventListOpenapi.do",
                params=params,
            )
        )
        return tuple(
            HeritageEvent.model_validate(_event_mapping(item)) for item in result_items(result)
        )

    def list(self, *, year: int, month: int) -> PaginatedResult[HeritageEvent]:
        items = list(self.by_month(year=year, month=month))
        return PaginatedResult[HeritageEvent](
            total=len(items),
            page=1,
            size=len(items) or 1,
            items=items,
        )

    def iter_months(
        self,
        *,
        search_year: int | str | None = None,
        search_month: int | str | None = None,
        months_back: int | str = 1,
        months_ahead: int | str = 12,
        today: date | None = None,
        **_unused: Any,
    ) -> Iterator[HeritageEvent]:
        if search_year is not None or search_month is not None:
            year = int_value(search_year, date.today().year)
            month = int_value(search_month, date.today().month)
            yield from self.by_month(year=year, month=month)
            return

        anchor = today or date.today()
        start = _month_offset(anchor.year, anchor.month, -int_value(months_back, 1))
        total_months = int_value(months_back, 1) + int_value(months_ahead, 12) + 1
        for offset in range(total_months):
            year, month = _month_offset(start[0], start[1], offset)
            yield from self.by_month(year=year, month=month)


def _event_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    mapped = dict(raw)
    if "subTitle" not in mapped and "subTitle1" in mapped:
        mapped["subTitle"] = mapped.get("subTitle1")
    if "title" not in mapped:
        mapped["title"] = mapped.get("subTitle") or mapped.get("subTitle1")
    # 원천 payload를 보존한다 (intangible/legacy/research 모델과 동일 컨벤션 —
    # 다운스트림 source_records.raw_data 적재용).
    mapped["raw"] = dict(raw)
    return mapped


def _month_offset(year: int, month: int, offset: int) -> tuple[int, int]:
    zero_based = (year * 12) + (month - 1) + offset
    return zero_based // 12, (zero_based % 12) + 1
