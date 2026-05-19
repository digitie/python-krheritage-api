from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Gateway = Literal["khs", "gis", "nrich", "data_go_kr"]


@dataclass(frozen=True, slots=True)
class EndpointCatalogRow:
    """A UI-friendly endpoint catalog row for debug and exploration tools."""

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
    default_params: dict[str, str] = field(default_factory=dict)

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
            "default_params": dict(self.default_params),
        }


def api_catalog(*, gateway: Gateway | None = None) -> tuple[EndpointCatalogRow, ...]:
    """Return endpoint rows used by docs, tests, and the Streamlit debug UI."""

    rows = _CATALOG
    if gateway is None:
        return rows
    return tuple(row for row in rows if row.gateway == gateway)


def env_names_for_gateway(gateway: Gateway) -> tuple[str, ...]:
    if gateway == "data_go_kr":
        return ("KHERITAGE_API_KEY", "DATA_GO_KR_API_KEY", "SERVICE_KEY")
    return ()


_KHS_PORTAL = "https://www.khs.go.kr/cha/idx/Index.do"
_GIS_PORTAL = "https://gis-heritage.go.kr"
_NRICH_PORTAL = "https://portal.nrich.go.kr/kor/apiList.do?menuIdx=665"
_DATA_GO_KR_PORTAL = "https://www.data.go.kr"


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
        default_params={
            "ccbaKdcd": "11",
            "ccbaAsno": "0000010000000",
            "ccbaCtcd": "11",
        },
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
        default_params={
            "ccbaKdcd": "11",
            "ccbaAsno": "0000010000000",
            "ccbaCtcd": "11",
        },
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
        default_params={
            "ccbaKdcd": "11",
            "ccbaAsno": "0000010000000",
            "ccbaCtcd": "11",
        },
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
        default_params={
            "ccbaKdcd": "11",
            "ccbaAsno": "0000010000000",
            "ccbaCtcd": "11",
            "ccbaGbn": "kr",
        },
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
    ),
)
