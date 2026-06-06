from __future__ import annotations

from datetime import date

from pydantic import Field, field_validator

from krheritage.models.base import KrHeritageModel


class HeritageEvent(KrHeritageModel):
    sn: str | None = None
    title: str | None = None
    sub_title: str | None = Field(default=None, alias="subTitle")
    sub_title2: str | None = Field(default=None, alias="subTitle2")
    starts_on: date | None = Field(default=None, alias="startDate")
    ends_on: date | None = Field(default=None, alias="endDate")
    place: str | None = Field(default=None, alias="siteName")
    address: str | None = None
    tel_name: str | None = Field(default=None, alias="telName")
    contents: str | None = None
    heritage_name: str | None = None
    main_image: str | None = Field(default=None, alias="mainImage")
    longitude: float | None = None
    latitude: float | None = None
    url: str | None = None
    raw: dict[str, object] = Field(default_factory=dict)

    @property
    def display_title(self) -> str | None:
        title = self.title or self.sub_title
        if title and self.sub_title2:
            return f"{title} {self.sub_title2}".strip()
        return title

    @field_validator("starts_on", "ends_on", mode="before")
    @classmethod
    def _parse_compact_date(cls, value: object) -> object:
        if isinstance(value, str):
            digits = "".join(char for char in value if char.isdigit())
            if len(digits) == 8:
                return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))
        return value
