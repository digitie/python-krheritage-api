from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """Small Python 3.10-compatible StrEnum replacement."""

    def __str__(self) -> str:
        return str(self.value)
