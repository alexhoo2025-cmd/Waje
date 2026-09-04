"""Fixed-query, aggregate-only gateway for the Waje Agent Runtime application.

The language model never receives a general SQL execution capability. Each
function in this module selects a pre-approved query template and binds only
typed, bounded filter values. The only data objects referenced are the five
safe aggregate views declared in :mod:`config`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Iterable, Mapping

from .config import (
    DATA_LOCATION,
    DATA_PROJECT_ID,
    MAX_QUERY_BYTES,
    MAX_RESULT_ROWS,
    MAX_RUN_BYTES,
    METRIC_DEFINITION_VERSION,
    MINIMUM_GROUP_SIZE,
    QueryFilters,
    SAFE_VIEWS,
)


class QueryGatewayError(RuntimeError):
    """The safe gateway rejected or could not run an aggregate query."""


@dataclass(frozen=True)
class QueryPlan:
    """A pre-approved read-only view query and its bound parameters."""

    tool_name: str
    view_name: str
    sql: str
    parameters: Mapping[str, Any]

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class GatewayResult:
    """Bounded, safe result envelope returned to the model tool."""

    status: str
    tool_name: str
    source_view: str
    query_fingerprint: str
    scanned_bytes: int | None
    rows: tuple[dict[str, Any], ...]
    data_cutoff_at: str | None
    complete_day: bool | None
    quality_status: str | None
    metric_definition_version: str
    missing_reason: str | None = None


def _where(
    filters: QueryFilters,
    *,
    allowed_filter_fields: set[str],
    allow_rank_dimension: bool = False,
    allow_country_via_dimension: bool = False,
) -> tuple[list[str], dict[str, Any]]:
    clauses = ["metric_date_lagos BETWEEN @date_from AND @date_to"]
    parameters: dict[str, Any] = {
        "date_from": filters.window.date_from.isoformat(),
        "date_to": filters.window.date_to.isoformat(),
    }
    for field_name in ("endpoint", "app_package", "app_version", "country"):
        value = getattr(filters, field_name)
        if value:
            if field_name == "country" and allow_country_via_dimension:
                continue
            if field_name not in allowed_filter_fields:
                raise QueryGatewayError(f"filter_not_available_for_tool:{field_name}")
            clauses.append(f"{field_name} = @{field_name}")
            parameters[field_name] = value
    if allow_rank_dimension and filters.rank_dimension:
        clauses.append("analysis_dimension = @rank_dimension")
        parameters["rank_dimension"] = filters.rank_dimension
    elif filters.rank_dimension:
        raise QueryGatewayError("rank_dimension_not_available_for_tool")
    return clauses, parameters


def build_plan(tool_name: str, filters: QueryFilters) -> QueryPlan:
    """Construct one immutable safe-view query for a named agent function."""

    if tool_name == "data_health":
        view_name = SAFE_VIEWS["data_health"]
        where, parameters = _where(filters, allowed_filter_fields={"endpoint", "app_package"})
        sql = f"""
SELECT
  metric_date_lagos, endpoint, platform, app_package, source_name,
  source_record_count, distinct_session_count, session_start_event_count,
  event_name_count, data_cutoff_at, source_freshness_lag_minutes,
  complete_day, quality_status, quality_note, metric_definition_version
FROM `{view_name}`
WHERE {' AND '.join(where)}
ORDER BY metric_date_lagos DESC, endpoint, source_name
LIMIT {MAX_RESULT_ROWS}
"""
    elif tool_name in {"native_performance", "network_quality"}:
        view_name = SAFE_VIEWS["native_performance"]
        where, parameters = _where(
            filters,
            allowed_filter_fields={"endpoint", "app_package", "app_version"},
            allow_rank_dimension=True,
            allow_country_via_dimension=True,
        )
        if filters.country:
            if filters.rank_dimension not in {None, "country"}:
                raise QueryGatewayError("country_requires_country_rank_dimension")
            where.append("analysis_dimension = 'country'")
            where.append("analysis_value = @country")
            parameters["country"] = filters.country
        elif filters.rank_dimension is None:
            where.append("analysis_dimension = 'overview'")
        if tool_name == "network_quality":
            where.append("network_request_count > 0")
        parameters["top_n"] = filters.top_n
        sql = f"""
SELECT
  metric_date_lagos, endpoint, platform, app_package, app_version,
  analysis_dimension, analysis_value, performance_record_count,
  duration_trace_count, duration_trace_p95_ms, screen_trace_count,
  slow_frame_ratio, frozen_frame_ratio, network_request_count,
  network_response_count, network_success_count, network_success_rate,
  network_p95_ms, data_cutoff_at, complete_day, quality_status,
  metric_definition_version
FROM `{view_name}`
WHERE {' AND '.join(where)}
  AND performance_record_count >= {MINIMUM_GROUP_SIZE}
ORDER BY metric_date_lagos DESC, performance_record_count DESC, analysis_value
LIMIT @top_n
"""
    elif tool_name == "stability":
        view_name = SAFE_VIEWS["stability"]
        where, parameters = _where(
            filters,
            allowed_filter_fields={"endpoint", "app_package", "app_version"},
        )
        parameters["top_n"] = filters.top_n
        sql = f"""
SELECT
  metric_date_lagos, endpoint, platform, app_package, app_version,
  device_name_bucket, os_version, error_type, export_record_count,
  dedup_event_count, issue_count, data_cutoff_at, complete_day,
  quality_status, quality_note, metric_definition_version
FROM `{view_name}`
WHERE {' AND '.join(where)}
ORDER BY metric_date_lagos DESC, dedup_event_count DESC, issue_count DESC
LIMIT @top_n
"""
    elif tool_name == "event_session_context":
        view_name = SAFE_VIEWS["event_session"]
        where, parameters = _where(
            filters,
            allowed_filter_fields={"endpoint", "app_package", "app_version"},
        )
        parameters["top_n"] = filters.top_n
        sql = f"""
SELECT
  metric_date_lagos, endpoint, platform, app_package, app_version,
  event_category, event_name_bucket, event_count, session_start_event_count,
  distinct_session_count, data_cutoff_at, complete_day, quality_status,
  metric_definition_version
FROM `{view_name}`
WHERE {' AND '.join(where)}
ORDER BY metric_date_lagos DESC, event_count DESC
LIMIT @top_n
"""
    elif tool_name == "h5_observability_status":
        view_name = SAFE_VIEWS["h5_observability"]
        where, parameters = _where(
            filters,
            allowed_filter_fields={"endpoint", "app_package", "app_version"},
        )
        where.append("endpoint = 'h5'")
        parameters["top_n"] = filters.top_n
        sql = f"""
SELECT
  metric_date_lagos, endpoint, app_package, app_version, event_category,
  event_name_bucket, event_count, covered_days, data_cutoff_at, complete_day,
  quality_status, missing_reason, metric_definition_version
FROM `{view_name}`
WHERE {' AND '.join(where)}
ORDER BY metric_date_lagos DESC, event_count DESC
LIMIT @top_n
"""
    else:
        raise QueryGatewayError("tool_not_allowed")
    return QueryPlan(tool_name=tool_name, view_name=view_name, sql=sql.strip(), parameters=parameters)


def _safe_scalar(value: Any) -> Any:
    """Serialize supported aggregate values without preserving nested payloads."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, date):
        return value.isoformat()
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    return str(value)


def _safe_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed if a view accidentally projects a forbidden-looking field."""

    prohibited = {
        "user_id", "user_pseudo_id", "session_id", "device_id", "advertising_id",
        "token", "cookie", "url", "request_body", "response_body", "stack_trace",
        "order_id", "transaction_id", "email", "phone", "bvn", "nin",
    }
    output: dict[str, Any] = {}
    for key, value in row.items():
        if str(key).lower() in prohibited:
            raise QueryGatewayError(f"unsafe_field_from_view:{key}")
        output[str(key)] = _safe_scalar(value)
    return output


class BigQueryGateway:
    """Executes only fixed safe-view plans with dry-run budget enforcement."""

    def __init__(
        self,
        *,
        client: Any | None = None,
        max_query_bytes: int = MAX_QUERY_BYTES,
        max_run_bytes: int = MAX_RUN_BYTES,
    ) -> None:
        self._client = client
        self._max_query_bytes = max_query_bytes
        self._max_run_bytes = max_run_bytes
        self._run_scanned_bytes = 0

    def _client_or_raise(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from google.cloud import bigquery
        except ImportError as exc:  # pragma: no cover - deployment dependency
            raise QueryGatewayError("bigquery_client_library_unavailable") from exc
        self._client = bigquery.Client(project=DATA_PROJECT_ID, location=DATA_LOCATION)
        return self._client

    @staticmethod
    def _query_config(parameters: Mapping[str, Any], *, dry_run: bool) -> Any:
        try:
            from google.cloud import bigquery
        except ImportError as exc:  # pragma: no cover - deployment dependency
            raise QueryGatewayError("bigquery_client_library_unavailable") from exc
        query_parameters = []
        for key, value in parameters.items():
            if key in {"date_from", "date_to"}:
                query_parameters.append(bigquery.ScalarQueryParameter(key, "DATE", value))
            elif key == "top_n":
                query_parameters.append(bigquery.ScalarQueryParameter(key, "INT64", value))
            else:
                query_parameters.append(bigquery.ScalarQueryParameter(key, "STRING", value))
        return bigquery.QueryJobConfig(
            dry_run=dry_run,
            use_query_cache=False,
            maximum_bytes_billed=MAX_QUERY_BYTES,
            query_parameters=query_parameters,
            labels={"waje_agent": "device_performance", "privacy": "aggregate_only"},
        )

    def execute(self, tool_name: str, filters: QueryFilters) -> GatewayResult:
        plan = build_plan(tool_name, filters)
        client = self._client_or_raise()
        dry_job = client.query(plan.sql, job_config=self._query_config(plan.parameters, dry_run=True), location=DATA_LOCATION)
        scanned_bytes = int(getattr(dry_job, "total_bytes_processed", 0) or 0)
        if scanned_bytes > self._max_query_bytes:
            raise QueryGatewayError("query_exceeds_1_gib_budget")
        if self._run_scanned_bytes + scanned_bytes > self._max_run_bytes:
            raise QueryGatewayError("agent_run_exceeds_5_gib_budget")

        job = client.query(plan.sql, job_config=self._query_config(plan.parameters, dry_run=False), location=DATA_LOCATION)
        rows = tuple(_safe_row(dict(row.items())) for row in job.result(max_results=MAX_RESULT_ROWS))
        self._run_scanned_bytes += int(getattr(job, "total_bytes_processed", scanned_bytes) or scanned_bytes)
        if not rows:
            return GatewayResult(
                status="no_data",
                tool_name=tool_name,
                source_view=plan.view_name,
                query_fingerprint=plan.fingerprint,
                scanned_bytes=scanned_bytes,
                rows=(),
                data_cutoff_at=None,
                complete_day=None,
                quality_status="no_data",
                metric_definition_version=METRIC_DEFINITION_VERSION,
                missing_reason="safe_view_returned_no_aggregate_rows",
            )

        latest_cutoff = max((str(row.get("data_cutoff_at")) for row in rows if row.get("data_cutoff_at")), default=None)
        complete_values = {row.get("complete_day") for row in rows if row.get("complete_day") is not None}
        quality_values = {str(row.get("quality_status")) for row in rows if row.get("quality_status")}
        if "blocked" in quality_values:
            status = "blocked"
        elif "delayed" in quality_values:
            status = "delayed"
        elif "data_gap" in quality_values:
            status = "data_gap"
        elif "immature" in quality_values:
            status = "immature"
        elif any(value != "certified" for value in quality_values):
            status = "provisional"
        else:
            status = "certified"
        return GatewayResult(
            status=status,
            tool_name=tool_name,
            source_view=plan.view_name,
            query_fingerprint=plan.fingerprint,
            scanned_bytes=scanned_bytes,
            rows=rows,
            data_cutoff_at=latest_cutoff,
            complete_day=True if complete_values == {True} else False if complete_values else None,
            quality_status=next(iter(sorted(quality_values)), None),
            metric_definition_version=METRIC_DEFINITION_VERSION,
        )


def result_as_tool_payload(result: GatewayResult) -> dict[str, Any]:
    """Return a compact model-facing object; SQL and raw job metadata stay private."""

    return {
        "status": result.status,
        "source_view": result.source_view,
        "data_cutoff_at": result.data_cutoff_at,
        "complete_day": result.complete_day,
        "sample_count": len(result.rows),
        "quality_status": result.quality_status,
        "metric_definition_version": result.metric_definition_version,
        "query_bytes": result.scanned_bytes,
        "aggregates": list(result.rows),
        "missing_reason": result.missing_reason,
    }
