from __future__ import annotations

import asyncio
from pathlib import Path


async def write_bytes(dest: Path, content: bytes) -> Path:
    return await asyncio.to_thread(_write_bytes, dest, content)


def _write_bytes(dest: Path, content: bytes) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return dest

