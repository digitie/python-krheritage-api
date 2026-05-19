from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class KrHeritageError(Exception):
    """Base exception for all krheritage errors."""


class ConfigError(KrHeritageError, ValueError):
    """Raised when runtime configuration is invalid."""


class TransportError(KrHeritageError):
    """Raised when HTTP transport fails before an API response is parsed."""


class RateLimitError(TransportError):
    """Raised when local rate limiting cannot schedule a request."""


@dataclass(slots=True)
class ApiErrorResponse(KrHeritageError):
    """Raised when a provider returns an explicit error payload."""

    code: str
    message: str
    payload: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

