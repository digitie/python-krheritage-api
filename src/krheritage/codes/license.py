from __future__ import annotations

from enum import IntEnum


class KoglLicense(IntEnum):
    """Korea Open Government License USE_SCOPE values."""

    TYPE_0 = 3396
    TYPE_1 = 371
    TYPE_2 = 372
    TYPE_3 = 373
    TYPE_4 = 374
    TYPE_AI = 3397

    @property
    def korean(self) -> str:
        return _KOGL_KO[self]

    @property
    def allows_commercial(self) -> bool:
        return self in {KoglLicense.TYPE_0, KoglLicense.TYPE_1, KoglLicense.TYPE_3}

    @property
    def allows_modification(self) -> bool:
        return self in {KoglLicense.TYPE_0, KoglLicense.TYPE_1, KoglLicense.TYPE_2}

    @property
    def allows_ai_training(self) -> bool:
        return self in {KoglLicense.TYPE_AI, KoglLicense.TYPE_0}


_KOGL_KO: dict[KoglLicense, str] = {
    KoglLicense.TYPE_0: "자유 이용",
    KoglLicense.TYPE_1: "출처표시",
    KoglLicense.TYPE_2: "출처표시 + 상업적 이용금지",
    KoglLicense.TYPE_3: "출처표시 + 변경금지",
    KoglLicense.TYPE_4: "출처표시 + 비상업 + 변경금지",
    KoglLicense.TYPE_AI: "AI 학습 허용",
}

