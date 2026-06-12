from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from krheritage.codes import HeritageDomain, HeritageType, KoglLicense, domain_for_type
from krheritage.models.base import KrHeritageModel


class HeritageKey(KrHeritageModel):
    """Composite key used by cha.go.kr and khs.go.kr endpoints.

    Live ``SearchKindOpenapiList`` rows occasionally ship with missing key
    components, so list parsing stays lenient and accepts ``None`` here.
    Detail payloads enforce completeness through ``HeritageDetail`` instead.
    """

    ccba_kdcd: str | None = Field(default=None, alias="ccbaKdcd")
    ccba_asno: str | None = Field(default=None, alias="ccbaAsno")
    ccba_ctcd: str | None = Field(default=None, alias="ccbaCtcd")

    @property
    def is_complete(self) -> bool:
        """Whether every key component is a non-empty string."""

        return bool(self.ccba_kdcd and self.ccba_asno and self.ccba_ctcd)

    @property
    def heritage_type(self) -> HeritageType | None:
        try:
            return HeritageType(int(self.ccba_kdcd)) if self.ccba_kdcd else None
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

    @field_validator("longitude", "latitude", mode="before")
    @classmethod
    def _blank_coordinate_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

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

    @model_validator(mode="after")
    def _require_complete_key(self) -> HeritageDetail:
        if not self.key.is_complete:
            raise ValueError(
                "detail payload is missing composite key components: "
                f"ccbaKdcd={self.key.ccba_kdcd!r}, ccbaAsno={self.key.ccba_asno!r}, "
                f"ccbaCtcd={self.key.ccba_ctcd!r}"
            )
        return self
