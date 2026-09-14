from __future__ import annotations

from typing import Any


class KrHeritageError(Exception):
    """Base exception for all krheritage errors."""


class ConfigError(KrHeritageError, ValueError):
    """Raised when runtime configuration is invalid."""


class TransportError(KrHeritageError):
    """HTTP 전송이 실패했을 때 상태와 재시도 가능 여부를 전달한다."""

    def __init__(
        self, message: str, *, status_code: int | None = None, retryable: bool = True,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class RateLimitError(TransportError):
    """Raised when local rate limiting cannot schedule a request."""


class PayloadParseError(KrHeritageError):
    """Raised when a response body cannot be parsed as JSON or XML."""

    def __init__(self, reason: str, length: int, prefix: bytes) -> None:
        super().__init__(reason, length, prefix)
        self.reason = reason
        self.length = length
        self.prefix = prefix

    def __str__(self) -> str:
        return f"{self.reason} (length={self.length}, prefix={self.prefix!r})"


class ApiErrorResponse(KrHeritageError):
    """Raised when a provider returns an explicit error payload."""

    def __init__(self, code: str, message: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(code, message)
        self.code = code
        self.message = message
        self.payload = payload

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

