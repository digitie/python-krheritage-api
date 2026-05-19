from __future__ import annotations

from enum import IntEnum


class CityCode(IntEnum):
    """AREA_CD values used by public heritage datasets."""

    SEOUL = 345
    BUSAN = 346
    DAEGU = 347
    INCHEON = 348
    GWANGJU = 349
    DAEJEON = 350
    ULSAN = 351
    SEJONG = 352
    GYEONGGI = 353
    GANGWON = 354
    CHUNGBUK = 355
    CHUNGNAM = 356
    JEONBUK = 357
    JEONNAM = 358
    GYEONGBUK = 359
    GYEONGNAM = 360
    JEJU = 361
    NATIONWIDE = 362
    OVERSEAS = 363

    @property
    def korean(self) -> str:
        return _CITY_KO[self]


_CITY_KO: dict[CityCode, str] = {
    CityCode.SEOUL: "서울특별시",
    CityCode.BUSAN: "부산광역시",
    CityCode.DAEGU: "대구광역시",
    CityCode.INCHEON: "인천광역시",
    CityCode.GWANGJU: "광주광역시",
    CityCode.DAEJEON: "대전광역시",
    CityCode.ULSAN: "울산광역시",
    CityCode.SEJONG: "세종특별자치시",
    CityCode.GYEONGGI: "경기도",
    CityCode.GANGWON: "강원특별자치도",
    CityCode.CHUNGBUK: "충청북도",
    CityCode.CHUNGNAM: "충청남도",
    CityCode.JEONBUK: "전북특별자치도",
    CityCode.JEONNAM: "전라남도",
    CityCode.GYEONGBUK: "경상북도",
    CityCode.GYEONGNAM: "경상남도",
    CityCode.JEJU: "제주특별자치도",
    CityCode.NATIONWIDE: "전국",
    CityCode.OVERSEAS: "국외",
}
