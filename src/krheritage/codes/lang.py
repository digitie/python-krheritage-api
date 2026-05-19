from __future__ import annotations

from krheritage.codes._compat import StrEnum


class Lang(StrEnum):
    """Narration language codes used by SearchVoiceOpenapi."""

    KO = "kr"
    EN = "en"
    JA = "jp"
    ZH = "ch"

    @property
    def korean(self) -> str:
        return _LANG_KO[self]


_LANG_KO: dict[Lang, str] = {
    Lang.KO: "한국어",
    Lang.EN: "영어",
    Lang.JA: "일본어",
    Lang.ZH: "중국어",
}

