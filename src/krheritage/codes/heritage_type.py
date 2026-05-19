from __future__ import annotations

from enum import IntEnum


class HeritageType(IntEnum):
    """FORMAL_CD designation categories used by Korea Heritage APIs."""

    NATIONAL_TREASURE = 25
    TREASURE = 26
    HISTORIC_SITE = 27
    HISTORIC_SCENIC = 28
    SCENIC_SITE = 29
    NATURAL_MONUMENT = 30
    INTANGIBLE_NATIONAL = 31
    FOLKLORE_NATIONAL = 32
    TANGIBLE_LOCAL = 33
    INTANGIBLE_LOCAL = 34
    MEMORIAL_LOCAL = 35
    FOLKLORE_LOCAL = 36
    HERITAGE_MATERIAL = 37
    REGISTERED = 38
    MOVABLE_GENERAL = 39
    BURIED = 40
    UNDESIGNATED = 2533
    NO_DESIGNATION = 2537
    OVERSEAS_HERITAGE = 2859
    UNDESIGNATED_RUIN = 2860
    UNDESIGNATED_ARTIFACT = 2861

    @property
    def korean(self) -> str:
        return _HERITAGE_TYPE_KO[self]

    @property
    def is_designated(self) -> bool:
        return self.value < 2500


_HERITAGE_TYPE_KO: dict[HeritageType, str] = {
    HeritageType.NATIONAL_TREASURE: "국보",
    HeritageType.TREASURE: "보물",
    HeritageType.HISTORIC_SITE: "사적",
    HeritageType.HISTORIC_SCENIC: "사적 및 명승",
    HeritageType.SCENIC_SITE: "명승",
    HeritageType.NATURAL_MONUMENT: "천연기념물",
    HeritageType.INTANGIBLE_NATIONAL: "국가무형유산",
    HeritageType.FOLKLORE_NATIONAL: "국가민속유산",
    HeritageType.TANGIBLE_LOCAL: "시도유형문화유산",
    HeritageType.INTANGIBLE_LOCAL: "시도무형유산",
    HeritageType.MEMORIAL_LOCAL: "시도기념물",
    HeritageType.FOLKLORE_LOCAL: "시도민속문화유산",
    HeritageType.HERITAGE_MATERIAL: "문화유산자료",
    HeritageType.REGISTERED: "등록유산",
    HeritageType.MOVABLE_GENERAL: "일반동산문화유산",
    HeritageType.BURIED: "매장유산",
    HeritageType.UNDESIGNATED: "비지정유산",
    HeritageType.NO_DESIGNATION: "지정사항 없음",
    HeritageType.OVERSEAS_HERITAGE: "해외문화유산",
    HeritageType.UNDESIGNATED_RUIN: "비지정 유적건조물",
    HeritageType.UNDESIGNATED_ARTIFACT: "비지정 유물",
}

