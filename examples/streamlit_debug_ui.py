"""Streamlit debug UI for python-krheritage-api.

Standard path: ``examples/streamlit_debug_ui.py``. Run with::

    pip install -e ".[debug-ui]"
    streamlit run examples/streamlit_debug_ui.py

Every request parameter widget below is generated from
``EndpointCatalogRow.required_params``/``optional_params`` (see
``krheritage/catalog.py``) — there is no per-endpoint ``if entry.id == ...``
branching for form layout. Requests themselves go through the single
generic ``HeritageClient.debug_fetch()`` method.
"""
# ruff: noqa: E402

from __future__ import annotations

import json
import os
import sys
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
    import pandas as pd
    import streamlit as st
except ModuleNotFoundError as exc:  # pragma: no cover - optional UI dependency
    raise SystemExit('Run `pip install -e ".[debug-ui]"` to use the Streamlit UI.') from exc

import krheritage
from krheritage import HeritageClient
from krheritage.catalog import EndpointCatalogRow, api_catalog, env_names_for_gateway
from krheritage.debug import DebugRun, debug_error, jsonable, redact_sensitive, save_fixture


def main() -> None:
    st.set_page_config(page_title="KR Heritage API Debug", layout="wide")
    st.title("KR Heritage API Debug")

    all_rows = list(api_catalog())
    gateways = sorted({row.gateway for row in all_rows})
    default_index = gateways.index("khs") if "khs" in gateways else 0
    selected_gateway = st.sidebar.selectbox("Data source", gateways, index=default_index)

    gateway_rows = list(api_catalog(gateway=selected_gateway))
    labels = [row.label for row in gateway_rows]
    selected_label = st.sidebar.selectbox("API", labels)
    entry = gateway_rows[labels.index(selected_label)]

    st.sidebar.caption(entry.description)
    st.sidebar.caption(entry.returns)

    env_names = env_names_for_gateway(entry.gateway)
    api_key = _auth_sidebar(entry, env_names)
    timeout = st.sidebar.number_input("Timeout", min_value=1.0, max_value=120.0, value=30.0)
    fixture_base_dir = _fixture_base_dir_sidebar()

    tabs = st.tabs(
        [
            "Raw Response",
            "Pydantic Model",
            "Processed Result",
            "Validation Errors",
            "Debug Trace",
            "Fixture / Testcase",
        ]
    )

    with tabs[0]:
        _raw_response_tab(entry, api_key=api_key, timeout=float(timeout))
    with tabs[1]:
        _pydantic_model_tab(entry)
    with tabs[2]:
        _processed_result_tab(entry)
    with tabs[3]:
        _validation_errors_tab(entry)
    with tabs[4]:
        _debug_trace_tab(all_rows, entry, env_names)
    with tabs[5]:
        _fixture_tab(entry, fixture_base_dir)


def _raw_response_tab(entry: EndpointCatalogRow, *, api_key: str, timeout: float) -> None:
    st.subheader(entry.dataset_name)
    st.caption(f"{entry.gateway} / {entry.path}")

    try:
        submitted, params, custom_path, missing = _request_form(entry)
    except ValueError as exc:
        st.error(str(exc))
        return

    preview = dict(params)
    if entry.credential_param:
        preview[entry.credential_param] = "***" if api_key else "(none — request will be unsigned)"
    if entry.requires_custom_path:
        preview["_custom_path"] = custom_path or "(empty)"
    st.subheader("Request params preview")
    st.json(preview)

    if not submitted:
        return
    if entry.requires_custom_path and not custom_path.strip():
        st.error("Custom path or URL is required for this endpoint.")
        return
    if missing:
        st.error("Missing required parameters: " + ", ".join(missing))
        return

    try:
        client = HeritageClient(api_key=api_key or None, timeout=timeout)
        try:
            run = client.debug_fetch(entry.id, params=params, custom_path=custom_path)
        finally:
            client.close()
    except Exception as exc:  # pragma: no cover - defensive; debug_fetch already structures errors
        run = DebugRun(
            function="debug_fetch",
            input=redact_sensitive({"entry_id": entry.id, "params": params}),
            request={},
            response={},
            parsed=None,
            processed=None,
            trace=[f"unexpected failure before debug_fetch could run: {exc.__class__.__name__}"],
            error=debug_error(exc),
            catalog=entry.asdict(),
        )

    _store_run(entry, run)
    if run.error:
        st.error(f"{run.error['type']}: {run.error['message']}")
    body = run.response.get("body")
    if body is not None:
        st.json(jsonable(body))
    else:
        st.info("No response body was captured — see Debug Trace / Validation Errors.")


def _request_form(
    entry: EndpointCatalogRow,
) -> tuple[bool, dict[str, Any], str, list[str]]:
    key_prefix = entry.id

    with st.form(f"request-form:{key_prefix}"):
        custom_path = ""
        if entry.requires_custom_path:
            custom_path = st.text_input(
                "Custom path or URL",
                value="",
                placeholder="/B551011/... or a full https:// URL",
                help="Relative paths are joined to data.go.kr's base URL.",
                key=f"{key_prefix}:custom_path",
            )

        st.subheader("Required parameters")
        if entry.required_params:
            required_values = _render_param_grid(entry.required_params, entry, key_prefix)
        else:
            st.caption("This endpoint has no required parameters.")
            required_values = {}

        st.subheader("Optional parameters")
        if entry.optional_params:
            optional_values = _render_param_grid(entry.optional_params, entry, key_prefix)
        else:
            st.caption("This endpoint has no optional parameters.")
            optional_values = {}

        extra_text = st.text_area(
            "Extra params JSON",
            value="{}",
            height=110,
            help="Add provider-specific parameters that are not represented above.",
            key=f"{key_prefix}:extra",
        )
        submitted = st.form_submit_button("Run selected API")

    params = {**required_values, **optional_values, **_parse_extra_params(extra_text, entry)}
    missing = [name for name in entry.required_params if not str(params.get(name, "")).strip()]
    return submitted, _non_empty(params), custom_path, missing


def _render_param_grid(
    names: tuple[str, ...],
    entry: EndpointCatalogRow,
    key_prefix: str,
) -> dict[str, str]:
    values: dict[str, str] = {}
    for index in range(0, len(names), 2):
        columns = st.columns(2)
        for column, name in zip(columns, names[index : index + 2], strict=False):
            with column:
                values[name] = _param_widget(name, entry, key_prefix)
    return values


def _param_widget(name: str, entry: EndpointCatalogRow, key_prefix: str) -> str:
    """Render one form widget from catalog metadata (never a hardcoded per-name branch)."""

    widget_key = f"{key_prefix}:param:{name}"
    help_text = entry.param_help.get(name) or None
    enum_cls = entry.param_enum.get(name)
    if enum_cls is not None:
        choices = list(enum_cls)
        default_value = entry.default_params.get(name, "")
        index = next(
            (
                position
                for position, choice in enumerate(choices)
                if str(choice.value) == default_value
            ),
            0,
        )
        selection = st.selectbox(
            name,
            choices,
            index=index,
            format_func=lambda choice: f"{choice.name} ({choice.value})",
            help=help_text,
            key=widget_key,
        )
        return str(selection.value)
    return st.text_input(
        name,
        value=entry.default_params.get(name, ""),
        help=help_text,
        key=widget_key,
    )


def _parse_extra_params(text: str, entry: EndpointCatalogRow) -> dict[str, Any]:
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Extra params JSON is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Extra params JSON must be an object")
    reserved = {"serviceKey", "ServiceKey"}
    if entry.credential_param:
        reserved.add(entry.credential_param)
    return {str(key): value for key, value in payload.items() if key not in reserved}


def _non_empty(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if str(value).strip()}


def _pydantic_model_tab(entry: EndpointCatalogRow) -> None:
    run = _current_run(entry)
    if run is None:
        st.info("Run the selected API in the Raw Response tab first.")
        return
    if entry.model_hint is None:
        st.info(f"{entry.id} has no Pydantic model wired up yet; showing the parsed payload.")
    st.json(jsonable(run.parsed))


def _processed_result_tab(entry: EndpointCatalogRow) -> None:
    run = _current_run(entry)
    if run is None:
        st.info("Run the selected API in the Raw Response tab first.")
        return
    data = jsonable(run.processed)
    if isinstance(data, list) and data:
        st.dataframe(pd.json_normalize(data, sep="."), width="stretch", hide_index=True)
    else:
        st.json(data)


def _validation_errors_tab(entry: EndpointCatalogRow) -> None:
    run = _current_run(entry)
    if run is None:
        st.info("No API has been run for this selection yet.")
        return

    if run.error:
        st.error(f"{run.error['type']}: {run.error['message']}")
        st.json(run.error)
    elif not run.validation_errors:
        st.success("No validation errors for the current run.")

    if run.validation_errors:
        st.warning(f"{len(run.validation_errors)} row(s) failed model validation.")
        st.json(list(run.validation_errors))


def _debug_trace_tab(
    rows: list[EndpointCatalogRow],
    entry: EndpointCatalogRow,
    env_names: tuple[str, ...],
) -> None:
    st.subheader("Catalog")
    st.dataframe([row.asdict() for row in rows], width="stretch", hide_index=True)

    st.subheader("Selected API")
    st.json(entry.asdict())
    st.caption(f"credential env: {', '.join(env_names) if env_names else '-'}")

    run = _current_run(entry)
    if run is None:
        return

    st.subheader("Trace")
    for line in run.trace:
        st.write(f"- {line}")

    st.subheader("Last request")
    st.json(run.request)


def _fixture_tab(entry: EndpointCatalogRow, fixture_base_dir: str) -> None:
    run = _current_run(entry)
    if run is None:
        st.info("Run the selected API in the Raw Response tab before saving a fixture.")
        st.caption("Fixture base dir")
        st.code(fixture_base_dir, language=None)
        return

    with st.expander("Save as fixture", expanded=True):
        case_name = st.text_input("Case name", value=f"{entry.id}_normal")
        description = st.text_area("Description", value=f"{entry.dataset_name} normal case")
        assertion_mode = st.selectbox(
            "Assertion mode",
            ["snapshot", "schema_only", "required_fields", "count"],
        )
        exclude_fields_raw = st.text_input(
            "Exclude fields",
            value="fetched_at, request_id, updated_at",
        )
        required_fields_raw = st.text_input("Required fields", value="")
        overwrite = st.checkbox("Overwrite existing fixture", value=False)

        assertion = {
            "mode": assertion_mode,
            "exclude_fields": [
                value.strip() for value in exclude_fields_raw.split(",") if value.strip()
            ],
            "required_fields": [
                value.strip() for value in required_fields_raw.split(",") if value.strip()
            ],
        }

        st.subheader("Fixture preview")
        st.json(
            {
                "function": entry.id,
                "input": jsonable(run.input),
                "request": jsonable(run.request),
                "response": jsonable(run.response),
                "processed": jsonable(run.processed),
                "assertion": assertion,
            }
        )

        if st.button("Save as fixture"):
            try:
                path = save_fixture(
                    base_dir=fixture_base_dir,
                    function_name=entry.id,
                    case_name=case_name,
                    description=description,
                    input_data=run.input,
                    request_data=run.request,
                    response_data=run.response,
                    parsed_result=run.parsed,
                    processed_result=run.processed,
                    assertion=assertion,
                    library_version=krheritage.__version__,
                    overwrite=overwrite,
                )
            except Exception as exc:  # pragma: no cover - UI display
                st.error(f"{exc.__class__.__name__}: {exc}")
            else:
                st.success(f"Saved: {path}")


def _auth_sidebar(entry: EndpointCatalogRow, env_names: tuple[str, ...]) -> str:
    if not entry.credential_param:
        return ""

    st.sidebar.subheader("Environment")
    env_sources = _env_key_sources(env_names)
    mode = "manual"
    if env_sources:
        mode = st.sidebar.selectbox("Credential source", ["env", "manual"])
        if mode == "env":
            source = env_sources[0]
            st.sidebar.caption(f"Using {source['name']} from {source['source']}.")
    else:
        st.sidebar.caption(
            f"No {'/'.join(env_names) or 'credential'} value found in the process env or .env."
        )

    st.sidebar.subheader("Auth")
    if mode == "env" and env_sources:
        effective_key = env_sources[0]["value"]
    else:
        effective_key = st.sidebar.text_input(
            entry.credential_param,
            value="",
            type="password",
            placeholder="Paste the key manually",
            help=f"Available env names: {', '.join(env_names)}",
        )

    if entry.service_key_url:
        st.sidebar.link_button("Get a service key", entry.service_key_url)

    return effective_key


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
            sources.append({"name": name, "value": value, "source": ".env"})
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
    candidates = [ROOT / "tests" / "fixtures", ROOT / "tests", ROOT / "examples", ROOT]
    options: list[str] = []
    for path in candidates:
        resolved = str(path.resolve())
        if resolved not in options:
            options.append(resolved)
    custom_label = "Custom..."
    choice = st.sidebar.selectbox("Fixture base dir", [*options, custom_label])
    if choice == custom_label:
        choice = st.sidebar.text_input("Custom fixture base dir", value=options[0])
    st.sidebar.caption(choice)
    return choice


def _store_run(entry: EndpointCatalogRow, run: DebugRun) -> None:
    st.session_state[f"last_run:{entry.gateway}:{entry.id}"] = run


def _current_run(entry: EndpointCatalogRow) -> DebugRun | None:
    stored = st.session_state.get(f"last_run:{entry.gateway}:{entry.id}")
    return stored if isinstance(stored, DebugRun) else None


if __name__ == "__main__":
    main()
