from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class KrHeritageModel(BaseModel):
    """Base Pydantic model for provider payloads."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        arbitrary_types_allowed=False,
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


T = TypeVar("T")


class PaginatedResult(KrHeritageModel, Generic[T]):
    """Uniform container for list/search responses."""

    total: int = 0
    page: int = 1
    size: int = 10
    items: list[T] = Field(default_factory=list)

    def __iter__(self) -> Iterator[T]:  # type: ignore[override]
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def extend(self, items: Sequence[T]) -> None:
        self.items.extend(items)
