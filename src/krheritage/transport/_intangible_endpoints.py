from __future__ import annotations

DATA_GO_KR_SERVICE_ID = "1550246"
INTANGIBLE_ENDPOINTS: dict[str, tuple[str, str]] = {
    "records_photo": ("recordImageView", "recordImageList"),
    "sound_collection": ("soundFdView", "soundFdList"),
    "workshop_list": ("wshopFdView", "wshopFdList"),
}


def intangible_path(name: str) -> str:
    view, list_name = INTANGIBLE_ENDPOINTS[name]
    return f"/{DATA_GO_KR_SERVICE_ID}/{view}/{list_name}"

