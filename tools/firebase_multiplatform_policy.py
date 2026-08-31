"""Fail-closed validation for Firebase-only BigQuery aggregate SQL.

This policy is separate from the Remote MCP view policy: the Gemini MCP path
accepts only activated safe views, while the local API fallback may use the
explicitly approved Firebase export datasets. Both paths reject writes,
unbounded scans, sensitive projections and non-Waje objects.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


DEFAULT_MAX_ROWS = 500
DEFAULT_MAX_BYTES = 5 * 1024 * 1024 * 1024
AGGREGATE_ONLY_IDENTIFIERS = {"session_id", "event_id", "issue_id"}
FORBIDDEN_IDENTIFIERS = {
    "user_id",
    "user_pseudo_id",
    "uuid",
    "phone",
    "phone_number",
    "email",
    "bvn",
    "nin",
    "biometric",
    "face_image",
    "document_image",
    "account_number",
    "bank_account",
    "order_id",
    "transaction_id",
    "device_id",
    "advertising_id",
    "vendor_id",
    "ip",
    "token",
    "cookie",
    "request_body",
    "response_body",
    "stack_trace",
    "custom_keys",
    "installation_uuid",
}
FORBIDDEN_OPERATIONS = (
    "insert",
    "update",
    "delete",
    "merge",
    "create",
    "drop",
    "alter",
    "truncate",
    "export",
    "load",
    "call",
    "grant",
    "revoke",
    "execute immediate",
)


def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def source_references(sql: str) -> list[str]:
    # Region-qualified INFORMATION_SCHEMA references are commonly written as
    # `project`.region-xxx.INFORMATION_SCHEMA.TABLES. Remove quoting only for
    # parsing; the original SQL remains unchanged for execution/auditing.
    sql = sql.replace("`", "")
    refs = re.findall(
        r"(?:from|join|table)\s+`?([a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_*${}-]+){1,3})`?",
        sql,
        flags=re.I,
    )
    return sorted(set(item.lower().strip("`") for item in refs))


def _dataset_for_reference(reference: str) -> str | None:
    parts = reference.split(".")
    if len(parts) < 2:
        return None
    return ".".join(parts[:2])


def _select_clause(sql: str) -> str:
    match = re.search(r"\bselect\b(.*?)\bfrom\b", sql, flags=re.I | re.S)
    return match.group(1) if match else ""


def _sensitive_projection_errors(sql: str) -> list[str]:
    projection = _select_clause(sql).lower()
    # For CTEs, IDs may be carried into an outer aggregate but must not appear
    # as an output column. Inspect the outermost (last) SELECT projection.
    lowered = sql.lower()
    last_select = lowered.rfind("select")
    outer_projection = _select_clause(sql[last_select:]).lower() if last_select >= 0 else projection
    errors: list[str] = []
    for identifier in FORBIDDEN_IDENTIFIERS:
        if re.search(rf"\b{re.escape(identifier)}\b", projection):
            errors.append(f"direct_sensitive_identifier_projection:{identifier}")
    # Session/event/issue keys are permitted only as COUNT(DISTINCT key), never
    # as a returned dimension.
    for identifier in AGGREGATE_ONLY_IDENTIFIERS:
        if re.search(rf"\b{re.escape(identifier)}\b", outer_projection):
            direct_output = re.search(
                rf"(?:^|,)\s*`?{re.escape(identifier)}`?(?:\s+as\s+\w+)?\s*(?:,|$)",
                outer_projection,
            )
            if direct_output:
                errors.append(f"aggregate_only_identifier_projected:{identifier}")
    return errors


def _has_date_predicate(sql: str) -> bool:
    fields = (
        "event_date",
        "report_date",
        "cohort_date",
        "date",
        "dt",
        "_table_suffix",
        "_partitiondate",
        "event_time",
        "event_timestamp",
    )
    return any(
        re.search(
            rf"(?:\bdate\s*\(\s*)?`?{re.escape(field)}`?(?:\s*,[^)]*)?\s*\)?\s*(?:between|>=|>|=|in\b)",
            sql,
            flags=re.I,
        )
        for field in fields
    )


def _limit_value(sql: str) -> int | None:
    match = re.search(r"\blimit\s+(\d+)\b", sql, flags=re.I)
    return int(match.group(1)) if match else None


def validate_sql(
    sql: str,
    *,
    allowed_datasets: list[str],
    max_rows: int = DEFAULT_MAX_ROWS,
) -> list[str]:
    """Return deterministic blocking errors for one Firebase aggregate query."""
    if not isinstance(sql, str) or not sql.strip():
        return ["missing_sql"]
    cleaned = strip_comments(sql).strip()
    errors: list[str] = []
    statements = [item.strip() for item in cleaned.split(";") if item.strip()]
    if len(statements) != 1:
        errors.append("multiple_sql_statements_not_allowed")
    if not re.match(r"^(select|with)\b", cleaned, flags=re.I):
        errors.append("only_select_or_with_allowed")
    lowered = cleaned.lower()
    for operation in FORBIDDEN_OPERATIONS:
        if re.search(rf"\b{re.escape(operation)}\b", lowered):
            errors.append(f"forbidden_operation:{operation}")
    if re.search(r"\bselect\s+(?:distinct\s+)?\*\s*(?:,|from)\b", lowered):
        errors.append("select_star_not_allowed")

    metadata_query = "information_schema" in lowered
    if not metadata_query and not _has_date_predicate(cleaned):
        errors.append("date_or_partition_predicate_required")
    if not metadata_query:
        limit = _limit_value(cleaned)
        if limit is None:
            errors.append("limit_required")
        elif limit > max_rows:
            errors.append("limit_exceeds_policy")

    approved = {item.lower().strip("`") for item in allowed_datasets}
    refs = source_references(cleaned)
    if not refs:
        errors.append("approved_source_required")
    for reference in refs:
        if not reference.startswith("wajenigeria."):
            errors.append("source_outside_wajenigeria")
            continue
        if "information_schema" in reference:
            continue
        dataset = _dataset_for_reference(reference)
        if dataset not in approved:
            errors.append(f"source_outside_firebase_allowlist:{dataset or reference}")

    errors.extend(_sensitive_projection_errors(cleaned))
    return sorted(set(errors))


def validate_file(path: Path, *, allowed_datasets: list[str], max_rows: int = DEFAULT_MAX_ROWS) -> list[str]:
    return validate_sql(path.read_text(encoding="utf-8"), allowed_datasets=allowed_datasets, max_rows=max_rows)


def source_allowlist_from_config(config: dict[str, Any]) -> list[str]:
    profile = config.get("firebase_source_scope", {})
    values = profile.get("approved_dataset_allowlist", [])
    return [str(item) for item in values]
