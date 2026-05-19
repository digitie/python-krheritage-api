from __future__ import annotations

from pathlib import Path


async def write_bytes(dest: Path, content: bytes) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return dest

