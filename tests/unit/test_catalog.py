from __future__ import annotations

from krheritage.catalog import api_catalog, env_names_for_gateway


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
