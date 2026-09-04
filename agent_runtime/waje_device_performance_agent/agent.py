"""ADK entrypoint for the Waje aggregate-only device-performance agent."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from .config import (
    FALLBACK_MODEL,
    MODEL_LOCATION,
    PRIMARY_MODEL,
    THINKING_LEVEL,
    QueryFilters,
    RequestValidationError,
    normalize_filters,
)
from .query_gateway import BigQueryGateway, QueryGatewayError, result_as_tool_payload


AGENT_NAME = "waje_device_performance_analyst"
AGENT_DISPLAY_NAME = "Waje 端侧设备与性能分析助手"
SYSTEM_INSTRUCTION = (Path(__file__).with_name("system_instruction.md")).read_text(encoding="utf-8")


def selected_model() -> str:
    """Select the deployment-tested model; unlisted values fail closed."""

    candidate = os.environ.get("WAGE_AGENT_MODEL", PRIMARY_MODEL).strip()
    if candidate not in {PRIMARY_MODEL, FALLBACK_MODEL}:
        raise RuntimeError("configured_agent_model_not_allowed")
    return candidate


@lru_cache(maxsize=1)
def _gateway() -> BigQueryGateway:
    return BigQueryGateway()


def _filters(
    date_from: str | None,
    date_to: str | None,
    endpoint: str | None,
    app_package: str | None,
    app_version: str | None,
    country: str | None,
    rank_dimension: str | None,
    top_n: int | None,
) -> QueryFilters:
    return normalize_filters(
        date_from=date_from,
        date_to=date_to,
        endpoint=endpoint,
        app_package=app_package,
        app_version=app_version,
        country=country,
        rank_dimension=rank_dimension,
        top_n=top_n,
    )


def _run(tool_name: str, filters: QueryFilters) -> dict[str, Any]:
    try:
        payload = result_as_tool_payload(_gateway().execute(tool_name, filters))
        payload["actual_model"] = selected_model()
        return payload
    except RequestValidationError as exc:
        return {
            "status": "blocked",
            "missing_reason": str(exc),
            "actual_model": selected_model(),
        }
    except QueryGatewayError as exc:
        return {
            "status": "blocked",
            "missing_reason": str(exc),
            "actual_model": selected_model(),
        }


def get_data_health(
    date_from: str | None = None,
    date_to: str | None = None,
    endpoint: str | None = None,
    app_package: str | None = None,
    app_version: str | None = None,
    country: str | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Read source coverage, freshness, complete-day and quality aggregates only."""

    return _run("data_health", _filters(date_from, date_to, endpoint, app_package, app_version, country, None, top_n))


def get_native_performance(
    date_from: str | None = None,
    date_to: str | None = None,
    endpoint: str | None = None,
    app_package: str | None = None,
    app_version: str | None = None,
    country: str | None = None,
    rank_dimension: str | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Read native P95, frame, and trace aggregates by one safe dimension."""

    return _run("native_performance", _filters(date_from, date_to, endpoint, app_package, app_version, country, rank_dimension, top_n))


def get_network_quality(
    date_from: str | None = None,
    date_to: str | None = None,
    endpoint: str | None = None,
    app_package: str | None = None,
    app_version: str | None = None,
    country: str | None = None,
    rank_dimension: str | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Read network P95 and HTTP response-health aggregates, never business success."""

    return _run("network_quality", _filters(date_from, date_to, endpoint, app_package, app_version, country, rank_dimension, top_n))


def get_stability(
    date_from: str | None = None,
    date_to: str | None = None,
    endpoint: str | None = None,
    app_package: str | None = None,
    app_version: str | None = None,
    country: str | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Read Crashlytics event and issue aggregates, never rates or raw stacks."""

    return _run("stability", _filters(date_from, date_to, endpoint, app_package, app_version, country, None, top_n))


def get_event_session_context(
    date_from: str | None = None,
    date_to: str | None = None,
    endpoint: str | None = None,
    app_package: str | None = None,
    app_version: str | None = None,
    country: str | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Read event and session-context aggregates with explicit session semantics."""

    return _run("event_session_context", _filters(date_from, date_to, endpoint, app_package, app_version, country, None, top_n))


def get_h5_observability_status(
    date_from: str | None = None,
    date_to: str | None = None,
    app_version: str | None = None,
    country: str | None = None,
    top_n: int = 5,
) -> dict[str, Any]:
    """Read H5 Firebase behavior aggregates and explicit observability gaps."""

    return _run("h5_observability_status", _filters(date_from, date_to, "h5", "waje_ng_firebase_h5", app_version, country, None, top_n))


def build_app(model: str | None = None) -> Any:
    """Build an ADK app lazily so policy tests require no cloud dependencies."""

    try:
        from google.adk.agents import Agent
        from google.genai import types
        from vertexai.agent_engines import AdkApp
    except ImportError as exc:  # pragma: no cover - deployment dependency
        raise RuntimeError("agent_runtime_dependencies_unavailable") from exc

    active_model = model or selected_model()
    if active_model not in {PRIMARY_MODEL, FALLBACK_MODEL}:
        raise RuntimeError("configured_agent_model_not_allowed")
    generation_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL)
    )
    agent = Agent(
        model=active_model,
        name=AGENT_NAME,
        description="Aggregate-only Waje Firebase/GA4 device and performance analyst.",
        instruction=SYSTEM_INSTRUCTION,
        generate_content_config=generation_config,
        tools=[
            get_data_health,
            get_native_performance,
            get_network_quality,
            get_stability,
            get_event_session_context,
            get_h5_observability_status,
        ],
    )
    return AdkApp(agent=agent)


if __name__ == "__main__":  # pragma: no cover - deployment entrypoint
    build_app()
