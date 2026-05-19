from __future__ import annotations

from pydantic import Field

from krheritage.codes import HeritageDomain, HeritageType, KoglLicense, domain_for_type
from krheritage.models.base import KrHeritageModel


class HeritageKey(KrHeritageModel):
    """Composite key used by cha.go.kr and khs.go.kr endpoints."""

    ccba_kdcd: str = Field(alias="ccbaKdcd")
    ccba_asno: str = Field(alias="ccbaAsno")
    ccba_ctcd: str = Field(alias="ccbaCtcd")

    @property
    def heritage_type(self) -> HeritageType | None:
        try:
            return HeritageType(int(self.ccba_kdcd))
        except (TypeError, ValueError):
            return None

    @property
    def natural_key(self) -> str:
        return f"{self.ccba_kdcd}-{self.ccba_asno}-{self.ccba_ctcd}"


class HeritageSummary(KrHeritageModel):
    """Summary item returned by SearchKindOpenapiList."""

    key: HeritageKey
    name_ko: str = Field(alias="ccbaMnm1")
    name_en: str | None = Field(default=None, alias="ccbaMnm2")
    category: str | None = Field(default=None, alias="ccmaName")
    region: str | None = Field(default=None, alias="ccbaCtcdNm")
    sigungu: str | None = Field(default=None, alias="ccsiName")
    owner: str | None = Field(default=None, alias="ccbaAdmin")
    longitude: float | None = None
    latitude: float | None = None
    image_url: str | None = Field(default=None, alias="imageUrl")
    license: KoglLicense | None = None

    @property
    def domain(self) -> HeritageDomain | None:
        heritage_type = self.key.heritage_type
        return domain_for_type(heritage_type) if heritage_type is not None else None

    @property
    def address(self) -> str | None:
        parts = [part for part in (self.region, self.sigungu) if part]
        return " ".join(parts) if parts else None


class HeritageDetail(HeritageSummary):
    """Detailed heritage payload returned by SearchKindOpenapiDt."""

    quantity: str | None = Field(default=None, alias="ccbaQuan")
    designated_at: str | None = Field(default=None, alias="ccbaAsdt")
    location_text: str | None = Field(default=None, alias="ccbaLcad")
    manager: str | None = Field(default=None, alias="ccbaAdmin")
    content: str | None = None
    content_html: str | None = None
