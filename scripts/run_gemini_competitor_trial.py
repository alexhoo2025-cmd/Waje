#!/usr/bin/env python3
"""Run one two-stage Gemini competitor-intelligence trial.

Stage 1 uses Gemini Flash once per configured entity to collect public evidence.
Stage 2 uses Gemini Pro to synthesize only the normalized evidence from stage 1.
The runner is fail-closed when the enterprise Gemini runtime is not configured.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from gemini_bridge import classify_gemini_failure, extract_model_payload, sanitize  # noqa: E402


TZ = ZoneInfo("Asia/Hong_Kong")
TOPICS = [
    "product_update",
    "gameplay",
    "promotion",
    "payment_and_withdrawal",
    "commercial_signal",
    "user_sentiment",
    "market_and_regulation",
    "stability_and_network",
]
EVIDENCE_LEVELS = {"confirmed", "reported", "inferred", "unverified"}
REQUIRED_EVIDENCE_FIELDS = (
    "topic",
    "claim",
    "source_url",
    "published_at",
    "retrieved_at",
    "evidence_level",
    "surface",
    "claim_boundary",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now() -> dt.datetime:
    return dt.datetime.now(TZ)


def is_valid_date(value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()[:80] or "unknown"


def source_registry(config: dict[str, Any]) -> list[dict[str, Any]]:
    return list(config.get("entities", []))


def preflight(config: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    command = config.get("gemini_command", ["gemini"])
    executable = shutil.which(str(command[0])) if command else None
    if not config.get("runtime_project_id"):
        return {
            "status": "blocked",
            "reason": "runtime_project_id_missing",
            "message": "企业 Gemini/Vertex 运行项目未配置；不得调用个人 API Key。",
            "competitors": len(sources),
            "gemini_cli_available": bool(executable),
        }
    if not executable:
        return {
            "status": "blocked",
            "reason": "gemini_cli_missing",
            "message": "Gemini CLI 不在 PATH 中。",
            "competitors": len(sources),
            "gemini_cli_available": False,
        }
    if not sources:
        return {
            "status": "blocked",
            "reason": "source_registry_empty",
            "message": "没有可用的竞品来源配置。",
            "competitors": 0,
            "gemini_cli_available": True,
        }
    return {"status": "ready", "competitors": len(sources), "gemini_cli_available": True}


def collection_prompt(entity: dict[str, Any], date_from: str, date_to: str, topics: list[str]) -> str:
    source_text = json.dumps(entity.get("sources", []), ensure_ascii=False)
    query_text = json.dumps(entity.get("search_queries", []), ensure_ascii=False)
    return f"""你是 Waje 竞品公开情报采集器，使用 Gemini 3.7 Flash。

对象：{entity.get('name', entity.get('id'))}
市场：{entity.get('market', 'Nigeria')}
角色：{entity.get('role', 'competitor')}
时间窗口：{date_from} 至 {date_to}
主题：{', '.join(topics)}
已配置公开来源：{source_text}
建议搜索词：{query_text}

要求：
1. 只检索公开网页、公开公告、公开应用商店、公开用户评价和公开市场信息。
2. 不读取任何账号、Cookie、Token、内部数据或用户个人明细。
3. 重要事实必须附 source_url、published_at、retrieved_at、evidence_level 和 claim_boundary（official|media|user_feedback|analysis_guess）。
4. 只记录窗口内的新信息；没有可信信息的主题返回 data_gap，不要编造内容。
5. 区分官方自述、媒体报道、用户反馈和分析推断；不要把宣传内容当作业务效果。

只返回 JSON：
{{
  "status": "ok|quality_warning|no_data|failed",
  "auth_context": {{"enterprise_account": true, "bigquery_connection": false, "workspace": ""}},
  "entity": "{entity.get('id', '')}",
  "items": [{{
    "topic": "product_update",
    "claim": "公开事实摘要",
    "source_url": "https://...",
    "published_at": "YYYY-MM-DD",
    "retrieved_at": "YYYY-MM-DD",
    "evidence_level": "confirmed|reported|inferred|unverified",
    "claim_boundary": "official|media|user_feedback|analysis_guess",
    "surface": "web|app|social|store",
    "data_gap": null
  }}],
  "next_steps": []
}}
"""


def synthesis_prompt(collection: dict[str, Any], date_from: str, date_to: str) -> str:
    compact = json.dumps(collection, ensure_ascii=False)
    return f"""你是 Waje 竞品情报分析器，使用 Gemini 3.1 Pro Preview。

分析窗口：{date_from} 至 {date_to}
以下是已经过字段清理的公开情报证据，只能基于这些证据分析，不得自行补造事实：

{compact}

请输出 JSON，完成：
1. Waje 与竞品在产品、玩法、运营、支付提现、商业化、用户反馈和稳定性方面的对比；
2. 标出 Waje H5 的相关机会和风险，重点覆盖设备性能、加载、付费用户留存和羊毛用户识别；
3. 输出 P0/P1 事项、证据等级、待人工确认项和下一步建议；
4. 所有重要结论必须引用 evidence_items 中的 source_url；不能把公开宣传内容解释成真实业务效果；
5. 无证据的结论标记 hypothesis 或 unverified。

返回：
{{
  "status": "ok|quality_warning|failed",
  "executive_summary": "",
  "comparisons": [],
  "p0_items": [],
  "p1_items": [],
  "recommendations": [],
  "gaps": [],
  "evidence_items": []
}}
"""


def invoke(config: dict[str, Any], prompt: str, model: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    command = [str(item) for item in config.get("gemini_command", ["gemini"])]
    command.extend(["--approval-mode", "plan", "--output-format", "json", "--model", model, "-p", prompt])
    child_env = os.environ.copy()
    child_env.pop("GOOGLE_API_KEY", None)
    child_env.pop("GEMINI_API_KEY", None)
    child_env["GOOGLE_CLOUD_PROJECT"] = str(config["runtime_project_id"])
    child_env["GOOGLE_CLOUD_LOCATION"] = str(config.get("location", "us-central1"))
    child_env["GEMINI_TELEMETRY_ENABLED"] = "false"
    started = dt.datetime.now(dt.UTC)
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=child_env,
            capture_output=True,
            text=True,
            timeout=int(config.get("limits", {}).get("timeout_seconds", 180)),
            check=False,
        )
    except FileNotFoundError:
        return None, {"status": "blocked_tooling", "error": "Gemini CLI not found", "duration_ms": 0}
    except subprocess.TimeoutExpired:
        return None, {"status": "failed", "error": "Gemini CLI timeout", "duration_ms": int((dt.datetime.now(dt.UTC) - started).total_seconds() * 1000)}
    receipt = {
        "status": "ok" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "duration_ms": int((dt.datetime.now(dt.UTC) - started).total_seconds() * 1000),
    }
    if completed.returncode != 0:
        status, message = classify_gemini_failure(completed.stderr)
        receipt.update({"status": status, "error": message})
        return None, receipt
    try:
        payload = extract_model_payload(json.loads(completed.stdout))
        return payload, receipt
    except (json.JSONDecodeError, ValueError) as exc:
        receipt.update({"status": "failed", "error": str(exc)})
        return None, receipt


def normalize_items(entity: dict[str, Any], payload: dict[str, Any] | None, retrieved_at: str) -> tuple[list[dict[str, Any]], list[str]]:
    if not payload:
        return [], ["model_response_missing"]
    auth = payload.get("auth_context") if isinstance(payload.get("auth_context"), dict) else {}
    if auth.get("enterprise_account") is not True:
        return [], ["enterprise_identity_not_verified"]
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    output: list[dict[str, Any]] = []
    errors: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        invalid = False
        for field in REQUIRED_EVIDENCE_FIELDS:
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"item_missing_{field}")
                invalid = True
                break
        if invalid:
            continue
        claim = str(item.get("claim") or "").strip()
        source_url = str(item.get("source_url") or "").strip()
        evidence_level = str(item.get("evidence_level") or "").strip()
        if evidence_level not in EVIDENCE_LEVELS:
            errors.append("item_invalid_evidence_level")
            continue
        if not claim or not re.match(r"^https?://", source_url):
            errors.append("item_invalid_claim_or_source")
            continue
        if not is_valid_date(str(item.get("published_at"))):
            errors.append("item_invalid_published_at")
            continue
        if not is_valid_date(str(item.get("retrieved_at"))):
            errors.append("item_invalid_retrieved_at")
            continue
        clean = sanitize(
            item,
            {
                "user_id",
                "uuid",
                "phone",
                "email",
                "cookie",
                "token",
            },
        )
        clean.update(
            {
                "entity": entity.get("id"),
                "entity_name": entity.get("name"),
                "market": entity.get("market", "Nigeria"),
            }
        )
        output.append(clean)
    return output, errors


def dedupe(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    duplicates = 0
    for item in items:
        key = hashlib.sha256(f"{item.get('source_url')}|{item.get('claim')}".encode("utf-8")).hexdigest()
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        result.append(item)
    return result, duplicates


def quality_report(collection: dict[str, Any], entity_count: int, topic_count: int, duplicates: int, failed_sources: list[str]) -> dict[str, Any]:
    items = collection.get("items", [])
    cited = sum(bool(item.get("source_url")) for item in items)
    unverified = sum(str(item.get("evidence_level")) == "unverified" for item in items)
    covered_entities = len({item.get("entity") for item in items if item.get("entity")})
    covered_topics = len({item.get("topic") for item in items if item.get("topic")})
    item_count = len(items)

    def safe_rate(numerator: int, denominator: int) -> float | None:
        if denominator <= 0:
            return None
        return numerator / denominator

    metrics = {
        "competitor_coverage": safe_rate(covered_entities, entity_count),
        "topic_coverage": safe_rate(covered_topics, topic_count),
        "source_valid_rate": safe_rate(cited, item_count),
        "citation_coverage": safe_rate(cited, item_count),
        "duplicate_rate": safe_rate(duplicates, item_count + duplicates),
        "unverified_rate": unverified / item_count if item_count else None,
        "item_count": item_count,
        "failed_sources": failed_sources,
        "status": collection.get("status"),
    }
    if collection.get("status") in {"blocked", "failed"} and not items:
        grade = "C"
    elif metrics["competitor_coverage"] is not None and metrics["competitor_coverage"] >= 1 and metrics["source_valid_rate"] == 1 and not failed_sources and metrics["unverified_rate"] <= 0.2:
        grade = "A"
    elif metrics["competitor_coverage"] is not None and metrics["competitor_coverage"] >= 0.6 and metrics["source_valid_rate"] is not None and metrics["source_valid_rate"] >= 0.8:
        grade = "B"
    else:
        grade = "C"
    return {"grade": grade, "metrics": metrics, "quality_boundary": "公开情报不证明竞品真实业务效果或因果关系。"}


def blocked_report(report_date: str, preflight_result: dict[str, Any], model_map: dict[str, str]) -> str:
    return f"""---
type: competitor-intelligence-report
status: blocked
updated: {report_date}
tags: [waje, competitor, gemini, blocked]
---

# Gemini 竞品情报试运行｜{report_date}

## 执行状态

**Blocked：本次没有调用 Gemini，也没有生成竞品事实结论。**

- 阻塞原因：`{preflight_result.get('reason')}`
- 说明：{preflight_result.get('message')}
- Flash 模型：`{model_map.get('collection')}`
- Pro 模型：`{model_map.get('synthesis')}`

## 质量边界

本报告不代表竞品没有动态，不代表来源返回 0；仅表示企业 Gemini 运行项目、许可证或 CLI 能力尚未满足试运行条件。

## 解阻塞后执行

1. 配置企业 Gemini/Vertex 运行项目并确认模型权限；
2. 运行 Flash 分竞品采集；
3. 完成证据去重和来源质量检查；
4. 运行 Pro 综合分析；
5. 由 Codex 审计后再发布正式日报。
"""


def build_report(report_date: str, collection: dict[str, Any], synthesis: dict[str, Any], quality: dict[str, Any]) -> str:
    def pct(value: float | None) -> str:
        return f"{value:.1%}" if isinstance(value, (int, float)) else "N/A"

    lines = [
        "---",
        "type: competitor-intelligence-report",
        f"updated: {report_date}",
        f"status: {quality.get('grade', 'C').lower()}",
        "tags: [waje, competitor, gemini, public-intelligence]",
        "---",
        "",
        f"# Gemini 竞品情报分析｜{report_date}",
        "",
        "## 执行摘要",
        "",
        str(synthesis.get("executive_summary") or "暂无综合摘要"),
        "",
        "## 质量评估",
        "",
        f"- 等级：`{quality.get('grade')}`",
        f"- 竞品覆盖率：`{pct(quality['metrics'].get('competitor_coverage'))}`",
        f"- 主题覆盖率：`{pct(quality['metrics'].get('topic_coverage'))}`",
        f"- 来源有效率：`{pct(quality['metrics'].get('source_valid_rate'))}`",
        f"- 未核验事实占比：`{pct(quality['metrics'].get('unverified_rate'))}`",
        "",
        "## 产品与运营对比",
        "",
    ]
    comparisons = synthesis.get("comparisons") if isinstance(synthesis.get("comparisons"), list) else []
    lines.extend(f"- {item}" if not isinstance(item, dict) else f"- **{item.get('topic', '对比')}**：{item.get('finding', item.get('summary', ''))}" for item in comparisons)
    if not comparisons:
        lines.append("- 暂无已核验对比结果。")
    lines.extend(["", "## P0/P1 事项", ""])
    for label, key in (("P0", "p0_items"), ("P1", "p1_items")):
        values = synthesis.get(key) if isinstance(synthesis.get(key), list) else []
        lines.extend(f"- **{label}**：{item}" for item in values)
    lines.extend(["", "## 对 Waje H5 的建议", ""])
    recommendations = synthesis.get("recommendations") if isinstance(synthesis.get("recommendations"), list) else []
    lines.extend(f"- {item}" for item in recommendations)
    if not recommendations:
        lines.append("- 基于证据不足，暂不输出确定性建议。")
    lines.extend(["", "## 证据与待确认项", ""])
    gaps = synthesis.get("gaps") if isinstance(synthesis.get("gaps"), list) else []
    lines.extend(f"- {item}" for item in gaps)
    lines.extend(["", "## 情报事实条目", "", "| 对象 | 主题 | 事实 | 来源 | 证据等级 |", "|---|---|---|---|---|"])
    for item in collection.get("items", [])[:300]:
        lines.append(f"| {item.get('entity_name', item.get('entity', ''))} | {item.get('topic', '')} | {item.get('claim', '')} | {item.get('source_url', '')} | {item.get('evidence_level', '')} |")
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> dict[str, Any]:
    config = read_json(ROOT / "config/gemini-enterprise.json")
    sources_config = read_json(ROOT / "config/intel_sources.json")
    report_date = args.report_date or now().date().isoformat()
    end_date = dt.date.fromisoformat(args.date_to) if args.date_to else dt.date.fromisoformat(report_date)
    start_date = dt.date.fromisoformat(args.date_from) if args.date_from else end_date - dt.timedelta(days=13)
    date_from, date_to = start_date.isoformat(), end_date.isoformat()
    entities = source_registry(sources_config)
    task_id = args.task_id or f"competitor-trial-{report_date}"
    out_dir = ROOT / "data/outputs/gemini" / report_date / task_id
    html_path = ROOT / "output/html" / f"{report_date}-Gemini竞品情报分析.html"
    model_map = {"collection": config.get("preferred_models", {}).get("web_research", "gemini-3.7-flash"), "synthesis": config.get("preferred_models", {}).get("competitor_intelligence", "gemini-3.1-pro-preview")}
    pf = preflight(config, entities)
    receipt = {"schema_version": 1, "task_id": task_id, "report_date": report_date, "window": {"date_from": date_from, "date_to": date_to, "timezone": "Asia/Hong_Kong"}, "models": model_map, "status": "blocked" if pf["status"] != "ready" else "running", "preflight": pf, "stages": []}
    if pf["status"] != "ready":
        receipt["stages"].append({"stage": "preflight", "status": pf["status"], "reason": pf.get("reason"), "message": pf.get("message"), "message_hint": pf.get("competitors")})
        collection = {"status": "blocked", "items": [], "entity_count": len(entities), "topic_count": len(TOPICS)}
        synthesis = {"status": "blocked", "executive_summary": ""}
        quality = {
            "grade": "Blocked",
            "metrics": {
                "competitor_coverage": None,
                "topic_coverage": None,
                "source_valid_rate": None,
                "citation_coverage": None,
                "duplicate_rate": None,
                "unverified_rate": None,
                "item_count": 0,
                "failed_sources": [],
                "status": "blocked",
            },
            "quality_boundary": "未执行，不代表真实数据为 0。",
        }
        report_md = blocked_report(report_date, pf, model_map)
    else:
        all_items: list[dict[str, Any]] = []
        failed: list[str] = []
        for entity in entities:
            payload, stage_receipt = invoke(config, collection_prompt(entity, date_from, date_to, TOPICS), model_map["collection"])
            items, errors = normalize_items(entity, payload, now().isoformat(timespec="seconds"))
            all_items.extend(items)
            if errors or stage_receipt.get("status") != "ok":
                failed.append(str(entity.get("id")))
            receipt["stages"].append({"stage": "collect", "entity": entity.get("id"), **stage_receipt, "item_count": len(items), "errors": errors})
        unique_items, duplicates = dedupe(all_items)
        collection = {"status": "ok" if unique_items else "quality_warning", "window": {"date_from": date_from, "date_to": date_to}, "items": unique_items, "entity_count": len(entities), "topic_count": len(TOPICS)}
        payload, stage_receipt = invoke(config, synthesis_prompt(collection, date_from, date_to), model_map["synthesis"])
        synthesis = payload or {"status": "failed", "gaps": [stage_receipt.get("error", "synthesis response missing")]}
        receipt["stages"].append({"stage": "synthesis", **stage_receipt})
        quality = quality_report(collection, len(entities), len(TOPICS), duplicates, failed)
        report_md = build_report(report_date, collection, synthesis, quality)
        receipt["status"] = "ok" if quality["grade"] in {"A", "B"} else "quality_warning"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "collection.json", collection)
    write_json(out_dir / "synthesis.json", synthesis)
    write_json(out_dir / "quality.json", quality)
    report_path = out_dir / "report.md"
    report_path.write_text(report_md, encoding="utf-8")
    receipt["report"] = str(report_path.relative_to(ROOT))
    receipt["quality"] = str((out_dir / "quality.json").relative_to(ROOT))
    write_json(out_dir / "receipt.json", receipt)
    try:
        from render_analysis_report_html import render_markdown_file

        render_markdown_file(report_path, html_path)
        receipt["html"] = str(html_path.relative_to(ROOT))
        write_json(out_dir / "receipt.json", receipt)
    except Exception as exc:
        receipt.setdefault("warnings", []).append(f"html_render_failed: {exc}")
        write_json(out_dir / "receipt.json", receipt)
    return {"status": receipt["status"], "task_id": task_id, "report": receipt.get("report"), "html": receipt.get("html"), "quality": quality}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date-from")
    parser.add_argument("--date-to")
    parser.add_argument("--report-date")
    parser.add_argument("--task-id")
    args = parser.parse_args()
    result = run(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"ok", "quality_warning", "blocked"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
