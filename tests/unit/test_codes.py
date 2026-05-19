from __future__ import annotations

from krheritage import PROVIDER_NAME
from krheritage.codes import (
    CityCode,
    HeritageDomain,
    HeritageType,
    KoglLicense,
    Lang,
    domain_for_type,
)


def test_provider_name_matches_repository_slug() -> None:
    assert PROVIDER_NAME == "python-krheritage-api"


def test_city_code_korean_names_include_chungbuk_355() -> None:
    assert CityCode.SEOUL.korean == "서울특별시"
    assert CityCode.CHUNGBUK.value == 355
    assert CityCode.CHUNGBUK.korean == "충청북도"
    assert CityCode.CHUNGNAM.value == 356


def test_heritage_type_domain_mapping() -> None:
    assert HeritageType.NATIONAL_TREASURE.korean == "국보"
    assert domain_for_type(HeritageType.NATIONAL_TREASURE) is HeritageDomain.CULTURAL
    assert domain_for_type(HeritageType.NATURAL_MONUMENT) is HeritageDomain.NATURAL
    assert domain_for_type(HeritageType.INTANGIBLE_NATIONAL) is HeritageDomain.INTANGIBLE


def test_kogl_license_policy() -> None:
    assert KoglLicense.TYPE_0.allows_commercial
    assert KoglLicense.TYPE_0.allows_modification
    assert KoglLicense.TYPE_0.allows_ai_training
    assert KoglLicense.TYPE_AI.allows_ai_training
    assert not KoglLicense.TYPE_4.allows_commercial
    assert not KoglLicense.TYPE_4.allows_modification


def test_lang_values() -> None:
    assert Lang.KO.value == "kr"
    assert Lang.JA.korean == "일본어"

