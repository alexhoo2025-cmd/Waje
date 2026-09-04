#!/usr/bin/env python3
"""Run a privacy-safe Waje task through the enterprise Gemini CLI.

The bridge is deliberately fail-closed. It does not read credentials, does not run
BigQuery itself, and only persists a sanitized model contract plus an audit receipt.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

try:
    from .bigquery_mcp_policy import load_policy, validate_query as validate_mcp_query
    from .gemini_model_routing import classify_model_attempt, model_candidates, retryable_model_status
except ImportError:  # pragma: no cover - direct script execution fallback
    from bigquery_mcp_policy import load_policy, validate_query as validate_mcp_query
    from gemini_model_routing import classify_model_attempt, model_candidates, retryable_model_status


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "gemini-enterprise.json"
OUTPUT_ROOT = ROOT / "data" / "outputs" / "gemini"

EXPECTED_FIELDS = {
    "status",
    "auth_context",
    "sql",
    "source_objects",
    "data_cutoff",
    "complete_day",
    "metrics",
    "summary",
    "quality",
    "next_steps",
    "error",
    "sources",
    "evidence_level",
    "claims",
}

FORBIDDEN_SQL = (
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

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)")


class ContractError(ValueError):
    """Raised when the model response cannot be safely accepted."""


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("data_project_id", payload.get("project_id")) != "wajenigeria":
        raise ContractError("only the approved Waje project wajenigeria is allowed")
    return payload


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def _allowed_source(source: str, config: dict[str, Any]) -> bool:
    allowed_views = [str(item).lower().strip("`") for item in config.get("allowed_views", [])]
    allowed_datasets = [str(item).lower().strip("`") for item in config.get("allowed_datasets", [])]
    normalized = source.lower().strip("`")
    if normalized in allowed_views:
        return True
    parts = normalized.split(".")
    return len(parts) >= 2 and ".".join(parts[:2]) in allowed_datasets


def _source_references(sql: str) -> list[str]:
    refs = re.findall(
        r"(?:from|join|table)\s+`?([a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_*${}-]+){1,2})`?",
        sql,
        flags=re.I,
    )
    return sorted(set(refs))


def _select_clause(sql: str) -> str:
    match = re.search(r"\bselect\b(.*?)\bfrom\b", sql, flags=re.I | re.S)
    return match.group(1) if match else ""


def validate_sql(sql: str, config: dict[str, Any]) -> list[str]:
    """Return blocking validation errors for a model-generated query."""
    errors: list[str] = []
    if not isinstance(sql, str) or not sql.strip():
        return ["missing SQL"]

    cleaned = strip_sql_comments(sql).strip()
    statements = [item.strip() for item in cleaned.split(";") if item.strip()]
    if len(statements) != 1:
        errors.append("multiple SQL statements are not allowed")
    if not re.match(r"^(select|with)\b", cleaned, flags=re.I):
        errors.append("only SELECT/WITH queries are allowed")
    lowered = cleaned.lower()
    for keyword in FORBIDDEN_SQL:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            errors.append(f"forbidden SQL operation: {keyword}")
    if re.search(r"\bselect\s+(?:distinct\s+)?\*\s*(?:,|from)\b", lowered):
        errors.append("SELECT * is not allowed")

    sensitive = [str(item).lower() for item in config.get("sensitive_identifiers", [])]
    select_clause = _select_clause(cleaned)
    for expression in select_clause.split(","):
        expression = expression.strip().lower()
        if any(re.fullmatch(rf"(?:`?{re.escape(name)}`?)(?:\s+as\s+\w+)?", expression) for name in sensitive):
            errors.append("direct sensitive identifier projection is not allowed")
            break

    if not re.search(
        r"(?:event_date|register_date|dt|date|_partitiondate|timestamp|event_time)\s*(?:between|>=|>|=)",
        lowered,
    ):
        errors.append("a date or partition predicate is required")

    references = _source_references(cleaned)
    if not references:
        errors.append("no fully qualified approved source object found")
    elif not all(_allowed_source(ref, config) for ref in references):
        errors.append("query references an object outside the configured allowlist")
    elif any(not ref.lower().startswith("wajenigeria.") for ref in references):
        errors.append("only the Waje project wajenigeria is allowed")

    policy_ref = config.get("mcp_policy_path")
    if policy_ref:
        policy_path = Path(str(policy_ref))
        if not policy_path.is_absolute():
            policy_path = ROOT / policy_path
        if not policy_path.exists():
            errors.append("configured MCP policy file is missing")
        else:
            try:
                errors.extend(validate_mcp_query(cleaned, load_policy(policy_path)))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"MCP policy could not be loaded: {exc}")

    return sorted(set(errors))


def _redact_text(value: str) -> str:
    value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    return PHONE_RE.sub("[REDACTED_PHONE]", value)


def sanitize(value: Any, sensitive_keys: set[str]) -> Any:
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in sensitive_keys or str(key).lower() in {"rows", "raw_events", "user_details", "identities"}:
                continue
            output[str(key)] = sanitize(item, sensitive_keys)
        return output
    if isinstance(value, list):
        return [sanitize(item, sensitive_keys) for item in value[:3000]]
    if isinstance(value, str):
        return _redact_text(value)[:10000]
    return value


def extract_model_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and EXPECTED_FIELDS.intersection(raw):
        return raw
    if isinstance(raw, dict):
        for key in ("response", "text", "result", "output"):
            value = raw.get(key)
            if isinstance(value, dict):
                return extract_model_payload(value)
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed
    raise ContractError("Gemini response does not contain the required JSON contract")


def classify_gemini_failure(text: str) -> tuple[str, str]:
    """Map Gemini CLI errors to safe, actionable receipt states."""
    lowered = text.lower()
    if "aiplatform.endpoints.predict" in lowered:
        return "blocked_iam", "Vertex AI prediction permission is missing for the configured runtime project"
    if "subscription_required" in lowered or "valid license" in lowered or "cloudaicompanion.licenses.selfassign" in lowered:
        return "blocked_license", "Gemini Code Assist or enterprise Gemini license is not assigned"
    if "model" in lowered and ("not found" in lowered or "not available" in lowered):
        return "model_unavailable", "The requested Gemini model is not available in the configured runtime project"
    if "permission_denied" in lowered or "permission" in lowered and "denied" in lowered:
        return "blocked_iam", "Enterprise IAM denied the Gemini CLI request"
    return "failed", "Gemini CLI request failed; inspect the local error report without persisting raw output"


def build_prompt(
    task: str,
    task_type: str,
    config: dict[str, Any],
    date_from: str | None = None,
    date_to: str | None = None,
    dimensions: list[str] | None = None,
) -> str:
    task_spec = config.get("task_types", {}).get(task_type, {})
    requires_bigquery = task_spec.get("requires_bigquery", True)
    date_window = f"{date_from or '最近7个完整日'} 至 {date_to or '最新完整日'}"
    dimensions_text = ", ".join(dimensions or task_spec.get("required_dimensions", []))
    return f"""你是 Waje 企业 Gemini 分析执行器。

数据类型：{"企业 BigQuery 认证聚合数据" if requires_bigquery else "公开互联网信息"}
仅使用企业账号和本任务允许的数据源，不读取或返回不必要的敏感信息。

任务类型：{task_type}
任务目标：{task_spec.get('purpose', '')}
用户问题：{task}
时间范围：{date_window}
时区：{config.get('timezone', 'Africa/Lagos')}
建议维度：{dimensions_text}

执行要求：
1. {"只执行 SELECT/WITH，必须包含日期或分区过滤，禁止写操作、导出和修改配置；只使用企业授权的 Waje 项目 wajenigeria 数据集或 View。" if requires_bigquery else "只检索公开网页和公开应用商店/公告信息；每条重要事实必须带 source_url、published_at 和 retrieved_at。"}
2. 只返回聚合结果或公开事实摘要，默认不超过 3000 行；不要返回 user_id、uuid、手机号、邮箱、KYC 原始字段、订单明细或完整设备标识。
3. 明确数据截止时间、完整日、样本量、分母、成熟 cohort、货币、来源和缺失原因。
4. 不要把相关性写成因果；无法证明时标记为 hypothesis。

必须只返回 JSON 对象，字段契约为：
{{
  "status": "ok|no_data|delayed|quality_warning|blocked_authentication|failed",
  "auth_context": {{"enterprise_account": true, "bigquery_connection": {str(requires_bigquery).lower()}, "workspace": ""}},
  "sql": "SELECT ...",
  "source_objects": [],
  "data_cutoff": "",
  "complete_day": true,
  "metrics": [],
  "summary": "",
  "quality": {{"sample_size": 0, "denominator": "", "missing_reason": null}},
  "next_steps": [],
  "sources": [],
  "evidence_level": "confirmed|reported|inferred|unverified"
}}
"""


def _task_id(task_id: str | None) -> str:
    value = (task_id or "").strip()
    if value and re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", value):
        return value
    return f"task-{dt.datetime.now(dt.UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_report(path: Path, payload: dict[str, Any], receipt: dict[str, Any]) -> None:
    summary = str(payload.get("summary") or receipt.get("error") or "暂无可用摘要")
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), list) else []
    next_steps = payload.get("next_steps") if isinstance(payload.get("next_steps"), list) else []
    lines = [
        "# Gemini Waje 分析初稿",
        "",
        f"- 状态：`{receipt['status']}`",
        f"- 任务类型：`{receipt['task_type']}`",
        f"- 数据截止：`{payload.get('data_cutoff') or '未提供'}`",
        "",
        "## 初步结论",
        "",
        summary,
        "",
        "## 指标结果",
        "",
    ]
    if metrics:
        lines.extend(["| 指标 | 数值 | 说明 |", "|---|---:|---|"])
        for item in metrics[:100]:
            if not isinstance(item, dict):
                continue
            lines.append(f"| {item.get('name', '')} | {item.get('value', '')} | {item.get('definition', item.get('note', ''))} |")
    else:
        lines.append("- 无结构化指标结果。")
    lines.extend(["", "## 待办与人工确认", ""])
    lines.extend(f"- {item}" for item in next_steps[:100])
    if not next_steps:
        lines.append("- 需要 Codex 继续核对指标口径、数据质量和事实来源。")
    lines.extend(["", "## 质量边界", "", "本文件是 Gemini 初步分析草稿，正式结论必须经过 Codex 口径和数据质量审计。"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_task(
    task: str,
    task_type: str,
    config_path: Path = DEFAULT_CONFIG,
    date_from: str | None = None,
    date_to: str | None = None,
    dimensions: list[str] | None = None,
    task_id: str | None = None,
    output_dir: Path = OUTPUT_ROOT,
    dry_run: bool = False,
    recovery_probe: bool = False,
) -> dict[str, Any]:
    config = load_config(config_path)
    resolved_id = _task_id(task_id)
    prompt = build_prompt(task, task_type, config, date_from, date_to, dimensions)
    if dry_run:
        model_key = "complex_analysis" if task_type in {"h5_lightgame", "payer_retention", "kyc"} else task_type
        candidates = model_candidates(config, model_key)
        return {
            "status": "dry_run",
            "task_id": resolved_id,
            "task_type": task_type,
            "selected_model": candidates[0] if candidates and candidates[0] is not None else "cli_default",
            "model_candidates": [item if item is not None else "cli_default" for item in candidates],
            "model_routing": "preferred_then_fallback_then_cli_default",
            "prompt": prompt,
            "config_path": str(config_path.relative_to(ROOT) if config_path.is_relative_to(ROOT) else config_path),
        }

    policy = config.get("execution_policy", {})
    excluded = policy.get("cli_excluded_from_collaboration", False)
    if excluded or (policy.get("cli_normal_invocation_enabled", policy.get("normal_invocation_enabled")) is False and not recovery_probe):
        task_root = output_dir / dt.datetime.now().astimezone().date().isoformat() / resolved_id
        if task_root.exists():
            resolved_id += "-" + uuid.uuid4().hex[:8]
            task_root = task_root.with_name(resolved_id)
        paused = {"status": "blocked_cli_excluded" if excluded else "blocked_recovery_required", "task_id": resolved_id, "task_type": task_type,
                  "started_at": dt.datetime.now(dt.UTC).isoformat(), "model_attempts": [],
                  "error": "Local Gemini CLI excluded: permissions not enabled; no automatic invocation or recovery probe. Web Agent is independently available." if excluded else "Local Gemini CLI requires recovery; web Agent is independently available."}
        _write_json(task_root / "receipt.json", paused)
        _write_json(task_root / "result.json", {})
        return {"status": paused["status"], "task_id": resolved_id, "output_dir": _display_path(task_root)}

    started_at = dt.datetime.now(dt.UTC).isoformat()
    task_spec = config.get("task_types", {}).get(task_type, {})
    requires_bigquery = task_spec.get("requires_bigquery", True)
    model_key = "complex_analysis" if task_type in {"h5_lightgame", "payer_retention", "kyc"} else task_type
    candidates = model_candidates(config, model_key)
    selected_model = candidates[0] if candidates else None
    candidate_labels = [item if item is not None else "cli_default" for item in candidates]
    child_env = os.environ.copy()
    child_env.pop("GOOGLE_API_KEY", None)
    child_env.pop("GEMINI_API_KEY", None)
    child_env["GOOGLE_CLOUD_PROJECT"] = str(config["runtime_project_id"])
    child_env["GOOGLE_CLOUD_LOCATION"] = str(config.get("location", "us-central1"))
    child_env["GEMINI_TELEMETRY_ENABLED"] = "false"
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "task_id": resolved_id,
        "task_type": task_type,
        "started_at": started_at,
        "account_mode": "enterprise_required",
        "data_project_id": config.get("data_project_id", config.get("project_id")),
        "runtime_project_id": config.get("runtime_project_id"),
        "selected_model": selected_model if selected_model is not None else "cli_default",
        "model_candidates": candidate_labels,
        "model_routing": "preferred_then_fallback_then_cli_default",
        "model_attempts": [],
        "requires_bigquery": requires_bigquery,
        "status": "failed",
        "query_window": {"date_from": date_from, "date_to": date_to, "timezone": config.get("timezone")},
        "query_validated": False,
        "source_objects": [],
        "warnings": [],
    }

    if requires_bigquery and not config.get("runtime_project_id"):
        receipt.update({"status": "blocked_authentication", "error": "runtime_project_id is not configured; data and Gemini runtime projects must be confirmed separately"})
        task_root = output_dir / dt.datetime.now().astimezone().date().isoformat() / resolved_id
        _write_json(task_root / "result.json", {})
        _write_json(task_root / "receipt.json", receipt)
        _write_report(task_root / "report.md", {}, receipt)
        return {"status": receipt["status"], "task_id": resolved_id, "output_dir": _display_path(task_root)}

    payload: dict[str, Any] = {}
    timeout = int(config.get("limits", {}).get("timeout_seconds", 180))
    for index, model in enumerate(candidates or [None]):
        command = [str(item) for item in config.get("gemini_command", ["gemini"])]
        command.extend(["--approval-mode", str(config.get("approval_mode", "plan")), "--output-format", str(config.get("output_format", "json"))])
        if model is not None:
            command.extend(["--model", str(model)])
        command.extend(["-p", prompt])
        attempt: dict[str, Any] = {
            "index": index + 1,
            "model": model if model is not None else "cli_default",
        }
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                env=child_env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError:
            receipt.update({"status": "blocked_tooling", "error": "Gemini CLI was not found"})
            attempt["status"] = "blocked_tooling"
            receipt["model_attempts"].append(attempt)
            break
        except subprocess.TimeoutExpired:
            attempt.update({"status": "failed_timeout", "retryable": True})
            receipt["model_attempts"].append(attempt)
            if index + 1 < len(candidates):
                continue
            receipt.update({"status": "failed_timeout", "error": "Gemini CLI timed out"})
            break

        attempt["returncode"] = completed.returncode
        if completed.returncode != 0:
            status, retryable = classify_model_attempt(completed.returncode, completed.stderr)
            attempt.update({"status": status, "retryable": retryable, "stderr_summary": _redact_text(completed.stderr)[:2000]})
            receipt["model_attempts"].append(attempt)
            if retryable_model_status(status) and index + 1 < len(candidates):
                continue
            _status, message = classify_gemini_failure(completed.stderr)
            receipt.update({"status": _status, "error": message, "returncode": completed.returncode, "selected_model": model if model is not None else "cli_default"})
            break

        try:
            raw = json.loads(completed.stdout)
            payload = extract_model_payload(raw)
            attempt["status"] = "ok"
            receipt["model_attempts"].append(attempt)
            receipt.update({"selected_model": model if model is not None else "cli_default", "model_fallback_used": index > 0})
            break
        except (json.JSONDecodeError, ContractError) as exc:
            attempt.update({"status": "failed_invalid_json", "retryable": True, "response_parse": "invalid_json"})
            receipt["model_attempts"].append(attempt)
            if index + 1 < len(candidates):
                continue
            receipt.update({"status": "failed_invalid_json", "error": str(exc), "selected_model": model if model is not None else "cli_default"})

    if payload:
        safe_keys = {str(item).lower() for item in config.get("sensitive_identifiers", [])}
        payload = sanitize({key: value for key, value in payload.items() if key in EXPECTED_FIELDS}, safe_keys)
        auth = payload.get("auth_context") if isinstance(payload.get("auth_context"), dict) else {}
        enterprise_ok = auth.get("enterprise_account") is True and ((not requires_bigquery) or auth.get("bigquery_connection") is True)
        if not enterprise_ok:
            receipt.update({"status": "blocked_authentication", "error": "enterprise account or BigQuery connection was not verified"})
        else:
            sql_errors = [] if not requires_bigquery else validate_sql(str(payload.get("sql") or ""), config)
            receipt["query_validated"] = not sql_errors
            receipt["sql_errors"] = sql_errors
            receipt["source_objects"] = payload.get("source_objects", []) if isinstance(payload.get("source_objects"), list) else []
            receipt["data_cutoff"] = payload.get("data_cutoff")
            receipt["complete_day"] = payload.get("complete_day")
            if sql_errors:
                receipt.update({"status": "blocked_sql_validation", "error": "; ".join(sql_errors)})
            else:
                model_status = str(payload.get("status") or "quality_warning")
                receipt["status"] = model_status if model_status in {"ok", "no_data", "delayed", "quality_warning"} else "quality_warning"

    task_root = output_dir / dt.datetime.now().astimezone().date().isoformat() / resolved_id
    _write_json(task_root / "result.json", payload)
    _write_json(task_root / "receipt.json", receipt)
    _write_report(task_root / "report.md", payload, receipt)
    return {"status": receipt["status"], "task_id": resolved_id, "output_dir": _display_path(task_root)}


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--task-type", choices=["h5_performance", "h5_lightgame", "game_rtp", "payer_retention", "kyc", "web_research", "competitor_intelligence"], required=True)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--dimension", action="append", dest="dimensions", default=[])
    parser.add_argument("--task-id")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--recovery-probe", action="store_true", help="Explicitly test enterprise recovery; existing auth and query gates still apply")
    args = parser.parse_args(argv)
    result = run_task(
        task=args.task,
        task_type=args.task_type,
        config_path=Path(args.config).resolve(),
        date_from=args.date_from,
        date_to=args.date_to,
        dimensions=args.dimensions,
        task_id=args.task_id,
        output_dir=Path(args.output_dir).resolve(),
        dry_run=args.dry_run,
        recovery_probe=args.recovery_probe,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"ok", "no_data", "delayed", "quality_warning", "dry_run"} else 2


if __name__ == "__main__":
    raise SystemExit(cli_main())
