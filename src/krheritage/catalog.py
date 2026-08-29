from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal

from krheritage.codes.lang import Lang

Gateway = Literal["khs", "gis", "nrich", "data_go_kr"]


@dataclass(frozen=True, slots=True)
class EndpointCatalogRow:
    """A UI-friendly endpoint catalog row for debug and exploration tools.

    ``required_params``/``optional_params`` are the parameter metadata the
    Streamlit debug UI uses to auto-generate its request form — no endpoint
    should ever need a hardcoded ``if entry.id == "..."`` branch to know
    which fields to render. ``param_enum`` opts a parameter into a
    ``selectbox`` backed by an existing ``codes`` Enum instead of a free-text
    input. ``requires_custom_path`` flags the one row (``data-go-kr-custom``)
    that has no fixed ``path`` and instead takes a user-supplied path/URL.
    """

    id: str
    label: str
    gateway: Gateway
    dataset_name: str
    base_url_attr: str
    path: str
    method: str = "GET"
    response_format: str = "xml"
    model_hint: str | None = None
    credential_param: str | None = None
    service_key_url: str = ""
    portal_url: str = ""
    description: str = ""
    returns: str = ""
    required_params: tuple[str, ...] = ()
    optional_params: tuple[str, ...] = ()
    param_help: dict[str, str] = field(default_factory=dict)
    param_enum: dict[str, type[Enum]] = field(default_factory=dict)
    default_params: dict[str, str] = field(default_factory=dict)
    requires_custom_path: bool = False

    def asdict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "gateway": self.gateway,
            "dataset_name": self.dataset_name,
            "base_url_attr": self.base_url_attr,
            "path": self.path,
            "method": self.method,
            "response_format": self.response_format,
            "model_hint": self.model_hint,
            "credential_param": self.credential_param,
            "service_key_url": self.service_key_url,
            "portal_url": self.portal_url,
            "description": self.description,
            "returns": self.returns,
            "required_params": list(self.required_params),
            "optional_params": list(self.optional_params),
            "param_help": dict(self.param_help),
            "param_enum": {name: enum_cls.__name__ for name, enum_cls in self.param_enum.items()},
            "default_params": dict(self.default_params),
            "requires_custom_path": self.requires_custom_path,
        }


def api_catalog(*, gateway: Gateway | None = None) -> tuple[EndpointCatalogRow, ...]:
    """Return endpoint rows used by docs, tests, and the Streamlit debug UI."""

    rows = _CATALOG
    if gateway is None:
        return rows
    return tuple(row for row in rows if row.gateway == gateway)


def get_api_catalog_entry(entry_id: str) -> EndpointCatalogRow:
    """Return a single catalog row by its ``id``.

    Raises ``KeyError`` with the list of known ids when ``entry_id`` is not
    in the catalog, mirroring ``services.get_service``-style lookups.
    """

    try:
        return _CATALOG_BY_ID[entry_id]
    except KeyError:
        known = ", ".join(sorted(_CATALOG_BY_ID))
        raise KeyError(f"unknown catalog entry {entry_id!r}; known ids: {known}") from None


def env_names_for_gateway(gateway: Gateway) -> tuple[str, ...]:
    if gateway == "data_go_kr":
        return ("DATA_GO_KR_SERVICE_KEY",)
    return ()


_KHS_PORTAL = "https://www.khs.go.kr/cha/idx/Index.do"
_GIS_PORTAL = "https://gis-heritage.go.kr"
_NRICH_PORTAL = "https://portal.nrich.go.kr/kor/apiList.do?menuIdx=665"
_DATA_GO_KR_PORTAL = "https://www.data.go.kr"

_COMPOSITE_KEY_HELP: dict[str, str] = {
    "ccbaKdcd": "Heritage type code, e.g. 11.",
    "ccbaAsno": "Designation serial number, e.g. 0000010000000.",
    "ccbaCtcd": "Region code, e.g. 11.",
}
_COMPOSITE_KEY_DEFAULTS: dict[str, str] = {
    "ccbaKdcd": "11",
    "ccbaAsno": "0000010000000",
    "ccbaCtcd": "11",
}

# Baked in at import time so the event-list form has a sane, non-empty
# starting point without the UI having to special-case that one endpoint.
_now = datetime.now()


_CATALOG: tuple[EndpointCatalogRow, ...] = (
    EndpointCatalogRow(
        id="khs-search-list",
        label="KHS / SearchKindOpenapiList.do",
        gateway="khs",
        dataset_name="National heritage search list",
        base_url_attr="heritage_base_url",
        path="/SearchKindOpenapiList.do",
        model_hint="HeritageSummary",
        portal_url=_KHS_PORTAL,
        description="Search designated and undesignated national heritage records.",
        returns="Returns a paged list of heritage summaries (name, region, category, coordinates).",
        optional_params=("pageUnit", "pageIndex", "ccbaKdcd", "ccbaCtcd", "ccbaMnm1"),
        param_help={
            "pageUnit": "Rows per page.",
            "pageIndex": "1-based page number.",
            "ccbaKdcd": _COMPOSITE_KEY_HELP["ccbaKdcd"],
            "ccbaCtcd": _COMPOSITE_KEY_HELP["ccbaCtcd"],
            "ccbaMnm1": "Korean name contains text.",
        },
        default_params={"pageUnit": "10", "pageIndex": "1"},
    ),
    EndpointCatalogRow(
        id="khs-search-detail",
        label="KHS / SearchKindOpenapiDt.do",
        gateway="khs",
        dataset_name="National heritage detail",
        base_url_attr="heritage_base_url",
        path="/SearchKindOpenapiDt.do",
        model_hint="HeritageDetail",
        portal_url=_KHS_PORTAL,
        description="Fetch a single heritage record by composite key.",
        returns="Returns one heritage record with description text and designation metadata.",
        required_params=("ccbaKdcd", "ccbaAsno", "ccbaCtcd"),
        param_help=dict(_COMPOSITE_KEY_HELP),
        default_params=dict(_COMPOSITE_KEY_DEFAULTS),
    ),
    EndpointCatalogRow(
        id="khs-image",
        label="KHS / SearchImageOpenapi.do",
        gateway="khs",
        dataset_name="National heritage images",
        base_url_attr="heritage_base_url",
        path="/SearchImageOpenapi.do",
        portal_url=_KHS_PORTAL,
        description="Fetch image metadata by heritage composite key.",
        returns="Returns a list of image URLs and captions for the given heritage record.",
        required_params=("ccbaKdcd", "ccbaAsno", "ccbaCtcd"),
        param_help=dict(_COMPOSITE_KEY_HELP),
        default_params=dict(_COMPOSITE_KEY_DEFAULTS),
    ),
    EndpointCatalogRow(
        id="khs-video",
        label="KHS / SearchVideoOpenapi.do",
        gateway="khs",
        dataset_name="National heritage videos",
        base_url_attr="heritage_base_url",
        path="/SearchVideoOpenapi.do",
        portal_url=_KHS_PORTAL,
        description="Fetch video metadata by heritage composite key.",
        returns="Returns a list of video URLs and titles for the given heritage record.",
        required_params=("ccbaKdcd", "ccbaAsno", "ccbaCtcd"),
        param_help=dict(_COMPOSITE_KEY_HELP),
        default_params=dict(_COMPOSITE_KEY_DEFAULTS),
    ),
    EndpointCatalogRow(
        id="khs-voice",
        label="KHS / SearchVoiceOpenapi.do",
        gateway="khs",
        dataset_name="National heritage narrations",
        base_url_attr="heritage_base_url",
        path="/SearchVoiceOpenapi.do",
        portal_url=_KHS_PORTAL,
        description="Fetch narration metadata by heritage composite key and language.",
        returns="Returns narration audio URLs and transcripts for the given heritage record.",
        required_params=("ccbaKdcd", "ccbaAsno", "ccbaCtcd", "ccbaGbn"),
        param_help={**_COMPOSITE_KEY_HELP, "ccbaGbn": "Narration language."},
        param_enum={"ccbaGbn": Lang},
        default_params={**_COMPOSITE_KEY_DEFAULTS, "ccbaGbn": Lang.KO.value},
    ),
    EndpointCatalogRow(
        id="khs-event-list",
        label="KHS / openapi/selectEventListOpenapi.do",
        gateway="khs",
        dataset_name="National heritage events",
        base_url_attr="heritage_base_url",
        path="/openapi/selectEventListOpenapi.do",
        portal_url=_KHS_PORTAL,
        description="Fetch monthly national heritage event records.",
        returns="Returns a list of events with title, dates, and venue for the given month.",
        required_params=("searchYear", "searchMonth"),
        param_help={
            "searchYear": "4-digit year, e.g. 2026.",
            "searchMonth": "2-digit month, e.g. 05.",
        },
        default_params={
            "searchYear": str(_now.year),
            "searchMonth": f"{_now.month:02d}",
        },
    ),
    EndpointCatalogRow(
        id="gis-spca",
        label="GIS Heritage / xmlService/spca.do",
        gateway="gis",
        dataset_name="Heritage GIS location response",
        base_url_attr="gis_base_url",
        path="/xmlService/spca.do",
        portal_url=_GIS_PORTAL,
        description="Probe the GIS XML endpoint and inspect location payload shape.",
        returns="Returns heritage location features (point geometry plus raw properties).",
        optional_params=("minLng", "minLat", "maxLng", "maxLat"),
        param_help={
            "minLng": "Bounding box minimum longitude.",
            "minLat": "Bounding box minimum latitude.",
            "maxLng": "Bounding box maximum longitude.",
            "maxLat": "Bounding box maximum latitude.",
        },
    ),
    EndpointCatalogRow(
        id="nrich-api-list-page",
        label="NRICH / Open API catalog page",
        gateway="nrich",
        dataset_name="NRICH open API catalog page",
        base_url_attr="absolute",
        path="https://portal.nrich.go.kr/kor/apiList.do?menuIdx=665",
        response_format="html",
        portal_url=_NRICH_PORTAL,
        description="Open the NRICH catalog page for schema and endpoint discovery.",
        returns="Returns the raw HTML catalog page (no structured rows).",
    ),
    EndpointCatalogRow(
        id="data-go-kr-custom",
        label="data.go.kr / Custom path",
        gateway="data_go_kr",
        dataset_name="data.go.kr custom endpoint",
        base_url_attr="data_go_kr_base_url",
        path="/",
        response_format="json/xml",
        credential_param="serviceKey",
        service_key_url=_DATA_GO_KR_PORTAL,
        portal_url=_DATA_GO_KR_PORTAL,
        description="Use Extra params JSON and the Custom path field to probe key-required APIs.",
        returns="Returns whatever the targeted data.go.kr endpoint responds with (JSON or XML).",
        requires_custom_path=True,
    ),
)

_CATALOG_BY_ID: dict[str, EndpointCatalogRow] = {row.id: row for row in _CATALOG}
