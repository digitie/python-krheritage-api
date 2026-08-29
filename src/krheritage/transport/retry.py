from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from krheritage.exceptions import TransportError


def _is_retryable(exc: BaseException) -> bool:
    if not isinstance(exc, TransportError):
        return False
    cause = exc.__cause__
    if isinstance(cause, httpx.HTTPStatusError):
        status_code = cause.response.status_code
        return status_code == 429 or status_code >= 500
    return True


retry_transport = retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)

