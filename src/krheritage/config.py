from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from krheritage.exceptions import ConfigError

_platform_user_cache_path: Callable[..., Path] | None
try:
    from platformdirs import user_cache_path as _imported_user_cache_path
except ImportError:  # pragma: no cover - dependency fallback for bare source imports
    _platform_user_cache_path = None
else:
    _platform_user_cache_path = _imported_user_cache_path


DEFAULT_HERITAGE_BASE_URL = "https://www.khs.go.kr/cha"
DEFAULT_GIS_BASE_URL = "https://gis-heritage.go.kr/openapi"
DEFAULT_DATA_GO_KR_BASE_URL = "https://apis.data.go.kr"
DEFAULT_MAX_RPS = 5.0


@dataclass(frozen=True, slots=True)
class HeritageConfig:
    """Runtime configuration loaded from explicit args and environment variables."""

    api_key: str | None
    cache_dir: Path
    max_rps: float
    heritage_base_url: str = DEFAULT_HERITAGE_BASE_URL
    gis_base_url: str = DEFAULT_GIS_BASE_URL
    data_go_kr_base_url: str = DEFAULT_DATA_GO_KR_BASE_URL

    @classmethod
    def from_env(
        cls,
        *,
        api_key: str | None = None,
        cache_dir: str | Path | None = None,
        max_rps: float | str | None = None,
    ) -> HeritageConfig:
        resolved_api_key = api_key if api_key is not None else os.getenv("DATA_GO_KR_SERVICE_KEY")
        resolved_cache_dir = Path(
            cache_dir
            if cache_dir is not None
            else os.getenv("KHERITAGE_CACHE_DIR")
            or _default_cache_dir()
        )
        resolved_max_rps = _resolve_max_rps(
            max_rps if max_rps is not None else os.getenv("KHERITAGE_MAX_RPS")
        )
        return cls(
            api_key=resolved_api_key or None,
            cache_dir=resolved_cache_dir.expanduser(),
            max_rps=resolved_max_rps,
        )


def _resolve_max_rps(value: float | str | None) -> float:
    if value is None or value == "":
        return DEFAULT_MAX_RPS
    try:
        max_rps = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError("KHERITAGE_MAX_RPS must be a positive number") from exc
    if max_rps <= 0:
        raise ConfigError("KHERITAGE_MAX_RPS must be greater than 0")
    return max_rps


def _default_cache_dir() -> Path:
    if _platform_user_cache_path is None:
        return Path.home() / ".cache" / "python-krheritage-api"
    return _platform_user_cache_path("python-krheritage-api", "digitie")
