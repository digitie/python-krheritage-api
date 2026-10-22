from __future__ import annotations

from datetime import date

from pydantic import ConfigDict, Field, field_validator, model_validator

from krheritage.models.base import KrHeritageModel


class HeritageEvent(KrHeritageModel):
    """국가유산 행사 1회차 — live ``selectEventListOpenapi.do`` ``<item>``.

    필드 alias는 live 응답(2026-10 실측) 그대로다: ``seqNo``/``siteCode``/``subTitle``/
    ``subContent``/``sDate``/``eDate``/``groupName``/``contact``/``subDesc``/``subPath``/
    ``subDesc_2``/``subDesc_3``/``mainImageTemp``/``sido``/``gugun``/``subDate``.

    ``seqNo``(→ ``sn``)는 행사 프로그램 식별자이고 **row 식별자가 아니다** — 같은
    프로그램의 회차마다 ``sDate``/``eDate``만 다른 row가 여러 개 온다(2026-10 실측
    2,006 row 중 1,378 row가 중복 ``seqNo``). row 단위 키가 필요하면
    :attr:`occurrence_key`를 쓴다.

    응답에는 좌표가 없다 — ``longitude``/``latitude``는 항상 ``None``이다.
    ``address``는 ``sido``/``gugun``을 이어 붙인 best-effort 행정구역 문자열이다.
    """

    # JSON 응답에서 숫자로 올 수 있는 ``seqNo``/``siteCode`` 등이 row 하나로 월 전체를
    # 깨지 않도록 숫자→문자열 강제.
    model_config = ConfigDict(coerce_numbers_to_str=True)

    sn: str | None = Field(default=None, alias="seqNo")
    site_code: str | None = Field(default=None, alias="siteCode")
    title: str | None = None
    sub_title: str | None = Field(default=None, alias="subTitle")
    sub_title2: str | None = Field(default=None, alias="subTitle2")
    contents: str | None = Field(default=None, alias="subContent")
    starts_on: date | None = Field(default=None, alias="sDate")
    ends_on: date | None = Field(default=None, alias="eDate")
    group_name: str | None = Field(default=None, alias="groupName")
    tel_name: str | None = Field(default=None, alias="contact")
    place: str | None = Field(default=None, alias="subDesc")
    url: str | None = Field(default=None, alias="subPath")
    target_audience: str | None = Field(default=None, alias="subDesc_2")
    fee: str | None = Field(default=None, alias="subDesc_3")
    main_image: str | None = Field(default=None, alias="mainImageTemp")
    sido: str | None = None
    gugun: str | None = None
    schedule_text: str | None = Field(default=None, alias="subDate")
    address: str | None = None
    heritage_name: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    raw: dict[str, object] = Field(default_factory=dict)

    @property
    def display_title(self) -> str | None:
        title = self.title or self.sub_title
        if title and self.sub_title2:
            return f"{title} {self.sub_title2}".strip()
        return title

    @property
    def occurrence_key(self) -> str | None:
        """회차 단위 결정적 키 ``{sn}::{starts_on}::{ends_on}`` (``sn`` 없으면 ``None``).

        live 응답에서 ``seqNo``는 회차마다 반복되지만 (``seqNo``, ``sDate``, ``eDate``)
        조합은 2026-10 실측 기준 유일했다(상류가 보장하는 제약은 아니다). 날짜가 비면 해당 자리는 빈 문자열이다.
        """
        if not self.sn:
            return None
        starts = self.starts_on.isoformat() if self.starts_on is not None else ""
        ends = self.ends_on.isoformat() if self.ends_on is not None else ""
        return f"{self.sn}::{starts}::{ends}"

    @field_validator("*", mode="before")
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        # live 응답은 결측 값을 빈 CDATA(``<subDesc><![CDATA[]]></subDesc>``)로 준다.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("starts_on", "ends_on", mode="before")
    @classmethod
    def _parse_compact_date(cls, value: object) -> object:
        # live 형식은 ``YYYYMMDD``. ISO 날짜(시각 포함)와 숫자 8자리 표기·정수도 받는다.
        # 달력상 불가능한 값은 row 하나 때문에 월 전체 파싱이 깨지지 않도록 ``None``
        # (원문은 ``raw``에 보존된다).
        if isinstance(value, int) and not isinstance(value, bool):
            value = str(value)
        if isinstance(value, str):
            try:
                return date.fromisoformat(value.strip()[:10])
            except ValueError:
                pass
            digits = "".join(char for char in value if char.isdigit())
            if len(digits) != 8:
                return None
            try:
                return date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))
            except ValueError:
                return None
        return value

    @model_validator(mode="after")
    def _derive_address(self) -> HeritageEvent:
        if self.address is None:
            parts = [part for part in (self.sido, self.gugun) if part]
            self.address = " ".join(parts) or None
        return self
