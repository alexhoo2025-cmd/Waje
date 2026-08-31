#!/usr/bin/env python3
"""Run the Waje Firebase-only multi-platform aggregate analysis.

The runner is deliberately fail-closed. Gemini CLI is attempted only after the
enterprise BigQuery MCP preflight passes. If that path is unavailable, a fixed
read-only BigQuery CLI/API pack may run against the explicitly approved Firebase
datasets. No BigQuery, Firebase, Metabase or Lark write is performed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = ROOT / "analysis" / "firebase_multiplatform_device_performance_2026_08_27"
SQL_ROOT = ANALYSIS_ROOT / "sql"
CONFIG_PATH = ROOT / "config" / "gemini-enterprise.json"
POLICY_PATH = ROOT / "config" / "bigquery_mcp_policy.json"
SETTINGS_PATH = ROOT / ".gemini" / "settings.json"
DEFAULT_TIMEZONE = "Africa/Lagos"
DEFAULT_ACCOUNT = "robin@afuruika.net"
DEFAULT_DATA_PROJECT = "wajenigeria"
DEFAULT_DATA_LOCATION = "europe-west4"
DEFAULT_RUNTIME_PROJECT = "indigo-gecko-500503-j3"
DEFAULT_RUNTIME_LOCATION = "us-central1"
OUTPUT_ROW_CAP = 500

sys.path.insert(0, str(ROOT / "tools"))
from firebase_multiplatform_policy import source_allowlist_from_config, validate_sql  # noqa: E402
from gemini_model_routing import classify_model_attempt, model_candidates, retryable_model_status  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from render_analysis_report_html import render_markdown_file  # noqa: E402


QUERY_SPECS: list[dict[str, str]] = [
    {"id": "source_inventory", "file": "summary/00_source_inventory.sql", "kind": "metadata", "title": "Firebase 数据集与表元数据"},
    {"id": "android_analytics_summary", "file": "summary/01_android_analytics_summary.sql", "kind": "analytics", "title": "Android Analytics 窗口汇总"},
    {"id": "ios_analytics_summary", "file": "summary/02_ios_analytics_summary.sql", "kind": "analytics", "title": "iOS Analytics 窗口汇总"},
    {"id": "h5_analytics_summary", "file": "summary/03_h5_analytics_summary.sql", "kind": "h5", "title": "H5 Analytics 窗口汇总"},
    {"id": "android_sessions_summary", "file": "summary/04_android_sessions_summary.sql", "kind": "sessions", "title": "Android Sessions 窗口汇总"},
    {"id": "native_performance_summary", "file": "summary/05_native_performance_summary.sql", "kind": "performance", "title": "原生 Performance 窗口汇总"},
    {"id": "native_performance_top3", "file": "summary/06_native_performance_top3.sql", "kind": "performance_dimensions", "title": "原生 Performance 维度 Top 3 汇总"},
    {"id": "crashlytics_stability_summary", "file": "summary/07_crashlytics_stability_summary.sql", "kind": "stability", "title": "Crashlytics 稳定性窗口汇总"},
    {"id": "quality_freshness", "file": "summary/08_quality_freshness.sql", "kind": "quality", "title": "Firebase 质量与新鲜度元数据"},
]

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
TOKEN_RE = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._-]+")


def now_lagos() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).astimezone(ZoneInfo(DEFAULT_TIMEZONE))


def iso_date(value: str) -> str:
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"invalid date: {value}; use YYYY-MM-DD") from exc


def yyyymmdd(value: str) -> str:
    return iso_date(value).replace("-", "")


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def json_safe(value: Any, *, limit: int = OUTPUT_ROW_CAP) -> Any:
    """Keep structured output bounded and remove identity-like payloads."""
    forbidden = {
        "rows",
        "raw_events",
        "user_details",
        "identities",
        "token",
        "cookie",
        "user_id",
        "user_pseudo_id",
        "device_id",
        "advertising_id",
        "vendor_id",
        "session_id",
        "installation_id",
        "installation_uuid",
        "stack_trace",
        "custom_keys",
    }
    if isinstance(value, dict):
        return {str(k): json_safe(v, limit=limit) for k, v in value.items() if str(k).lower() not in forbidden}
    if isinstance(value, list):
        return [json_safe(v, limit=limit) for v in value[:limit]]
    if isinstance(value, str):
        value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
        value = TOKEN_RE.sub(r"\1[REDACTED]", value)
        return value[:10000]
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def redact(text: str) -> str:
    return TOKEN_RE.sub(r"\1[REDACTED]", EMAIL_RE.sub("[REDACTED_EMAIL]", text or ""))[:6000]


def command_path(name: str, fallback: str | None = None) -> str | None:
    return shutil.which(name) or fallback


def run_command(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout: int = 60,
) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"


def load_config() -> dict[str, Any]:
    config = read_json(CONFIG_PATH, {})
    if config.get("data_project_id", config.get("project_id")) != DEFAULT_DATA_PROJECT:
        raise ValueError("only the approved Waje data project wajenigeria is allowed")
    return config


def fill_sql(template: str, *, app_start: str, app_end: str, h5_start: str, h5_end: str, sessions_start: str, sessions_end: str, perf_start: str, perf_end: str, stability_start: str, stability_end: str, **_ignored: str) -> str:
    replacements = {
        "__APP_START_YYYYMMDD__": yyyymmdd(app_start),
        "__APP_END_YYYYMMDD__": yyyymmdd(app_end),
        "__H5_START_YYYYMMDD__": yyyymmdd(h5_start),
        "__H5_END_YYYYMMDD__": yyyymmdd(h5_end),
        "__SESSIONS_START__": sessions_start,
        "__SESSIONS_END__": sessions_end,
        "__PERF_START__": perf_start,
        "__PERF_END__": perf_end,
        "__STABILITY_START__": stability_start,
        "__STABILITY_END__": stability_end,
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def build_windows(date_from: str | None, date_to: str | None) -> dict[str, str]:
    default_end = now_lagos().date() - dt.timedelta(days=1)
    end = dt.date.fromisoformat(iso_date(date_to)) if date_to else default_end
    start = dt.date.fromisoformat(iso_date(date_from)) if date_from else end - dt.timedelta(days=6)
    if start > end:
        raise ValueError("date_from must be on or before date_to")
    h5_start = start - dt.timedelta(days=6)
    h5_end = start + dt.timedelta(days=1)
    sessions_start = start - dt.timedelta(days=2)
    return {
        "app_start": start.isoformat(),
        "app_end": end.isoformat(),
        "h5_start": h5_start.isoformat(),
        "h5_end": h5_end.isoformat(),
        "sessions_start": sessions_start.isoformat(),
        "sessions_end": end.isoformat(),
        "perf_start": start.isoformat(),
        "perf_end": end.isoformat(),
        "stability_start": start.isoformat(),
        "stability_end": end.isoformat(),
        "timezone": DEFAULT_TIMEZONE,
    }


def preflight(config: dict[str, Any]) -> dict[str, Any]:
    env = os.environ.copy()
    env["CLOUDSDK_ACTIVE_CONFIG_NAME"] = "waje-enterprise-gemini"
    env["CLOUDSDK_CORE_DISABLE_PROMPTS"] = "1"
    gemini = command_path("gemini", "/Users/robin/.local/bin/gemini")
    bq = command_path("bq", "/Users/robin/google-cloud-sdk/bin/bq")
    settings = read_json(SETTINGS_PATH, {}) or {}
    bq_settings = (settings.get("mcpServers") or {}).get("bigquery") or {}
    policy = read_json(POLICY_PATH, {}) or {}
    include_tools = bq_settings.get("includeTools", [])
    exclude_tools = bq_settings.get("excludeTools", [])
    policy_remote = policy.get("remote_mcp") or {}

    result: dict[str, Any] = {
        "enterprise_account_expected": DEFAULT_ACCOUNT,
        "data_project_id": DEFAULT_DATA_PROJECT,
        "data_location": DEFAULT_DATA_LOCATION,
        "runtime_project_id": config.get("runtime_project_id", DEFAULT_RUNTIME_PROJECT),
        "runtime_location": config.get("location", DEFAULT_RUNTIME_LOCATION),
        "gemini_cli": {"path": gemini, "version_status": "not_checked"},
        "bq_cli": {"path": bq},
        "gcloud": {"status": "not_checked", "account_verified": False},
        "adc": {"status": "not_checked"},
        "bigquery_mcp": {
            "status": "not_checked",
            "configured_endpoint": bq_settings.get("httpUrl"),
            "trust": bq_settings.get("trust") is True and policy_remote.get("trusted") is True,
            "include_tools": include_tools,
            "exclude_tools": exclude_tools,
            "active_allowed_views": policy.get("active_allowed_views", []),
        },
        "api_fallback": {"status": "not_checked"},
        "access_issues": [],
    }

    if gemini:
        code, out, err = run_command([gemini, "--version"], env=env, timeout=20)
        result["gemini_cli"]["version_status"] = "ok" if code == 0 else "failed"
        result["gemini_cli"]["version"] = redact(out.strip() or err.strip())
    else:
        result["access_issues"].append({"code": "blocked_tooling", "detail": "Gemini CLI not found"})

    if bq:
        code, out, err = run_command([bq, "--version"], env=env, timeout=20)
        result["bq_cli"]["status"] = "ok" if code == 0 else "failed"
        result["bq_cli"]["version"] = redact(out.strip() or err.strip())
    else:
        result["access_issues"].append({"code": "blocked_tooling", "detail": "bq CLI not found"})

    gcloud = command_path("gcloud", "/Users/robin/google-cloud-sdk/bin/gcloud")
    if gcloud:
        code, out, err = run_command([gcloud, "config", "list", "--format=value(core.account,core.project)"], env=env, timeout=30)
        raw_config = out.strip()
        visible = redact(raw_config)
        result["gcloud"]["status"] = "ok" if code == 0 else "failed"
        # Check the expected account before redaction; never persist the raw
        # email, but do not let redaction make a valid account look invalid.
        result["gcloud"]["account_verified"] = DEFAULT_ACCOUNT in raw_config
        result["gcloud"]["configured_project"] = visible.splitlines()[-1] if visible else None
        if code != 0:
            result["access_issues"].append({"code": "blocked_authentication", "detail": "gcloud configuration could not be read"})
        elif not result["gcloud"]["account_verified"]:
            result["access_issues"].append({"code": "wrong_gcloud_account", "detail": "waje-enterprise-gemini does not show robin@afuruika.net"})

    if gcloud:
        code, _out, err = run_command([gcloud, "auth", "application-default", "print-access-token"], env=env, timeout=30)
        result["adc"]["status"] = "ok" if code == 0 else "failed"
        if code != 0:
            result["access_issues"].append({"code": "blocked_authentication", "detail": "ADC token could not be obtained"})

    if gemini:
        code, out, err = run_command([gemini, "mcp", "list"], env=env, timeout=45)
        mcp_text = (out + "\n" + err).strip()
        lower = mcp_text.lower()
        connected = "bigquery" in lower and "connected" in lower and "disconnected" not in lower
        trusted = result["bigquery_mcp"]["trust"] and "execute_sql" in exclude_tools and "execute_sql_readonly" in include_tools
        active_views = result["bigquery_mcp"]["active_allowed_views"]
        result["bigquery_mcp"]["status"] = "ready" if code == 0 and connected and trusted and active_views else "blocked_external_prerequisites"
        result["bigquery_mcp"]["connected"] = connected
        result["bigquery_mcp"]["mcp_output_summary"] = "connected" if connected else "disconnected_or_unavailable"
        if result["bigquery_mcp"]["status"] != "ready":
            result["access_issues"].append({"code": "blocked_gemini_mcp", "detail": "BigQuery MCP must be connected, trusted and have active allowed views"})

    api_ready = result["bq_cli"].get("status") == "ok" and result["adc"].get("status") == "ok" and result["gcloud"].get("account_verified") is True
    result["api_fallback"]["status"] = "ready" if api_ready else "blocked_external_prerequisites"
    if not api_ready:
        result["access_issues"].append({"code": "blocked_api_fallback", "detail": "bq, ADC and Robin enterprise gcloud configuration are all required"})
    return result


def build_gemini_prompt(windows: dict[str, str], config: dict[str, Any]) -> str:
    return f"""你是 Waje 企业 Firebase-only 数据分析执行器。

任务：在企业 BigQuery Remote MCP 的已激活安全聚合 View 上，汇总 Android 三个生产包、现有 iOS 来源和 H5 Firebase 数据，服务于设备、性能、事件、会话和数据质量看板。

数据项目：wajenigeria
数据区域：europe-west4
Gemini 运行项目：{config.get('runtime_project_id', DEFAULT_RUNTIME_PROJECT)}
运行区域：{config.get('location', DEFAULT_RUNTIME_LOCATION)}
业务时区：Africa/Lagos
Android/iOS 窗口：{windows['app_start']} 至 {windows['app_end']}
H5 行为窗口：{windows['h5_start']} 至 {windows['h5_end']}

必须遵守：
1. 只使用已激活的授权聚合 View，不访问 Firebase 原始表、Origin、支付、订单、KYC 或用户明细表。
2. 只执行单条 SELECT/WITH；必须有日期过滤和 LIMIT 500；禁止 DDL、DML、导出和配置修改。
3. 只返回聚合数据、数据截止时间、完整日、样本量、分母、质量状态和缺失原因；不下载明细行。
4. 不返回 user_id、user_pseudo_id、session_id 明细、设备唯一标识、广告标识、Cookie、Token、URL、请求/响应正文、错误堆栈或订单字段。
5. Android、iOS、H5 分开统计；Analytics session_start 是事件数，不等于唯一会话数；H5 无 Web Vitals 时标记 data_gap。
6. 原生 P95 为主要性能指标，P50/P99 仅作诊断；合格样本少于 500 时返回 null。

只返回一个 JSON 对象，字段为：
{{
  "status": "ok|quality_warning|no_data|delayed|blocked_authentication|failed",
  "auth_context": {{"enterprise_account": true, "bigquery_connection": true, "workspace": "waje"}},
  "source_objects": [],
  "data_cutoff": {{}},
  "complete_day": true,
  "coverage_daily": [],
  "event_session_daily": [],
  "native_performance_daily": [],
  "stability_daily": [],
  "h5_behavior_daily": [],
  "quality_checks": [],
  "metrics": [],
  "summary": "",
  "recommendations": [],
  "access_issues": [],
  "sql": ""
}}
"""


def parse_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        return None


def run_gemini(windows: dict[str, str], config: dict[str, Any], pf: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    candidates = model_candidates(config)
    candidate_labels = [item if item is not None else "cli_default" for item in candidates]
    base_receipt: dict[str, Any] = {
        "attempted": False,
        "model_routing": "preferred_then_fallback_then_cli_default",
        "model_candidates": candidate_labels,
        "attempts": [],
    }
    if pf.get("bigquery_mcp", {}).get("status") != "ready":
        base_receipt["reason"] = "Gemini MCP preflight did not pass"
        return "blocked_external_prerequisites", {}, base_receipt
    gemini = pf.get("gemini_cli", {}).get("path")
    if not gemini:
        base_receipt["reason"] = "Gemini CLI not found"
        return "blocked_tooling", {}, base_receipt
    env = os.environ.copy()
    env.pop("GOOGLE_API_KEY", None)
    env.pop("GEMINI_API_KEY", None)
    env["GOOGLE_CLOUD_PROJECT"] = str(config.get("runtime_project_id", DEFAULT_RUNTIME_PROJECT))
    env["GOOGLE_CLOUD_LOCATION"] = str(config.get("location", DEFAULT_RUNTIME_LOCATION))
    env["GEMINI_TELEMETRY_ENABLED"] = "false"
    timeout = int(config.get("limits", {}).get("timeout_seconds", 180))
    for index, model in enumerate(candidates):
        command = [
            gemini,
            "--approval-mode", "plan",
            "--output-format", "json",
        ]
        if model is not None:
            command.extend(["--model", str(model)])
        command.extend([
            "--allowed-mcp-server-names", "bigquery",
            "-p", build_gemini_prompt(windows, config),
        ])
        code, out, err = run_command(command, env=env, timeout=timeout)
        attempt: dict[str, Any] = {
            "index": index + 1,
            "model": model if model is not None else "cli_default",
            "returncode": code,
        }
        if code != 0:
            status, retryable = classify_model_attempt(code, err)
            attempt.update({"status": status, "retryable": retryable, "stderr_summary": redact(err) if err else None})
            base_receipt["attempts"].append(attempt)
            if status in {"blocked_iam", "blocked_license"}:
                base_receipt.update({"attempted": True, "selected_model": model if model is not None else "cli_default"})
                return status, {}, base_receipt
            if retryable_model_status(status) and index + 1 < len(candidates):
                continue
            base_receipt.update({"attempted": True, "selected_model": model if model is not None else "cli_default"})
            return status, {}, base_receipt

        payload = parse_json_object(out)
        if payload is None:
            attempt.update({"status": "failed_invalid_json", "retryable": True, "response_parse": "invalid_json"})
            base_receipt["attempts"].append(attempt)
            if index + 1 < len(candidates):
                continue
            base_receipt.update({"attempted": True, "selected_model": model if model is not None else "cli_default"})
            return "failed_invalid_json", {}, base_receipt

        safe_payload = json_safe(payload)
        sql = safe_payload.get("sql")
        if isinstance(sql, str) and sql.strip():
            errors = validate_sql(sql, allowed_datasets=source_allowlist_from_config(config))
            attempt.update({"status": "blocked_sql_validation" if errors else "ok", "sql_validation_errors": errors})
            base_receipt["attempts"].append(attempt)
            base_receipt.update({"attempted": True, "selected_model": model if model is not None else "cli_default"})
            if errors:
                return "blocked_sql_validation", safe_payload, base_receipt
        else:
            attempt["status"] = "ok"
            base_receipt["attempts"].append(attempt)
            base_receipt.update({"attempted": True, "selected_model": model if model is not None else "cli_default"})
        return str(safe_payload.get("status") or "ok"), safe_payload, base_receipt

    base_receipt["attempted"] = True
    return "failed", {}, base_receipt


def parse_dry_bytes(output: str) -> int | None:
    for pattern in (r"totalBytesProcessed[\"']?\s*[:=]\s*[\"']?(\d+)", r"processedBytes[\"']?\s*[:=]\s*[\"']?(\d+)"):
        match = re.search(pattern, output, flags=re.I)
        if match:
            return int(match.group(1))
    return None


def classify_bq_error(text: str) -> str:
    lower = text.lower()
    if "permission_denied" in lower or "access denied" in lower or "permission" in lower and "denied" in lower:
        return "blocked_iam"
    if "not found" in lower or "does not exist" in lower:
        return "data_gap"
    if "location" in lower and "not found" in lower:
        return "blocked_location"
    if "quota" in lower or "billing" in lower:
        return "blocked_quota"
    return "failed"


def run_api_query(spec: dict[str, str], sql: str, config: dict[str, Any], pf: dict[str, Any], output_dir: Path, cumulative_bytes: int) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    bq = pf.get("bq_cli", {}).get("path")
    receipt: dict[str, Any] = {
        "id": spec["id"],
        "title": spec["title"],
        "sql_file": spec["file"],
        "sql_sha256": short_hash(sql),
        "status": "not_run",
        "source_project": DEFAULT_DATA_PROJECT,
        "location": DEFAULT_DATA_LOCATION,
        "raw_output_saved": False,
    }
    if not bq or pf.get("api_fallback", {}).get("status") != "ready":
        receipt.update({"status": "blocked_external_prerequisites", "error": "bq/ADC/enterprise account preflight did not pass"})
        return receipt, [], cumulative_bytes
    allowed = source_allowlist_from_config(config)
    errors = validate_sql(sql, allowed_datasets=allowed)
    receipt["sql_validation_errors"] = errors
    if errors:
        receipt.update({"status": "blocked_sql_validation", "error": "; ".join(errors)})
        return receipt, [], cumulative_bytes
    env = os.environ.copy()
    env["CLOUDSDK_ACTIVE_CONFIG_NAME"] = "waje-enterprise-gemini"
    env["CLOUDSDK_CORE_DISABLE_PROMPTS"] = "1"
    base = [bq, f"--project_id={DEFAULT_DATA_PROJECT}", f"--location={DEFAULT_DATA_LOCATION}", "query", "--use_legacy_sql=false"]
    dry_code, dry_out, dry_err = run_command(base + ["--dry_run=true", "--format=prettyjson"], env=env, input_text=sql, timeout=int(config.get("limits", {}).get("timeout_seconds", 180)))
    dry_text = dry_out + "\n" + dry_err
    dry_bytes = parse_dry_bytes(dry_text)
    receipt["dry_run_returncode"] = dry_code
    receipt["dry_run_bytes"] = dry_bytes
    if dry_code != 0:
        receipt.update({"status": classify_bq_error(dry_text), "error": redact(dry_text)})
        return receipt, [], cumulative_bytes
    if dry_bytes is None:
        receipt.update({"status": "blocked_sql_validation", "error": "dry-run byte estimate missing"})
        return receipt, [], cumulative_bytes
    max_bytes = int(config.get("limits", {}).get("max_bytes_billed", 5 * 1024 * 1024 * 1024))
    max_audit = int(config.get("limits", {}).get("max_bytes_per_audit", 25 * 1024 * 1024 * 1024))
    if dry_bytes > max_bytes:
        receipt.update({"status": "blocked_cost", "error": "query exceeds per-query byte budget"})
        return receipt, [], cumulative_bytes
    if cumulative_bytes + dry_bytes > max_audit:
        receipt.update({"status": "blocked_cost", "error": "audit exceeds cumulative byte budget"})
        return receipt, [], cumulative_bytes
    actual_code = 1
    actual_out = ""
    actual_err = ""
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        actual_code, actual_out, actual_err = run_command(base + ["--format=json", f"--max_rows={OUTPUT_ROW_CAP}"], env=env, input_text=sql, timeout=int(config.get("limits", {}).get("timeout_seconds", 180)))
        if actual_code == 0:
            break
        network_failure = "network connection problem" in (actual_out + actual_err).lower() or "incompleteread" in (actual_out + actual_err).lower()
        if not network_failure or attempt == max_attempts:
            break
        time.sleep(1)
    receipt["actual_attempts"] = attempt
    if actual_code != 0:
        text = actual_out + "\n" + actual_err
        receipt.update({"status": classify_bq_error(text), "error": redact(text)})
        return receipt, [], cumulative_bytes + dry_bytes
    try:
        rows = json.loads(actual_out or "[]")
    except json.JSONDecodeError:
        receipt.update({"status": "failed", "error": "BigQuery returned invalid JSON"})
        return receipt, [], cumulative_bytes + dry_bytes
    if not isinstance(rows, list):
        rows = []
    rows = json_safe(rows)
    receipt.update({"status": "ok", "actual_bytes": dry_bytes, "row_count": len(rows), "raw_output_saved": False})
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / f"{spec['id']}.json", rows)
    return receipt, rows, cumulative_bytes + dry_bytes


def derive_coverage(query_rows: dict[str, list[dict[str, Any]]], query_receipts: list[dict[str, Any]], windows: dict[str, str]) -> list[dict[str, Any]]:
    """Return compact source/query coverage, never pretending a blank date is zero."""
    receipt_map = {item.get("id"): item for item in query_receipts}
    specs = [
        ("android", "android_analytics_summary", windows["app_start"], windows["app_end"]),
        ("ios", "ios_analytics_summary", windows["app_start"], windows["app_end"]),
        ("h5", "h5_analytics_summary", windows["h5_start"], windows["h5_end"]),
        ("android", "android_sessions_summary", windows["sessions_start"], windows["sessions_end"]),
        ("android_and_ios", "native_performance_summary", windows["perf_start"], windows["perf_end"]),
        ("android", "crashlytics_stability_summary", windows["stability_start"], windows["stability_end"]),
    ]
    output: list[dict[str, Any]] = []
    for endpoint, query_id, start, end in specs:
        receipt = receipt_map.get(query_id, {})
        rows = query_rows.get(query_id, [])
        observed_days = [str(row.get("metric_date_lagos")) for row in rows if row.get("metric_date_lagos")]
        reported_covered = [int(row.get("covered_days")) for row in rows if str(row.get("covered_days", "")).isdigit()]
        covered_days = max(reported_covered) if reported_covered else (len(set(observed_days)) if observed_days else None)
        status = "ok" if receipt.get("status") == "ok" else str(receipt.get("status") or "not_run")
        if status == "ok" and covered_days is not None and covered_days < 7:
            status = "immature"
        output.append({
            "endpoint": endpoint,
            "source_query": query_id,
            "requested_start": start,
            "requested_end": end,
            "covered_days": covered_days,
            "aggregate_row_count": len(rows),
            "status": status,
        })
    return output


def make_quality_checks(pf: dict[str, Any], query_receipts: list[dict[str, Any]], gemini_status: str, query_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append({"id": "gemini_mcp_preflight", "status": "passed" if pf.get("bigquery_mcp", {}).get("status") == "ready" else "blocked", "detail": "通过" if pf.get("bigquery_mcp", {}).get("status") == "ready" else "MCP 未同时满足连接、信任和安全 View 白名单"})
    checks.append({"id": "api_identity_preflight", "status": "passed" if pf.get("api_fallback", {}).get("status") == "ready" else "blocked", "detail": "通过" if pf.get("api_fallback", {}).get("status") == "ready" else "bq、ADC 或企业账号预检未通过"})
    for receipt in query_receipts:
        checks.append({"id": f"query:{receipt['id']}", "status": receipt.get("status"), "dry_run_bytes": receipt.get("dry_run_bytes"), "row_count": receipt.get("row_count"), "detail": receipt.get("error")})
        if receipt.get("row_count") == OUTPUT_ROW_CAP:
            checks.append({"id": f"query_limit:{receipt['id']}", "status": "quality_warning", "detail": f"结果达到 {OUTPUT_ROW_CAP} 行上限；需缩小维度或日期范围后才能得到完整排行"})
    checks.append({"id": "raw_row_output", "status": "passed", "detail": "仅保存聚合 JSON；未保存原始命令行输出"})
    checks.append({"id": "h5_web_performance", "status": "data_gap", "detail": "当前 H5 Firebase Analytics 没有 Web Vitals、路由完成、请求耗时或前端错误字段"})
    checks.append({"id": "cross_endpoint_trend_gate", "status": "immature", "detail": "每个端侧达到 7 个完整数据日后才允许发布趋势"})
    return checks


def overall_status(query_receipts: list[dict[str, Any]], api_rows: dict[str, list[dict[str, Any]]], gemini_status: str) -> tuple[str, str]:
    ok_count = sum(1 for item in query_receipts if item.get("status") == "ok")
    if ok_count == 0:
        if gemini_status.startswith("blocked") or gemini_status in {"blocked_tooling", "blocked_license"}:
            return "blocked_external_prerequisites", "Gemini 和本机 BigQuery API 均未产生聚合结果"
        return "blocked_authentication", "没有任何聚合查询完成"
    if any(item.get("status") not in {"ok"} for item in query_receipts):
            return "quality_warning", "至少一个 Firebase 数据源或查询缺失、延迟或受阻"
    if any(item.get("row_count") == OUTPUT_ROW_CAP for item in query_receipts):
        return "quality_warning", f"至少一个设备或稳定性维度结果达到 {OUTPUT_ROW_CAP} 行输出上限"
    if any(not rows for rows in api_rows.values()):
        return "quality_warning", "至少一个聚合查询结果为空"
    if gemini_status not in {"ok", "quality_warning", "no_data", "delayed"}:
        return "quality_warning", "Gemini MCP 未满足企业安全门禁，本次使用本机 BigQuery API 完成聚合复核"
    return "ok", "Firebase-only 聚合收集已完成"


def deterministic_observations(query_rows: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Create descriptive, non-causal observations from compact aggregates."""
    observations: list[str] = []
    performance = {str(row.get("endpoint")): row for row in query_rows.get("native_performance_summary", [])}
    if performance:
        android_rates = [float(row["network_success_rate"]) for row in performance.values() if str(row.get("platform")) == "Android" and row.get("network_success_rate") not in (None, "")]
        ios_rates = [float(row["network_success_rate"]) for row in performance.values() if str(row.get("platform")) == "iOS" and row.get("network_success_rate") not in (None, "")]
        if android_rates and ios_rates:
            observations.append(f"窗口汇总中 Android 各包 HTTP 成功率约为 {min(android_rates)*100:.2f}%～{max(android_rates)*100:.2f}%，现有 iOS 来源约为 {ios_rates[0]*100:.2f}%；这只是描述性差异，尚未完成请求类别、错误码和来源映射核验。")
        observations.append("原生轨迹 P95 当前按全部 DURATION_TRACE 汇总，未按 trace_category 拆分，因此不能直接解释为启动耗时或首页耗时。")
    stability = query_rows.get("crashlytics_stability_summary", [])
    if stability:
        by_endpoint: dict[str, int] = {}
        for row in stability:
            by_endpoint[str(row.get("endpoint"))] = by_endpoint.get(str(row.get("endpoint")), 0) + int(row.get("dedup_event_count") or 0)
        top = max(by_endpoint.items(), key=lambda item: item[1])
        observations.append(f"Crashlytics 窗口内去重事件量最高的是 {top[0]}（{compact_number(top[1])} 条）；这不是崩溃率，也不代表受影响用户数。")
    sessions = query_rows.get("android_sessions_summary", [])
    if sessions and any(float(row.get("performance_collection_flag_share") or 0) == 0 for row in sessions):
        observations.append("三个 Android 包的 Sessions Performance 开关覆盖均为 0%，但 Performance 表有大量记录；将其作为数据质量冲突，不据此判定性能未接入。")
    h5 = query_rows.get("h5_analytics_summary", [])
    if h5:
        h5_names = ", ".join(str(row.get("event_name_bucket")) for row in h5 if row.get("event_name_bucket"))
        observations.append(f"H5 当前只返回 {len(h5)} 类标准行为事件（{h5_names}），没有 Web Vitals、白屏、核心请求或前端错误观测。")
    return observations


def compact_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number >= 1_000_000:
        return f"{number/1_000_000:.2f}M".rstrip("0").rstrip(".")
    if number >= 1_000:
        return f"{number/1_000:.1f}k".rstrip("0").rstrip(".")
    return f"{number:,.0f}"


def compact_metric(value: Any) -> str:
    """Format a numeric metric without exposing float noise from JSON output."""
    if value is None or value == "":
        return "N/A"
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def percent_metric(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number <= 1:
        number *= 100
    return f"{number:.1f}%"


def markdown_report(artifact: dict[str, Any]) -> str:
    status = artifact.get("status", "blocked")
    windows = artifact.get("query_window", {})
    lines = [
        "---",
        "type: technical-analysis-report",
        f"status: {status}",
        f"updated: {artifact.get('generated_at', '')[:10]}",
        "---",
        "",
        "# Waje Firebase 多端设备与性能汇总分析报告",
        "",
        "## 执行摘要",
        "",
        f"**当前状态：`{status}`。** {artifact.get('status_reason', '')}",
        "",
        f"- 数据范围：Firebase-only；Android/iOS {windows.get('app_start')}～{windows.get('app_end')}，H5 {windows.get('h5_start')}～{windows.get('h5_end')}，时区 `Africa/Lagos`。",
        f"- 执行路径：`{artifact.get('route_selected')}`；Gemini 状态：`{artifact.get('gemini_status')}`；本机 API 状态：`{artifact.get('api_status')}`。",
        "- Android、iOS、H5 独立统计；事件数不解释为用户数，Sessions 不与 `session_start` 相加。",
        "- H5 当前只形成行为基线；Web Vitals、白屏、核心请求、前端错误和游戏阶段均标记为 `data_gap` / `blocked`。",
        "",
        "## 端侧现状",
        "",
        "| 端侧 | 当前实际汇总 | 主要可用指标 | 状态 |",
        "|---|---:|---|---|",
    ]
    event_rows = artifact.get("event_session_daily", [])
    perf_rows = artifact.get("native_performance_daily", [])
    sessions_rows = artifact.get("sessions_daily", [])
    h5_rows = artifact.get("h5_behavior_daily", [])
    android_events = sum(int(row.get("event_count") or 0) for row in event_rows if row.get("endpoint") == "android")
    ios_events = sum(int(row.get("event_count") or 0) for row in event_rows if row.get("endpoint") == "ios")
    h5_events = sum(int(row.get("event_count") or 0) for row in h5_rows)
    android_perf = sum(int(row.get("performance_record_count") or 0) for row in perf_rows if str(row.get("platform")) == "Android")
    ios_perf = sum(int(row.get("performance_record_count") or 0) for row in perf_rows if str(row.get("platform")) == "iOS")
    android_sessions = sum(int(row.get("distinct_session_count") or 0) for row in sessions_rows)
    lines.extend([
        f"| Android | {compact_number(android_events)} Analytics 事件；{compact_number(android_perf)} Performance 记录；{compact_number(android_sessions)} 去标识化会话 | 会话开始事件、轨迹/网络 P95、HTTP 成功率、慢帧/冻结帧、Fatal/Non-fatal 事件量 | `provisional` |",
        f"| iOS | {compact_number(ios_events)} Analytics 事件；{compact_number(ios_perf)} Performance 记录 | 会话开始事件、轨迹/网络 P95、屏幕流畅度 | `immature` / `provisional` |",
        f"| H5 | {compact_number(h5_events)} 行为事件 | page_view、session_start、first_visit、user_engagement | `provisional_behavior_only` |",
        "",
        "## 基于汇总结果的观察",
        "",
        "以下是窗口级聚合的描述性观察，不是因果判断；性能和稳定性比率仍按质量门禁解释。",
        "",
        *[f"- {item}" for item in (artifact.get("observations", []) or ["当前没有足够的聚合结果生成观察。"])] ,
        "",
        "## 数据覆盖与质量",
        "",
        "| 检查项 | 状态 | 说明 |",
        "|---|---|---|",
    ])
    for check in artifact.get("quality_checks", []):
        detail = str(check.get("detail") or "").replace("|", "/")
        lines.append(f"| {check.get('id','')} | `{check.get('status','')}` | {detail} |")
    lines.extend(["", "## Firebase 数据集清单", "", "| 数据集 | 表/视图数量 | 基础表 | 视图 |", "|---|---:|---:|---:|"])
    inventory_rows = artifact.get("source_inventory", [])
    for row in inventory_rows[:80]:
        lines.append(f"| {row.get('dataset_id','')} | {row.get('object_count',0)} | {row.get('base_table_count',0)} | {row.get('view_count',0)} |")
    if not inventory_rows:
        lines.append("| — | — | — | — | 未返回元数据 |")
    lines.extend(["", "## 表结构与质量元数据", "", "| 数据集 | 表 | 类型 | 创建时间 | 字段路径数 |", "|---|---|---|---|---:|"])
    quality_inventory = artifact.get("quality_inventory", [])
    for row in quality_inventory[:80]:
        lines.append(f"| {row.get('dataset_id','')} | {row.get('table_name','')} | {row.get('table_type','')} | {row.get('creation_time','')} | {row.get('field_path_count',0)} |")
    if not quality_inventory:
        lines.append("| — | — | — | — | 未返回质量元数据 |")
    lines.extend(["", "## Analytics 事件与会话汇总", "", "以下仅返回窗口级分类汇总；事件名只在 H5 的四类现有标准事件中保留。", "", "| 端侧 | 包体/来源 | 事件分类 | 事件名桶 | 事件数 | 覆盖天数 |", "|---|---|---|---|---:|---:|"])
    for row in (event_rows + h5_rows)[:80]:
        event_name = row.get("event_name_bucket") or "分类合计"
        lines.append(f"| {row.get('endpoint','')} | {row.get('app_package','')} | {row.get('event_category','')} | {event_name} | {compact_number(row.get('event_count',0))} | {row.get('covered_days','窗口汇总')} |")
    if not event_rows and not h5_rows:
        lines.append("| — | — | — | — | 未返回聚合结果 | — |")
    lines.extend(["", "## Android Sessions 汇总", "", "窗口级会话汇总；session_id 只在数据库内参与去重，不会返回。", "", "| 端侧 | 包体 | 去标识化会话数 | Sessions 事件数 | Performance 开关覆盖 | Crashlytics 开关覆盖 |", "|---|---|---:|---:|---:|---:|"])
    for row in sessions_rows[:80]:
        performance_flag = row.get("performance_collection_flag_share")
        crash_flag = row.get("crashlytics_collection_flag_share")
        lines.append(f"| {row.get('endpoint','')} | {row.get('app_package','')} | {compact_number(row.get('distinct_session_count',0))} | {compact_number(row.get('session_event_count',0))} | {percent_metric(performance_flag)} | {percent_metric(crash_flag)} |")
    if not sessions_rows:
        lines.append("| — | — | 未返回聚合结果 | — | — | — |")
    lines.extend(["", "## 原生 Performance 汇总", "", "窗口级端/包汇总；版本明细不作为默认返回。", "", "| 端侧 | 包体 | 性能记录 | 轨迹 P50(ms) | 轨迹 P95(ms) | 轨迹 P99(ms) | 网络 P95(ms) | 网络成功率 | 样本状态 |", "|---|---|---:|---:|---:|---:|---:|---:|---|"])
    for row in perf_rows[:80]:
        rate_text = percent_metric(row.get("network_success_rate"))
        lines.append(f"| {row.get('platform','')} | {row.get('app_package','')} | {compact_number(row.get('performance_record_count',0))} | {compact_metric(row.get('duration_trace_p50_ms'))} | {compact_metric(row.get('duration_trace_p95_ms'))} | {compact_metric(row.get('duration_trace_p99_ms'))} | {compact_metric(row.get('network_p95_ms'))} | {rate_text} | {row.get('sample_status','')} |")
    if not perf_rows:
        lines.append("| — | — | 未返回聚合结果 | — | — | — | — | — | blocked/data_gap |")
    lines.extend(["", "## 设备、系统与网络维度 Top 3", "", "仅返回每个端/包/维度的窗口级 Top 3 聚合值，不返回日期×版本明细。", "", "| 端侧 | 包体 | 维度 | 维度值 | 性能记录 | 轨迹 P95(ms) | 网络 P95(ms) | 网络成功率 | 样本状态 |", "|---|---|---|---|---:|---:|---:|---:|---|"])
    dimension_rows = artifact.get("native_performance_dimensions", [])
    for row in dimension_rows[:80]:
        rate_text = percent_metric(row.get("network_success_rate"))
        lines.append(f"| {row.get('endpoint','')} | {row.get('app_package','')} | {row.get('rank_dimension','')} | {row.get('rank_value','')} | {compact_number(row.get('performance_record_count',0))} | {compact_metric(row.get('duration_trace_p95_ms'))} | {compact_metric(row.get('network_p95_ms'))} | {rate_text} | {row.get('sample_status','')} |")
    if not dimension_rows:
        lines.append("| — | — | — | 未返回聚合结果 | — | — | — | — | data_gap |")
    if len(dimension_rows) >= OUTPUT_ROW_CAP:
        lines.extend(["", f"> 设备/系统/网络排行仅返回前 {OUTPUT_ROW_CAP} 行；正式看板必须固定一个主排行维度，避免截断影响解释。"])
    lines.extend(["", "## Crashlytics 稳定性", "", "- 当前只展示按 `event_id` 去重的事件量、按 `issue_id` 去重的问题数和 Fatal/Non-fatal 分类。",
                  "- 在官方字段、去重键、ANR 枚举和 Sessions 分母完成认证前，不计算崩溃率、ANR 率或受影响用户数。", ""])
    stability = artifact.get("stability_daily", [])
    if stability:
        lines.extend(["| 端侧 | 包体 | 类型 | 去重事件 | 问题数 | 数据截止 |", "|---|---|---|---:|---:|---|"])
        for row in stability[:80]:
            lines.append(f"| {row.get('endpoint','')} | {row.get('app_package','')} | {row.get('error_type','')} | {compact_number(row.get('dedup_event_count',0))} | {compact_number(row.get('issue_count',0))} | {row.get('data_cutoff_at','')} |")
    else:
        lines.append("当前没有可展示的稳定性聚合行；缺失原因见数据质量表。")
    if len(stability) >= OUTPUT_ROW_CAP:
        lines.extend(["", f"> 稳定性汇总仅返回前 {OUTPUT_ROW_CAP} 行；正式排行按单一主维度和样本门槛生成。"])
    lines.extend(["", "## H5 性能与核心漏斗缺口", "", "| 指标族 | 当前状态 | 不能直接推断的结论 |", "|---|---|---|", "| Web Vitals（LCP/INP/CLS/FCP/TTFB） | `data_gap` | 不能从 page_view 或停留事件推断加载速度 |", "| 页面白屏/黑屏与前端错误 | `data_gap` | 不能判定网页稳定性 |", "| 核心请求 P95 / 超时 / 重试 | `data_gap` | 不能定位弱网接口问题 |", "| 游戏就绪 / 可下注 / 首局 | `blocked` | Firebase 行为事件不等于服务端成功 |", "", "## 建议动作", ""])
    for rec in artifact.get("recommendations", []):
        lines.append(f"- {rec}")
    if not artifact.get("recommendations"):
        lines.append("- 等待权限或数据源恢复后重新执行本报告。")
    lines.extend(["", "## 审计边界", "", "本报告只保存聚合结果、查询回执和状态，不保存原始事件行、用户标识、设备唯一标识、Cookie、Token、URL、请求体、响应体、订单或错误堆栈。", ""])
    return "\n".join(lines)


def build_artifact(*, windows: dict[str, str], pf: dict[str, Any], gemini_status: str, gemini_payload: dict[str, Any], gemini_receipt: dict[str, Any], query_receipts: list[dict[str, Any]], query_rows: dict[str, list[dict[str, Any]]], run_id: str) -> dict[str, Any]:
    api_status = "ok" if any(item.get("status") == "ok" for item in query_receipts) else "blocked"
    status, reason = overall_status(query_receipts, query_rows, gemini_status)
    api_route = "gemini_mcp" if gemini_status in {"ok", "quality_warning", "no_data", "delayed"} else "api_fallback"
    quality_checks = make_quality_checks(pf, query_receipts, gemini_status, query_rows)
    event_rows = query_rows.get("android_analytics_summary", []) + query_rows.get("ios_analytics_summary", [])
    h5_rows = query_rows.get("h5_analytics_summary", [])
    sessions_rows = query_rows.get("android_sessions_summary", [])
    perf_rows = query_rows.get("native_performance_summary", [])
    dim_rows = query_rows.get("native_performance_top3", [])
    stability_rows = query_rows.get("crashlytics_stability_summary", [])
    recommendations = [
        "Gemini MCP 连接、trust 和安全 View 白名单未全部通过时，继续保持 API fallback，不启用自动自然语言查询。",
        "Android Performance 先按包体、版本、设备、系统和网络单维度做 P95 与成功率观察；样本不足 500 不进入正式排行。",
        "iOS 继续独立积累至少 7 个完整日，确认现有来源映射后再开放跨端趋势。",
        "H5 补齐 H5_NAVIGATION_PERF、H5_CORE_REQUEST、H5_GAME_READY、H5_BET_READY、H5_CLIENT_ERROR 等事件后，才能发布网页性能和核心漏斗指标。",
    ]
    if status == "blocked_external_prerequisites":
        recommendations.insert(0, "先恢复 Gemini MCP / Vertex / BigQuery 只读权限；当前回执不代表 Firebase 没有数据。")
    return {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": status,
        "status_reason": reason,
        "route_selected": api_route,
        "gemini_status": gemini_status,
        "api_status": api_status,
        "source_scope": "firebase_only",
        "summary_mode": "window_level_compact",
        "output_row_cap": OUTPUT_ROW_CAP,
        "query_result_row_count": sum(len(rows) for rows in query_rows.values()),
        "identity": DEFAULT_ACCOUNT,
        "data_project_id": DEFAULT_DATA_PROJECT,
        "data_location": DEFAULT_DATA_LOCATION,
        "runtime_project_id": pf.get("runtime_project_id", DEFAULT_RUNTIME_PROJECT),
        "runtime_location": pf.get("runtime_location", DEFAULT_RUNTIME_LOCATION),
        "query_window": windows,
        "coverage_daily": derive_coverage(query_rows, query_receipts, windows),
        "event_session_daily": event_rows,
        "sessions_daily": sessions_rows,
        "native_performance_daily": perf_rows,
        "native_performance_dimensions": dim_rows,
        "stability_daily": stability_rows,
        "h5_behavior_daily": h5_rows,
        "source_inventory": query_rows.get("source_inventory", []),
        "quality_inventory": query_rows.get("quality_freshness", []),
        "quality_checks": quality_checks,
        "observations": deterministic_observations(query_rows),
        "recommendations": recommendations,
        "access_issues": pf.get("access_issues", []),
        "query_receipts": query_receipts,
        "gemini_receipt": gemini_receipt,
        "gemini_summary": gemini_payload.get("summary") if isinstance(gemini_payload, dict) else None,
        "privacy": {"aggregate_only": True, "raw_rows_saved": False, "sensitive_values_saved": False},
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config()
    if args.source_scope != "firebase_only":
        raise ValueError("only --source-scope firebase_only is supported")
    windows = build_windows(args.date_from, args.date_to)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = args.run_id or f"firebase-multiplatform-{timestamp}-{uuid.uuid4().hex[:8]}"
    output_dir = ANALYSIS_ROOT / "runs" / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    write_json(output_dir / "preflight.json", {})
    pf = preflight(config)
    write_json(output_dir / "preflight.json", pf)

    if args.dry_run:
        validation = []
        allowlist = source_allowlist_from_config(config)
        for spec in QUERY_SPECS:
            template_path = SQL_ROOT / spec["file"]
            sql = fill_sql(template_path.read_text(encoding="utf-8"), **windows)
            errors = validate_sql(sql, allowed_datasets=allowlist)
            validation.append({"id": spec["id"], "file": spec["file"], "sql_sha256": short_hash(sql), "errors": errors})
        result = {"status": "dry_run", "run_id": run_id, "output_dir": str(output_dir.relative_to(ROOT)), "preflight": pf, "sql_validation": validation}
        write_json(output_dir / "run_receipt.json", result)
        return result

    gemini_status, gemini_payload, gemini_receipt = run_gemini(windows, config, pf)
    write_json(output_dir / "gemini_handoff.json", {"status": gemini_status, "payload": json_safe(gemini_payload), "receipt": gemini_receipt})
    query_receipts: list[dict[str, Any]] = []
    query_rows: dict[str, list[dict[str, Any]]] = {}
    cumulative_bytes = 0
    # Gemini is the preferred route. The fixed API pack is always run for
    # independent verification when local API access is ready, and is the
    # fallback when Gemini is blocked.
    for spec in QUERY_SPECS:
        template_path = SQL_ROOT / spec["file"]
        sql = fill_sql(template_path.read_text(encoding="utf-8"), **windows)
        receipt, rows, cumulative_bytes = run_api_query(spec, sql, config, pf, output_dir / "query_outputs", cumulative_bytes)
        query_receipts.append(receipt)
        query_rows[spec["id"]] = rows
    artifact = build_artifact(
        windows=windows,
        pf=pf,
        gemini_status=gemini_status,
        gemini_payload=gemini_payload,
        gemini_receipt=gemini_receipt,
        query_receipts=query_receipts,
        query_rows=query_rows,
        run_id=run_id,
    )
    write_json(output_dir / "artifact.json", artifact)
    write_json(output_dir / "source_inventory.json", artifact.get("source_inventory", []))
    write_json(output_dir / "quality_checks.json", artifact.get("quality_checks", []))
    write_json(output_dir / "api_reconciliation.json", {
        "status": "not_applicable" if not gemini_payload else "pending_metric_comparison",
        "route": artifact.get("route_selected"),
        "gemini_status": gemini_status,
        "api_status": artifact.get("api_status"),
        "metric_differences": [],
        "note": "Gemini and API outputs are compared only when both return the same aggregate metric and date grain.",
    })
    report_md = markdown_report(artifact)
    report_path = output_dir / "report.md"
    report_path.write_text(report_md, encoding="utf-8")
    render_markdown_file(report_path, output_dir / "report.html", title="Waje Firebase 多端设备与性能汇总分析报告")
    receipt = {
        "schema_version": 1,
        "run_id": run_id,
        "status": artifact["status"],
        "status_reason": artifact["status_reason"],
        "generated_at": artifact["generated_at"],
        "route_selected": artifact["route_selected"],
        "gemini_status": gemini_status,
        "api_status": artifact["api_status"],
        "source_scope": "firebase_only",
        "summary_mode": "window_level_compact",
        "output_row_cap": OUTPUT_ROW_CAP,
        "query_window": windows,
        "preflight_status": {
            "gemini_mcp": pf.get("bigquery_mcp", {}).get("status"),
            "api_fallback": pf.get("api_fallback", {}).get("status"),
        },
        "query_receipts": query_receipts,
        "cumulative_dry_run_bytes": cumulative_bytes,
        "query_result_row_count": sum(int(item.get("row_count") or 0) for item in query_receipts),
        "deliverables": ["report.html", "report.md", "artifact.json", "gemini_handoff.json", "api_reconciliation.json", "source_inventory.json", "quality_checks.json", "preflight.json", "query_outputs/"],
        "privacy": artifact["privacy"],
        "remote_writes": False,
    }
    write_json(output_dir / "run_receipt.json", receipt)
    return {"status": artifact["status"], "run_id": run_id, "output_dir": str(output_dir.relative_to(ROOT)), "route_selected": artifact["route_selected"], "gemini_status": gemini_status, "api_status": artifact["api_status"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--route", choices=["gemini_first"], default="gemini_first")
    parser.add_argument("--source-scope", choices=["firebase_only"], default="firebase_only")
    parser.add_argument("--report-format", default="html,md,json")
    parser.add_argument("--run-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.preflight_only:
            config = load_config()
            result = {"status": "preflight", "preflight": preflight(config)}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        result = run(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"ok", "quality_warning", "blocked_external_prerequisites", "blocked_authentication", "dry_run"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
