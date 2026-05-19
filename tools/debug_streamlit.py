"""Streamlit debug UI for python-krheritage-api."""
# ruff: noqa: E402

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
for module_name, module in list(sys.modules.items()):
    if module_name != "krheritage" and not module_name.startswith("krheritage."):
        continue
    module_file = getattr(module, "__file__", None)
    if module_file is not None and not Path(module_file).resolve().is_relative_to(SRC):
        del sys.modules[module_name]

try:
    import streamlit as st
except ModuleNotFoundError as exc:  # pragma: no cover - optional UI dependency
    raise SystemExit('Run `pip install -e ".[debug-ui]"` to use the Streamlit UI.') from exc

from krheritage.catalog import EndpointCatalogRow, api_catalog, env_names_for_gateway
from krheritage.config import HeritageConfig
from krheritage.models import HeritageDetail, HeritageSummary
from krheritage.transport import AsyncHttpxTransport, parse_payload


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    required: bool
    label: str
    placeholder: str = ""
    help: str = ""
    default: str = ""


def _param(
    name: str,
    *,
    required: bool = True,
    label: str | None = None,
    placeholder: str = "",
    help: str = "",
    default: str = "",
) -> ParameterSpec:
    return ParameterSpec(
        name=name,
        required=required,
        label=label or name,
        placeholder=placeholder,
        help=help,
        default=default,
    )


def main() -> None:
    st.set_page_config(page_title="KR Heritage API Debug", layout="wide")
    st.title("KR Heritage API Debug")

    gateways = sorted({row.gateway for row in api_catalog()})
    selected_gateway = st.sidebar.selectbox("Data source", gateways, index=gateways.index("khs"))
    rows = list(api_catalog(gateway=selected_gateway))
    selected_label = st.sidebar.selectbox("API", [row.label for row in rows])
    selected = rows[[row.label for row in rows].index(selected_label)]

    st.sidebar.caption("API full name")
    st.sidebar.write(_api_full_name(selected))
    st.sidebar.caption(selected.description)
    _portal_links(selected)

    custom_path = ""
    if selected.id == "data-go-kr-custom":
        custom_path = st.sidebar.text_input(
            "Custom path or URL",
            value="",
            placeholder="/B551011/...",
            help="Use an absolute URL or a path relative to https://apis.data.go.kr.",
        )

    env_names = env_names_for_gateway(selected.gateway)
    api_key = _auth_sidebar(selected, env_names)
    timeout = st.sidebar.number_input("Timeout", min_value=1.0, max_value=120.0, value=30.0)
    max_rps = st.sidebar.number_input("max_rps", min_value=0.1, max_value=30.0, value=5.0)
    fixture_base_dir = _fixture_base_dir_sidebar()

    tabs = st.tabs(
        [
            "Raw Response",
            "Parsed Payload",
            "Pydantic Model",
            "Processed Result",
            "Validation Errors",
            "Debug Trace",
            "Fixture / Testcase",
        ]
    )

    with tabs[0]:
        _raw_response_tab(
            selected,
            api_key=api_key,
            timeout=float(timeout),
            max_rps=float(max_rps),
            custom_path=custom_path,
        )
    with tabs[1]:
        _parsed_payload_tab(selected)
    with tabs[2]:
        _pydantic_model_tab(selected)
    with tabs[3]:
        _processed_result_tab(selected)
    with tabs[4]:
        _validation_errors_tab(selected)
    with tabs[5]:
        _debug_trace_tab(rows, selected, env_names)
    with tabs[6]:
        _fixture_tab(selected, fixture_base_dir)


def _raw_response_tab(
    selected: EndpointCatalogRow,
    *,
    api_key: str,
    timeout: float,
    max_rps: float,
    custom_path: str,
) -> None:
    st.subheader(selected.dataset_name)
    st.caption(f"{selected.gateway} / {selected.path}")

    try:
        submitted, params, extra_params, missing = _request_form(selected)
    except ValueError as exc:
        st.error(str(exc))
        return

    request_params = {**params, **extra_params}
    preview = _redacted_params(selected, request_params, api_key)
    st.subheader("Request params preview")
    st.json(preview)

    if not submitted:
        return
    if selected.id == "data-go-kr-custom" and not custom_path.strip():
        st.error("Custom path or URL is required for the data.go.kr custom endpoint.")
        return
    if missing:
        st.error("Missing required parameters: " + ", ".join(missing))
        return

    try:
        run = asyncio.run(
            _run_request(
                selected,
                request_params=request_params,
                api_key=api_key,
                timeout=timeout,
                max_rps=max_rps,
                custom_path=custom_path,
            )
        )
    except Exception as exc:  # pragma: no cover - UI display
        _store_run(
            selected,
            body_text="",
            parsed={},
            rows=[],
            request_params=preview,
            request_url="",
            model_name=None,
            models=[],
            validation_errors=[str(exc)],
        )
        st.error(str(exc))
        return

    _store_run(selected, **run)
    st.code(run["body_text"][:20_000], language=_language_for(selected))


def _request_form(
    selected: EndpointCatalogRow,
) -> tuple[bool, dict[str, Any], dict[str, Any], list[str]]:
    specs = _parameter_specs(selected)
    required_specs = [spec for spec in specs if spec.required]
    optional_specs = [spec for spec in specs if not spec.required]
    key_prefix = selected.id

    with st.form(f"request-form:{key_prefix}"):
        st.subheader("Required parameters")
        required_values = _render_param_grid(required_specs, key_prefix=key_prefix)
        if not required_specs:
            st.caption("This endpoint has no built-in required parameter spec.")

        st.subheader("Optional parameters")
        optional_values = _render_param_grid(optional_specs, key_prefix=key_prefix)
        extra_text = st.text_area(
            "Extra params JSON",
            value="{}",
            height=120,
            help="Add provider-specific parameters that are not represented in the form.",
            key=f"{key_prefix}:extra",
        )
        submitted = st.form_submit_button("Run selected API")

    params = {**required_values, **optional_values}
    missing = [spec.name for spec in required_specs if not str(params.get(spec.name, "")).strip()]
    extra_params = _parse_extra_params(extra_text)
    return submitted, _non_empty(params), extra_params, missing


def _render_param_grid(specs: tuple[ParameterSpec, ...], *, key_prefix: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for index in range(0, len(specs), 2):
        columns = st.columns(2)
        for column, spec in zip(columns, specs[index : index + 2], strict=False):
            with column:
                values[spec.name] = st.text_input(
                    spec.label,
                    value=spec.default,
                    placeholder=spec.placeholder,
                    help=spec.help or None,
                    key=f"{key_prefix}:param:{spec.name}",
                )
    return values


def _parameter_specs(selected: EndpointCatalogRow) -> tuple[ParameterSpec, ...]:
    defaults = dict(selected.default_params)
    if selected.id == "khs-search-list":
        return (
            _param("pageUnit", required=False, default=defaults.get("pageUnit", "10")),
            _param("pageIndex", required=False, default=defaults.get("pageIndex", "1")),
            _param("ccbaKdcd", required=False, help="Heritage type code, e.g. 11."),
            _param("ccbaCtcd", required=False, help="Region code, e.g. 11."),
            _param("ccbaMnm1", required=False, help="Korean name contains text."),
        )
    if selected.id in {"khs-search-detail", "khs-image", "khs-video"}:
        return _composite_key_specs(defaults)
    if selected.id == "khs-voice":
        return (
            *_composite_key_specs(defaults),
            _param("ccbaGbn", default=defaults.get("ccbaGbn", "kr"), help="kr, en, jp, ch"),
        )
    if selected.id == "khs-event-list":
        now = datetime.now()
        return (
            _param("searchYear", default=str(now.year)),
            _param("searchMonth", default=str(now.month)),
        )
    return tuple(_param(name, required=False, default=value) for name, value in defaults.items())


def _composite_key_specs(defaults: dict[str, str]) -> tuple[ParameterSpec, ...]:
    return (
        _param("ccbaKdcd", default=defaults.get("ccbaKdcd", "11")),
        _param("ccbaAsno", default=defaults.get("ccbaAsno", "0000010000000")),
        _param("ccbaCtcd", default=defaults.get("ccbaCtcd", "11")),
    )


def _parse_extra_params(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Extra params JSON is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Extra params JSON must be an object")
    return {
        str(key): value
        for key, value in payload.items()
        if key not in {"serviceKey", "ServiceKey", "authKey"}
    }


async def _run_request(
    selected: EndpointCatalogRow,
    *,
    request_params: dict[str, Any],
    api_key: str,
    timeout: float,
    max_rps: float,
    custom_path: str,
) -> dict[str, Any]:
    config = HeritageConfig.from_env(api_key=api_key or None, max_rps=max_rps)
    params = dict(request_params)
    if selected.credential_param and api_key:
        params[selected.credential_param] = api_key

    url = _endpoint_url(selected, config, custom_path=custom_path)
    transport = AsyncHttpxTransport(config, timeout=timeout)
    try:
        body = await transport.get(url, params=params)
    finally:
        await transport.aclose()

    body_text = body.decode("utf-8", errors="replace")
    parsed = _parse_body(selected, body)
    rows = _rows_for_selected(selected, parsed)
    model_name, models, validation_errors = _parse_models(selected, rows)
    return {
        "body_text": body_text,
        "parsed": parsed,
        "rows": rows,
        "request_params": _redacted_params(selected, request_params, api_key),
        "request_url": url,
        "model_name": model_name,
        "models": models,
        "validation_errors": validation_errors,
    }


def _endpoint_url(
    selected: EndpointCatalogRow,
    config: HeritageConfig,
    *,
    custom_path: str,
) -> str:
    if selected.id == "data-go-kr-custom":
        path = custom_path.strip()
        if path.startswith(("http://", "https://")):
            return path
        return _join_url(config.data_go_kr_base_url, path)
    if selected.base_url_attr == "absolute":
        return selected.path
    base_url = getattr(config, selected.base_url_attr)
    return _join_url(str(base_url), selected.path)


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _parse_body(selected: EndpointCatalogRow, body: bytes) -> dict[str, Any]:
    if selected.response_format == "html":
        return {"html": body.decode("utf-8", errors="replace")}
    return parse_payload(body)


def _rows_for_selected(
    selected: EndpointCatalogRow,
    parsed: dict[str, Any],
) -> list[dict[str, Any]]:
    result = parsed.get("result")
    if not isinstance(result, dict):
        return _rows_from_node(parsed)
    if selected.id == "khs-search-detail":
        base = {key: value for key, value in result.items() if key != "item"}
        return [{**base, **row} for row in _rows_from_node(result.get("item", {}))]
    if "item" in result:
        return _rows_from_node(result["item"])
    return [result]


def _rows_from_node(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        rows: list[dict[str, Any]] = []
        for item in value:
            rows.extend(_rows_from_node(item))
        return rows
    if not isinstance(value, dict):
        return [{"value": value}]

    list_lengths = [len(item) for item in value.values() if isinstance(item, list)]
    if not list_lengths:
        return [value]

    row_count = max(list_lengths)
    rows = []
    for index in range(row_count):
        row: dict[str, Any] = {}
        for key, item in value.items():
            if isinstance(item, list):
                row[key] = item[index] if index < len(item) else None
            else:
                row[key] = item
        rows.append(row)
    return rows


def _parse_models(
    selected: EndpointCatalogRow,
    rows: list[dict[str, Any]],
) -> tuple[str | None, list[dict[str, Any]], list[str]]:
    if selected.model_hint not in {"HeritageSummary", "HeritageDetail"}:
        return None, [], []

    model_cls = HeritageDetail if selected.model_hint == "HeritageDetail" else HeritageSummary
    models: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, row in enumerate(rows):
        try:
            payload = _heritage_model_payload(row)
            models.append(model_cls.model_validate(payload).model_dump(mode="json"))
        except Exception as exc:
            errors.append(f"row {index}: {exc}")
    return selected.model_hint, models, errors


def _heritage_model_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload["key"] = {
        "ccbaKdcd": str(row.get("ccbaKdcd", "")),
        "ccbaAsno": str(row.get("ccbaAsno", "")),
        "ccbaCtcd": str(row.get("ccbaCtcd", "")),
    }
    return payload


def _parsed_payload_tab(selected: EndpointCatalogRow) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("Run an API in the Raw Response tab to inspect the parsed payload.")
        return
    st.json(run["parsed"])


def _pydantic_model_tab(selected: EndpointCatalogRow) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("Run an API in the Raw Response tab to inspect model conversion.")
        return
    if not run["models"]:
        st.info("No Pydantic model conversion is configured for this endpoint yet.")
        return
    st.caption(f"{run['model_name']} / {len(run['models'])} rows")
    st.json(run["models"])


def _processed_result_tab(selected: EndpointCatalogRow) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("Run an API in the Raw Response tab to inspect row output.")
        return
    rows = run["rows"]
    if not rows:
        st.info("No rows were extracted from the response.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _validation_errors_tab(selected: EndpointCatalogRow) -> None:
    run = _current_run(selected)
    if run is None:
        st.info("No API has been run for this selection yet.")
        return
    if not run["validation_errors"]:
        st.success("No validation errors for the current run.")
        return
    for error in run["validation_errors"]:
        st.error(error)


def _debug_trace_tab(
    rows: list[EndpointCatalogRow],
    selected: EndpointCatalogRow,
    env_names: tuple[str, ...],
) -> None:
    st.subheader("Catalog")
    st.dataframe([row.asdict() for row in rows], use_container_width=True, hide_index=True)
    st.subheader("Selected API")
    st.json(selected.asdict())
    st.caption(f"credential env: {', '.join(env_names) if env_names else '-'}")

    run = _current_run(selected)
    if run is None:
        return
    st.subheader("Last request")
    st.code(str(run["request_url"]), language=None)
    st.json(run["request_params"])


def _fixture_tab(selected: EndpointCatalogRow, fixture_base_dir: str) -> None:
    st.caption("Fixture base dir")
    st.code(fixture_base_dir, language=None)
    run = _current_run(selected)
    if run is None:
        st.info("Run an API first to download a fixture JSON payload.")
        return
    fixture = json.dumps(run, ensure_ascii=False, indent=2, default=str)
    st.download_button(
        "Download last run fixture",
        data=fixture,
        file_name=f"{selected.id}-fixture.json",
        mime="application/json",
    )


def _store_run(selected: EndpointCatalogRow, **run: Any) -> None:
    st.session_state["last_run"] = {"selection_key": selected.id, **run}


def _current_run(selected: EndpointCatalogRow) -> dict[str, Any] | None:
    run = st.session_state.get("last_run")
    if not isinstance(run, dict) or run.get("selection_key") != selected.id:
        return None
    return run


def _api_full_name(selected: EndpointCatalogRow) -> str:
    return f"{selected.dataset_name} / {selected.gateway} / {selected.path}"


def _portal_links(selected: EndpointCatalogRow) -> None:
    if selected.portal_url:
        st.sidebar.link_button("Provider portal", selected.portal_url)
    if selected.service_key_url:
        st.sidebar.link_button("Service key", selected.service_key_url)


def _auth_sidebar(selected: EndpointCatalogRow, env_names: tuple[str, ...]) -> str:
    if not selected.credential_param:
        return ""
    st.sidebar.subheader("Auth")
    env_sources = _env_key_sources(env_names)
    auth_mode = "manual"
    if env_sources:
        auth_mode = st.sidebar.selectbox("Credential source", ["env", "manual"])
        if auth_mode == "env":
            st.sidebar.caption(f"{env_sources[0]['name']} from {env_sources[0]['source']}")
            return env_sources[0]["value"]
    return st.sidebar.text_input(
        selected.credential_param,
        value="",
        type="password",
        placeholder="Paste key manually",
        help=f"Available env names: {', '.join(env_names)}",
    )


def _env_key_sources(env_names: tuple[str, ...]) -> list[dict[str, str]]:
    local_env = _load_local_env()
    sources: list[dict[str, str]] = []
    for name in env_names:
        value = os.getenv(name)
        if value:
            sources.append({"name": name, "value": value, "source": "process env"})
            return sources
    for name in env_names:
        value = local_env.get(name)
        if value:
            sources.append({"name": name, "value": value, "source": ".env or .env.local"})
            return sources
    return sources


def _load_local_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for filename in (".env", ".env.local"):
        path = ROOT / filename
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


def _fixture_base_dir_sidebar() -> str:
    st.sidebar.subheader("Fixtures")
    candidates = [
        ROOT / "tests" / "fixtures",
        ROOT / "tests",
        ROOT / "tools",
        ROOT,
    ]
    options = [str(path.resolve()) for path in candidates]
    selected = st.sidebar.selectbox("Fixture base dir", [*options, "Custom..."])
    if selected == "Custom...":
        selected = st.sidebar.text_input("Custom fixture base dir", value=options[0])
    return selected


def _redacted_params(
    selected: EndpointCatalogRow,
    params: dict[str, Any],
    api_key: str,
) -> dict[str, Any]:
    preview = dict(params)
    if selected.credential_param and api_key:
        preview[selected.credential_param] = "***"
    return preview


def _non_empty(params: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in params.items() if str(value).strip()}


def _language_for(selected: EndpointCatalogRow) -> str | None:
    if selected.response_format == "html":
        return "html"
    if "json" in selected.response_format:
        return "json"
    return "xml"


if __name__ == "__main__":
    main()
