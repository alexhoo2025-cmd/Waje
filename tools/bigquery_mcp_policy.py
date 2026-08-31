"""Fail-closed policy checks for Waje BigQuery Remote MCP query requests.

This module never connects to BigQuery. It validates SQL, active-view scope and
dry-run budgets before a caller invokes an external MCP or BigQuery API tool.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "config" / "bigquery_mcp_policy.json"


def load_policy(path: Path | str = DEFAULT_POLICY) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("project_id") != "wajenigeria":
        raise ValueError("BigQuery MCP policy is restricted to project wajenigeria")
    if payload.get("policy_mode") != "fail_closed":
        raise ValueError("BigQuery MCP policy must remain fail_closed")
    return payload


def strip_comments(sql: str) -> str:
    without_blocks = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", without_blocks)


def source_references(sql: str) -> list[str]:
    refs = re.findall(
        r"(?:from|join|table)\s+`?([a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_*${}-]+){1,2})`?",
        sql,
        flags=re.I,
    )
    return sorted(set(ref.lower().strip("`") for ref in refs))


def select_clause(sql: str) -> str:
    match = re.search(r"\bselect\b(.*?)\bfrom\b", sql, flags=re.I | re.S)
    return match.group(1) if match else ""


def _has_date_predicate(sql: str, fields: list[str]) -> bool:
    for field in fields:
        expression = rf"(?:`?[a-zA-Z0-9_]+`?\.)?`?{re.escape(field)}`?\s*(?:between|>=|>|=|in\b)"
        if re.search(expression, sql, flags=re.I):
            return True
    return False


def _limit_value(sql: str) -> int | None:
    match = re.search(r"\blimit\s+(\d+)\b", sql, flags=re.I)
    return int(match.group(1)) if match else None


def _direct_sensitive_projection(sql: str, identifiers: list[str]) -> bool:
    projection = select_clause(sql).lower()
    for identifier in identifiers:
        expression = rf"(?:`?[a-zA-Z0-9_]+`?\.)?`?{re.escape(identifier.lower())}`?"
        if re.search(expression, projection, flags=re.I):
            return True
    return False


def validate_query(sql: str, policy: dict[str, Any]) -> list[str]:
    """Return fail-closed errors for one proposed Remote MCP query."""
    errors: list[str] = []
    if not isinstance(sql, str) or not sql.strip():
        return ["missing_sql"]

    remote = policy.get("remote_mcp", {})
    if remote.get("trusted") is not True:
        errors.append("remote_mcp_not_trusted")
    tools = set(remote.get("allowed_tools", []))
    if "execute_sql_readonly" not in tools or "execute_sql" not in set(remote.get("denied_tools", [])):
        errors.append("remote_mcp_tool_allowlist_not_readonly")

    cleaned = strip_comments(sql).strip()
    statements = [statement.strip() for statement in cleaned.split(";") if statement.strip()]
    if len(statements) != 1:
        errors.append("multiple_sql_statements_not_allowed")
    allowed_starts = tuple(policy.get("sql_policy", {}).get("allowed_statement_starts", []))
    if not re.match(rf"^({'|'.join(map(re.escape, allowed_starts))})\b", cleaned, flags=re.I):
        errors.append("only_select_or_with_allowed")

    lowered = cleaned.lower()
    for keyword in policy.get("sql_policy", {}).get("forbidden_operations", []):
        if re.search(rf"\b{re.escape(keyword.lower())}\b", lowered):
            errors.append(f"forbidden_operation:{keyword}")
    if policy.get("sql_policy", {}).get("forbid_select_star") and re.search(r"\bselect\s+(?:distinct\s+)?\*\s*(?:,|from)\b", lowered):
        errors.append("select_star_not_allowed")

    is_metadata = "information_schema" in lowered
    if policy.get("sql_policy", {}).get("require_date_predicate") and not is_metadata:
        fields = [str(item) for item in policy.get("sql_policy", {}).get("date_predicate_fields", [])]
        if not _has_date_predicate(cleaned, fields):
            errors.append("date_or_partition_predicate_required")

    active_views = {str(item).lower().strip("`") for item in policy.get("active_allowed_views", [])}
    refs = source_references(cleaned)
    if not refs:
        errors.append("approved_source_view_required")
    elif not active_views:
        errors.append("no_active_authorized_views")
    elif any(ref not in active_views for ref in refs):
        errors.append("source_outside_active_authorized_views")
    elif any(not ref.startswith("wajenigeria.") for ref in refs):
        errors.append("source_outside_wajenigeria")

    identifiers = [str(item) for item in policy.get("sql_policy", {}).get("forbidden_identifiers", [])]
    if _direct_sensitive_projection(cleaned, identifiers):
        errors.append("direct_sensitive_identifier_projection")

    if policy.get("sql_policy", {}).get("require_limit") and not is_metadata:
        limit = _limit_value(cleaned)
        if limit is None:
            errors.append("limit_required")
        elif limit > int(policy.get("limits", {}).get("max_rows", 3000)):
            errors.append("limit_exceeds_policy")

    return sorted(set(errors))


def validate_dry_run_bytes(processed_bytes: int | None, policy: dict[str, Any], cumulative_bytes: int = 0) -> list[str]:
    if processed_bytes is None:
        return ["dry_run_bytes_missing"]
    if processed_bytes > int(policy.get("limits", {}).get("max_bytes_per_query", 0)):
        return ["query_bytes_exceed_policy"]
    if cumulative_bytes + processed_bytes > int(policy.get("limits", {}).get("max_bytes_per_audit", 0)):
        return ["audit_bytes_exceed_policy"]
    return []


def build_preflight(policy: dict[str, Any], mcp_status: str = "not_checked") -> dict[str, Any]:
    active_views = policy.get("active_allowed_views", [])
    trusted = policy.get("remote_mcp", {}).get("trusted") is True
    status = "ready" if trusted and active_views and mcp_status == "ok" else "blocked_external_prerequisites"
    return {
        "status": status,
        "project_id": policy["project_id"],
        "remote_mcp": {
            "endpoint": policy["remote_mcp"]["endpoint"],
            "trust": trusted,
            "mcp_status": mcp_status,
            "allowed_tools": policy["remote_mcp"]["allowed_tools"],
            "denied_tools": policy["remote_mcp"]["denied_tools"],
        },
        "active_allowed_views": active_views,
        "candidate_views": policy["candidate_views"],
        "required_external_actions": policy["required_external_actions"],
        "policy_mode": policy["policy_mode"],
    }
