from __future__ import annotations

from pathlib import Path

import pytest

from krheritage.config import DEFAULT_MAX_RPS, HeritageConfig
from krheritage.exceptions import ConfigError


def test_config_prefers_explicit_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KHERITAGE_API_KEY", "env-key")
    monkeypatch.setenv("KHERITAGE_CACHE_DIR", str(tmp_path / "env-cache"))
    monkeypatch.setenv("KHERITAGE_MAX_RPS", "9")

    config = HeritageConfig.from_env(
        api_key="explicit-key",
        cache_dir=tmp_path / "explicit-cache",
        max_rps=3,
    )

    assert config.api_key == "explicit-key"
    assert config.cache_dir == tmp_path / "explicit-cache"
    assert config.max_rps == 3


def test_config_loads_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KHERITAGE_API_KEY", "env-key")
    monkeypatch.setenv("KHERITAGE_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("KHERITAGE_MAX_RPS", "2.5")

    config = HeritageConfig.from_env()

    assert config.api_key == "env-key"
    assert config.cache_dir == tmp_path
    assert config.max_rps == 2.5


def test_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KHERITAGE_API_KEY", raising=False)
    monkeypatch.delenv("KHERITAGE_CACHE_DIR", raising=False)
    monkeypatch.delenv("KHERITAGE_MAX_RPS", raising=False)

    config = HeritageConfig.from_env()

    assert config.api_key is None
    assert "python-krheritage-api" in config.cache_dir.parts
    assert config.max_rps == DEFAULT_MAX_RPS


def test_invalid_max_rps_raises() -> None:
    with pytest.raises(ConfigError):
        HeritageConfig.from_env(max_rps="nope")

    with pytest.raises(ConfigError):
        HeritageConfig.from_env(max_rps=0)
