from __future__ import annotations

import warnings

URL_ALIASES: dict[str, str] = {
    "https://apis.data.go.kr/1550246/recodeImageView": (
        "https://apis.data.go.kr/1550246/recordImageView"
    ),
    "http://apis.data.go.kr/1550246/recodeImageView": (
        "https://apis.data.go.kr/1550246/recordImageView"
    ),
}


def resolve(url: str) -> str:
    """Resolve known moved endpoints and warn on legacy URLs."""

    replacement = URL_ALIASES.get(url)
    if replacement is None:
        return url
    warnings.warn(
        f"Endpoint moved: {url} -> {replacement}",
        DeprecationWarning,
        stacklevel=2,
    )
    return replacement

