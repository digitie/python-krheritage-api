from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class TokenBucket:
    """Async token bucket rate limiter."""

    max_rps: float = 5.0
    capacity: float | None = None
    _tokens: float = field(init=False)
    _updated_at: float = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        if self.max_rps <= 0:
            raise ValueError("max_rps must be greater than 0")
        self.capacity = self.max_rps if self.capacity is None else self.capacity
        self._tokens = self.capacity
        self._updated_at = time.monotonic()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_for = (1 - self._tokens) / self.max_rps
            await asyncio.sleep(wait_for)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated_at
        self._updated_at = now
        assert self.capacity is not None
        self._tokens = min(self.capacity, self._tokens + elapsed * self.max_rps)


@dataclass(slots=True)
class SyncTokenBucket:
    """Blocking token bucket rate limiter."""

    max_rps: float = 5.0
    capacity: float | None = None
    _tokens: float = field(init=False)
    _updated_at: float = field(init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        if self.max_rps <= 0:
            raise ValueError("max_rps must be greater than 0")
        self.capacity = self.max_rps if self.capacity is None else self.capacity
        self._tokens = self.capacity
        self._updated_at = time.monotonic()

    def acquire(self) -> None:
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_for = (1 - self._tokens) / self.max_rps
            time.sleep(wait_for)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated_at
        self._updated_at = now
        assert self.capacity is not None
        self._tokens = min(self.capacity, self._tokens + elapsed * self.max_rps)

