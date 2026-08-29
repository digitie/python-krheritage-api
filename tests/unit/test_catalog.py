from __future__ import annotations

import pytest

from krheritage.catalog import api_catalog, env_names_for_gateway, get_api_catalog_entry
from krheritage.codes.lang import Lang


def test_api_catalog_exposes_debug_ui_rows() -> None:
    rows = api_catalog()
    ids = {row.id for row in rows}

    assert "khs-search-list" in ids
    assert "khs-search-detail" in ids
    assert "gis-spca" in ids
    assert all(row.label for row in rows)
    assert all(row.method == "GET" for row in rows)


def test_api_catalog_filters_by_gateway() -> None:
    rows = api_catalog(gateway="khs")

    assert rows
    assert {row.gateway for row in rows} == {"khs"}


def test_env_names_for_data_go_kr_gateway() -> None:
    assert env_names_for_gateway("data_go_kr") == ("DATA_GO_KR_SERVICE_KEY",)
    assert env_names_for_gateway("khs") == ()


def test_get_api_catalog_entry_returns_the_matching_row() -> None:
    entry = get_api_catalog_entry("khs-search-detail")

    assert entry.id == "khs-search-detail"
    assert entry.required_params == ("ccbaKdcd", "ccbaAsno", "ccbaCtcd")


def test_get_api_catalog_entry_raises_key_error_with_known_ids() -> None:
    with pytest.raises(KeyError, match="khs-search-list"):
        get_api_catalog_entry("does-not-exist")


def test_every_row_carries_parameter_metadata_for_form_generation() -> None:
    # The Streamlit debug UI auto-generates its request form from these
    # fields — every row must at least expose the (possibly empty) tuples so
    # the UI never needs a per-id branch to know what to render.
    for row in api_catalog():
        assert isinstance(row.required_params, tuple)
        assert isinstance(row.optional_params, tuple)


def test_gis_spca_exposes_its_real_optional_parameters() -> None:
    # Regression guard: the old debug UI's hardcoded _parameter_specs()
    # fell through to an empty tuple for gis-spca, hiding all 4 of its real
    # optional bounding-box parameters.
    entry = get_api_catalog_entry("gis-spca")

    assert entry.optional_params == ("minLng", "minLat", "maxLng", "maxLat")


def test_khs_voice_language_param_uses_the_lang_enum() -> None:
    entry = get_api_catalog_entry("khs-voice")

    assert entry.param_enum["ccbaGbn"] is Lang
    assert entry.default_params["ccbaGbn"] == Lang.KO.value


def test_data_go_kr_custom_requires_a_custom_path() -> None:
    entry = get_api_catalog_entry("data-go-kr-custom")

    assert entry.requires_custom_path is True
    assert entry.credential_param == "serviceKey"


def test_asdict_serializes_enum_params_as_class_names() -> None:
    entry = get_api_catalog_entry("khs-voice")

    snapshot = entry.asdict()

    assert snapshot["param_enum"] == {"ccbaGbn": "Lang"}
    assert snapshot["required_params"] == ["ccbaKdcd", "ccbaAsno", "ccbaCtcd", "ccbaGbn"]
