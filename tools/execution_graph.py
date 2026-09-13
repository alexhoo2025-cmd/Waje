#!/usr/bin/env python3
"""Build a compact, evidence-bounded execution graph for Waje report workflows."""

from __future__ import annotations

import argparse
import ast
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import tomllib
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
GENERATED = Path("knowledge/_generated")
STATE = Path("data/processed/execution_graph")
OUTPUT = Path("data/outputs/execution_graph")
RECEIPT_NAMES = {
    "receipt.json", "run-log.json", "quality.json", "delivery-receipt.json",
    "report-receipt.json", "run_receipt.json", "execution_receipt.json",
    "last-approved-version.json",
}
SKIP_PARTS = {
    ".git", ".obsidian", ".venv", ".venv-wechat", ".local", "node_modules",
    "dist", "build", "tmp", "_generated", "__pycache__", ".bkit", ".codex-work",
}
STATUS_MAP = {
    "passed": "ok", "ready": "ok", "completed": "ok", "success": "ok",
    "succeeded": "ok", "running": "unknown", "started": "unknown",
    "skipped": "not_run", "skipped_existing_batch": "ok",
}
KNOWN_STATUS = {
    "ok", "partial", "degraded", "blocked", "failed", "error", "shortfall",
    "immature", "unknown", "manual", "not_run", "auth_required",
    "already_running", "no_data", "skipped_no_revision", "disabled",
}


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def safe_rel(value: str | Path, root: Path) -> str | None:
    try:
        path = Path(value)
        absolute = path.resolve() if path.is_absolute() else (root / path).resolve()
        return absolute.relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return None


def read_json(path: Path, fallback: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(content, encoding="utf-8")
    os.replace(temp, path)


def digest(path: Path) -> str | None:
    try:
        if path.stat().st_size > 2_000_000:
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def load_config(root: Path) -> dict[str, Any]:
    payload = read_json(root / "config/execution_graph.json", {})
    if not isinstance(payload, dict):
        raise ValueError("config/execution_graph.json is invalid")
    return payload


def normalize_status(value: Any) -> str:
    raw = str(value or "unknown").lower().strip()
    return STATUS_MAP.get(raw, raw if raw in KNOWN_STATUS else "unknown")


def payload_time(payload: dict[str, Any]) -> str | None:
    for key in ("finished_at", "run_at", "generated_at", "updated_at", "started_at", "date"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: set[tuple[str, str, str]] = set()
        self.diagnostics: list[dict[str, Any]] = []

    def node(self, node_id: str, kind: str, label: str, **meta: Any) -> str:
        item = self.nodes.setdefault(node_id, {"id": node_id, "kind": kind, "label": label})
        for key, value in meta.items():
            if value not in (None, "", [], {}):
                item[key] = value
        return node_id

    def edge(self, source: str, target: str, kind: str) -> None:
        if source != target:
            self.edges.add((source, target, kind))

    def diagnostic(self, code: str, severity: str, message: str, **meta: Any) -> None:
        item = {"code": code, "severity": severity, "message": message}
        item.update({key: value for key, value in meta.items() if value not in (None, "", [], {})})
        self.diagnostics.append(item)


def file_node(graph: Graph, path: str, kind: str, **meta: Any) -> str:
    return graph.node(kind + ":" + path, kind, path, path=path, **meta)


def extract_paths(text: str) -> list[str]:
    return sorted(set(
        item.rstrip(".,;:")
        for item in re.findall(r"(?:data|knowledge|output|analysis|config|scripts|tools)/[A-Za-z0-9_./{}-]+", text)
    ))


def extract_scripts(text: str) -> list[str]:
    return sorted(set(re.findall(r"(?:scripts|tools)/[A-Za-z0-9_./-]+\.(?:py|mjs|js|ts)", text)))


def source_kind(value: str) -> str | None:
    lowered = value.lower()
    if "lark" in lowered or "飞书" in value:
        return "authorized_lark_source"
    if "google play" in lowered:
        return "public_google_play_source"
    if "wechat" in lowered or "公众号" in value:
        return "public_or_authorized_wechat_source"
    if "bigquery" in lowered or "firebase" in lowered or "origin" in lowered or "gm" in lowered:
        return "authorized_aggregate_data_source"
    if "public" in lowered or "公开" in value:
        return "public_web_source"
    return None


def open_state_db(root: Path) -> sqlite3.Connection:
    path = root / STATE / "execution-state.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_events (
                event_key TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                status TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                receipt_paths_json TEXT NOT NULL,
                artifact_paths_json TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS execution_events_latest ON execution_events(job_id, occurred_at DESC)")
    return conn


def sanitized_paths(paths: Iterable[str], root: Path) -> list[str]:
    return sorted({item for value in paths if (item := safe_rel(value, root))})


def add_event(
    root: Path,
    job_id: str,
    run_id: str,
    phase: str,
    status: str,
    receipt_paths: Iterable[str] = (),
    artifact_paths: Iterable[str] = (),
    occurred_at: str | None = None,
) -> str:
    if phase not in {"started", "finished"}:
        raise ValueError("phase must be started or finished")
    key = hashlib.sha256((job_id + "|" + run_id + "|" + phase).encode()).hexdigest()
    with contextlib.closing(open_state_db(root)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO execution_events(event_key, job_id, run_id, phase, status, occurred_at, receipt_paths_json, artifact_paths_json)
                VALUES(?,?,?,?,?,?,?,?)
                ON CONFLICT(event_key) DO UPDATE SET
                  status=excluded.status, occurred_at=excluded.occurred_at,
                  receipt_paths_json=excluded.receipt_paths_json,
                  artifact_paths_json=excluded.artifact_paths_json
                """,
                (
                    key, job_id, run_id, phase, normalize_status(status), occurred_at or now_iso(),
                    json.dumps(sanitized_paths(receipt_paths, root)),
                    json.dumps(sanitized_paths(artifact_paths, root)),
                ),
            )
    return key


def latest_events(root: Path) -> dict[str, dict[str, Any]]:
    with contextlib.closing(open_state_db(root)) as conn:
        rows = conn.execute("SELECT * FROM execution_events ORDER BY occurred_at DESC, event_key DESC").fetchall()
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row["job_id"] in result:
            continue
        result[row["job_id"]] = {
            "run_id": row["run_id"],
            "phase": row["phase"],
            "status": row["status"],
            "occurred_at": row["occurred_at"],
            "receipt_paths": json.loads(row["receipt_paths_json"]),
            "artifact_paths": json.loads(row["artifact_paths_json"]),
        }
    return result


def parse_automation(automation_id: str, automations_root: Path | None) -> dict[str, Any] | None:
    if not automations_root:
        return None
    path = automations_root / automation_id / "automation.toml"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    return {key: data.get(key) for key in ("id", "name", "kind", "status", "rrule", "model", "reasoning_effort")}


def resolve_python_module(source: Path, module: str, root: Path) -> str | None:
    if not module:
        return None
    raw = module.replace(".", "/")
    choices = [
        source.parent / (raw + ".py"),
        root / "scripts" / (raw + ".py"),
        root / "tools" / (raw + ".py"),
        root / (raw + ".py"),
    ]
    for candidate in choices:
        if candidate.is_file():
            return safe_rel(candidate, root)
    return None


def add_code_edges(graph: Graph, root: Path, scripts: Iterable[str]) -> None:
    for script_path in sorted(set(scripts)):
        source = root / script_path
        if not source.is_file():
            graph.diagnostic("missing_script", "warning", "任务清单引用的脚本不存在", script=script_path)
            continue
        source_node = file_node(graph, script_path, "script")
        text = source.read_text(encoding="utf-8", errors="ignore")
        if source.suffix == ".py":
            try:
                tree = ast.parse(text)
            except SyntaxError:
                graph.diagnostic("unparsed_python", "warning", "Python 脚本无法解析", script=script_path)
                tree = None
            if tree:
                for item in ast.walk(tree):
                    if isinstance(item, ast.ImportFrom):
                        target = resolve_python_module(source, item.module or "", root)
                        if target:
                            graph.edge(source_node, file_node(graph, target, "script"), "depends_on")
                    if isinstance(item, ast.Import):
                        for alias in item.names:
                            target = resolve_python_module(source, alias.name, root)
                            if target:
                                graph.edge(source_node, file_node(graph, target, "script"), "depends_on")
        if source.suffix in {".js", ".mjs", ".ts", ".tsx", ".jsx"}:
            for raw in re.findall(r"(?:from\s*|import\s*\(|require\s*\()['\"]([^'\"]+)", text):
                if not raw.startswith("."):
                    continue
                base = (source.parent / raw).resolve()
                for suffix in (".mjs", ".js", ".ts", ".tsx", ".py"):
                    candidate = base if base.suffix else base.with_suffix(suffix)
                    if candidate.is_file():
                        target = safe_rel(candidate, root)
                        if target:
                            graph.edge(source_node, file_node(graph, target, "script"), "depends_on")
                        break
        for target in extract_scripts(text):
            if (root / target).is_file():
                graph.edge(source_node, file_node(graph, target, "script"), "executes")


def receipt_paths(root: Path, graph_config: dict[str, Any]) -> list[Path]:
    found: set[Path] = set()
    output = root / "data/outputs"
    if output.exists():
        for path in output.rglob("*.json"):
            if path.name in RECEIPT_NAMES:
                found.add(path)
    analysis_root = root / str(graph_config.get("ad_hoc_inclusion", {}).get("root", "analysis"))
    names = set(graph_config.get("ad_hoc_inclusion", {}).get("required_markers", []))
    if analysis_root.exists():
        for path in analysis_root.rglob("*.json"):
            if path.name in names or path.name in RECEIPT_NAMES:
                found.add(path)
    return sorted(found)


def payload_status(payload: dict[str, Any]) -> str:
    for key in ("final_status", "status", "quality_status"):
        if key in payload:
            return normalize_status(payload[key])
    if payload.get("ok") is True:
        return "ok"
    if payload.get("ok") is False:
        return "failed"
    return "unknown"


def infer_job(payload: dict[str, Any], path: str) -> str | None:
    for key in ("job_id", "task_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    if "play_reviews" in path:
        return "google_play_reviews_weekly" if "/weekly/" in path else "google_play_reviews_daily"
    if "meeting_minutes" in path:
        return "meeting_minutes_weekday"
    if "waje_config" in path:
        return "waje_config_weekly"
    if "outputs/weekly" in path:
        return "weekly_report"
    return None


def receipt_priority(name: str) -> int:
    if name == "run-log.json":
        return 3
    if name == "quality.json":
        return 2
    if name in {"delivery-receipt.json", "report-receipt.json"}:
        return 1
    return 0


def add_receipts(graph: Graph, root: Path, graph_config: dict[str, Any], jobs: dict[str, str]) -> None:
    latest: dict[str, tuple[str | None, int, str, str]] = {}
    quality_checker = graph.node(
        "quality_check:report_quality",
        "quality_check",
        "scripts/check_report_quality.mjs",
    )
    delivery_runner = graph.node(
        "delivery:readable_report",
        "delivery",
        "scripts/deliver_readable_report.mjs",
    )
    graph.edge(delivery_runner, file_node(graph, "scripts/deliver_readable_report.mjs", "script"), "executes")
    for path in receipt_paths(root, graph_config):
        relative = safe_rel(path, root)
        if not relative:
            continue
        payload = read_json(path, {})
        if not isinstance(payload, dict):
            continue
        status = payload_status(payload)
        stamp = payload_time(payload)
        receipt = file_node(graph, relative, "receipt", status=status, observed_at=stamp, sha256=digest(path))
        job_id = infer_job(payload, relative)
        if job_id in jobs:
            graph.edge(jobs[job_id], receipt, "observed_by")
            old = latest.get(job_id)
            priority = receipt_priority(path.name)
            newer = old is None or (stamp and (old[0] is None or stamp > old[0]))
            equal_time_higher_priority = old is not None and stamp == old[0] and priority > old[1]
            if newer or equal_time_higher_priority:
                latest[job_id] = (stamp, priority, status, relative)
        artifact_path = payload.get("artifact") if isinstance(payload.get("artifact"), str) else None
        artifact_rel = safe_rel(artifact_path, root) if artifact_path else None
        if path.name == "last-approved-version.json":
            report = graph.node("report:" + str(path.parent), "report", path.parent.name, scope="approved_report")
            approved = graph.node(
                "approved_version:" + relative,
                "approved_version",
                path.parent.name,
                status=status,
                revision=payload.get("revision") or payload.get("revision_id"),
                sha256=digest(path),
            )
            graph.edge(report, approved, "approves")
            graph.edge(approved, receipt, "observed_by")
        if path.name in {"delivery-receipt.json", "report-receipt.json"}:
            delivery = graph.node("delivery:" + str(path.parent), "delivery", path.parent.name, status=status)
            graph.edge(delivery, receipt, "observed_by")
            if artifact_rel:
                artifact = file_node(graph, artifact_rel, "artifact")
                graph.edge(artifact, quality_checker, "validates")
                graph.edge(quality_checker, delivery, "validates")
                graph.edge(delivery, artifact, "delivers")
    for job_id, (stamp, _priority, status, receipt) in latest.items():
        graph.nodes[jobs[job_id]].update({"receipt_status": status, "receipt_observed_at": stamp, "receipt_path": receipt})


def add_ad_hoc_reports(graph: Graph, root: Path, graph_config: dict[str, Any]) -> None:
    base = root / str(graph_config.get("ad_hoc_inclusion", {}).get("root", "analysis"))
    names = set(graph_config.get("ad_hoc_inclusion", {}).get("required_markers", []))
    if not base.exists():
        return
    for directory in sorted(item for item in base.iterdir() if item.is_dir()):
        matches = [item for item in directory.rglob("*.json") if item.name in names]
        if not matches:
            continue
        relative = safe_rel(directory, root)
        if not relative:
            continue
        report = graph.node("report:" + relative, "report", directory.name, scope="ad_hoc_receipted")
        for item in matches[:30]:
            path = safe_rel(item, root)
            if not path:
                continue
            payload = read_json(item, {})
            status = payload_status(payload) if isinstance(payload, dict) else "unknown"
            graph.edge(report, file_node(graph, path, "receipt", status=status, sha256=digest(item)), "observed_by")


def add_automation_nodes(
    graph: Graph,
    manifest: dict[str, Any],
    graph_config: dict[str, Any],
    jobs: dict[str, str],
    automations_root: Path | None,
) -> None:
    stages = manifest.get("stages", []) if isinstance(manifest.get("stages"), list) else []
    expected = {
        str(item["automation_id"]): str(item["expected_rrule"]).replace("RRULE:", "")
        for item in graph_config.get("declared_schedules", [])
        if item.get("automation_id")
    }
    automation_ids = {str(stage["automation_id"]) for stage in stages if stage.get("automation_id")}
    automation_ids.update(expected)
    for automation_id in sorted(automation_ids):
        actual = parse_automation(automation_id, automations_root)
        node = graph.node(
            "automation:" + automation_id,
            "automation",
            (actual or {}).get("name", automation_id),
            automation_id=automation_id,
            actual_status=(actual or {}).get("status", "unknown"),
            actual_rrule=(actual or {}).get("rrule"),
            actual_model=(actual or {}).get("model"),
        )
        for stage in stages:
            job_id = str(stage.get("id") or "")
            if stage.get("automation_id") == automation_id and job_id in jobs:
                graph.edge(node, jobs[job_id], "scheduled_by")
        if automation_id in expected:
            actual_rrule = str((actual or {}).get("rrule") or "").replace("RRULE:", "")
            if actual_rrule and actual_rrule != expected[automation_id]:
                graph.diagnostic(
                    "declared_vs_observed_mismatch",
                    "warning",
                    "文档声明的调度与生效 automation 不一致",
                    automation_id=automation_id,
                    expected_rrule=expected[automation_id],
                    actual_rrule=actual_rrule,
                )


def build_execution_graph(root: Path, *, automations_root: Path | None = None, reason: str = "manual") -> dict[str, Any]:
    root = root.resolve()
    graph_config = load_config(root)
    manifest = read_json(root / "jobs/manifest.json", {})
    if not isinstance(manifest, dict):
        raise ValueError("jobs/manifest.json is invalid")
    if automations_root is None:
        candidate = Path.home() / ".codex/automations"
        automations_root = candidate if candidate.exists() else None
    graph = Graph()
    graph.node("project:waje-analyst", "project", manifest.get("name", "Waje Analyst"), timezone=manifest.get("timezone"))
    stages = manifest.get("stages", []) if isinstance(manifest.get("stages"), list) else []
    report_jobs = set(graph_config.get("report_job_ids", []))
    jobs: dict[str, str] = {}
    scripts: list[str] = []
    for stage in stages:
        job_id = str(stage.get("id") or "")
        if not job_id:
            continue
        manual = stage.get("status") == "manual_only"
        node = graph.node(
            "job:" + job_id,
            "manual_workflow" if manual else "job",
            job_id,
            schedule=stage.get("schedule"),
            declared_status="manual" if manual else normalize_status(stage.get("status", "unknown")),
            report_chain=job_id in report_jobs,
            failure_policy=stage.get("failure_policy"),
        )
        jobs[job_id] = node
        graph.edge("project:waje-analyst", node, "depends_on")
        for script in extract_scripts(str(stage.get("script", ""))):
            scripts.append(script)
            graph.edge(node, file_node(graph, script, "script"), "executes")
        inputs = str(stage.get("input", ""))
        for path in extract_paths(inputs):
            if path.startswith("config/"):
                graph.edge(file_node(graph, path, "config"), node, "reads")
        source = source_kind(inputs)
        if source:
            source_node = graph.node("source:" + job_id + ":" + source, "source", source, external=True, redacted=True)
            graph.edge(source_node, node, "reads")
        outputs = str(stage.get("output", ""))
        for path in extract_paths(outputs):
            kind = "receipt" if any(term in path.lower() for term in ("receipt", "run-log", "quality", "manifest")) else "artifact"
            graph.edge(node, file_node(graph, path, kind), "writes")
        if manual:
            for workflow in stage.get("workflow", []):
                manual_node = graph.node("manual:" + str(workflow), "manual_workflow", str(workflow), status="manual", precondition=stage.get("reason"))
                graph.edge(node, manual_node, "depends_on")
    add_code_edges(graph, root, scripts)
    add_automation_nodes(graph, manifest, graph_config, jobs, automations_root)
    add_receipts(graph, root, graph_config, jobs)
    add_ad_hoc_reports(graph, root, graph_config)
    for job_id, event in latest_events(root).items():
        if job_id not in jobs:
            continue
        node = graph.nodes[jobs[job_id]]
        node.update({"observed_status": event["status"], "observed_at": event["occurred_at"], "last_run_id": event["run_id"]})
        for path in event["receipt_paths"]:
            graph.edge(jobs[job_id], file_node(graph, path, "receipt"), "observed_by")
        for path in event["artifact_paths"]:
            graph.edge(jobs[job_id], file_node(graph, path, "artifact"), "writes")
    for job_id, node_id in jobs.items():
        node = graph.nodes[node_id]
        if node["kind"] == "job" and "observed_status" not in node and "receipt_status" not in node:
            graph.diagnostic("missing_observation", "info", "任务尚无可关联的运行回执", job_id=job_id)
    nodes = sorted(graph.nodes.values(), key=lambda item: item["id"])
    edges = [{"source": source, "target": target, "type": kind} for source, target, kind in sorted(graph.edges)]
    statuses = Counter(
        str(node.get("observed_status") or node.get("receipt_status") or node.get("declared_status") or "unknown")
        for node in nodes if node["kind"] in {"job", "manual_workflow"}
    )
    payload = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "root": str(root),
        "reason": reason,
        "coverage": {
            "scope": "report_chain_plus_receipted_ad_hoc",
            "excluded_dirs": sorted(SKIP_PARTS),
            "external_sources": "logical_redacted_nodes",
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "status_counts": dict(sorted(statuses.items())),
        "nodes": nodes,
        "edges": edges,
        "diagnostics": graph.diagnostics,
    }
    run_id = dt.datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%z")
    receipt_path = root / OUTPUT / dt.date.today().isoformat() / run_id / "refresh-receipt.json"
    payload["refresh_receipt"] = safe_rel(receipt_path, root)
    write_json(root / GENERATED / "execution-graph.json", payload)
    write_text(root / GENERATED / "执行图看板.md", render_dashboard(payload))
    write_json(
        receipt_path,
        {
            "schema_version": 1,
            "status": "ok",
            "run_at": payload["generated_at"],
            "reason": reason,
            "source_coverage": payload["coverage"],
            "status_counts": payload["status_counts"],
            "diagnostic_count": len(graph.diagnostics),
            "artifacts": ["knowledge/_generated/execution-graph.json", "knowledge/_generated/执行图看板.md"],
        },
    )
    return payload


def mermaid_id(value: str) -> str:
    return "n_" + hashlib.sha1(value.encode()).hexdigest()[:10]


def render_dashboard(payload: dict[str, Any]) -> str:
    selected = [
        node for node in payload["nodes"]
        if node["kind"] in {"job", "manual_workflow", "script", "automation"}
        and (node.get("report_chain") or node["kind"] in {"manual_workflow", "automation"} or node["id"].startswith("job:"))
    ][:80]
    ids = {node["id"] for node in selected}
    mermaid = ["flowchart LR"]
    for node in selected:
        label = str(node["label"]).replace(chr(34), chr(39))[:90]
        mermaid.append(f'  {mermaid_id(node["id"])}["{label}"]')
    for edge in payload["edges"]:
        if edge["source"] in ids and edge["target"] in ids:
            mermaid.append(f'  {mermaid_id(edge["source"])} -->|{edge["type"]}| {mermaid_id(edge["target"])}')
    rows = ["|任务|声明状态|观测状态|最近回执|", "|---|---|---|---|"]
    for node in payload["nodes"]:
        if node["kind"] not in {"job", "manual_workflow"}:
            continue
        rows.append(
            f"| {node['label']} | {node.get('declared_status', node.get('status', 'unknown'))} | "
            f"{node.get('observed_status', node.get('receipt_status', 'unknown'))} | {node.get('receipt_path', '—')} |"
        )
    diagnostics = [f"- {item['severity']} {item['code']}：{item['message']}" for item in payload["diagnostics"]]
    if not diagnostics:
        diagnostics = ["- 暂无结构性诊断。"]
    return "\n".join([
        "---",
        "type: execution-graph-dashboard",
        "status: generated",
        f"updated: {payload['generated_at'][:10]}",
        "tags: [generated, execution-graph, report-chain]",
        "---",
        "",
        "# 报告链执行图看板",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 节点：{payload['coverage']['node_count']}；关系：{payload['coverage']['edge_count']}。",
        f"- 状态分布：{json.dumps(payload['status_counts'], ensure_ascii=False)}。",
        "- 外部来源仅为脱敏逻辑节点；状态只来自回执和事件。",
        "",
        "## 核心执行链",
        "",
        "~~~mermaid",
        *mermaid,
        "~~~",
        "",
        "## 任务状态",
        "",
        *rows,
        "",
        "## 诊断",
        "",
        *diagnostics,
        "",
        "> 完整机器可读拓扑见 execution-graph.json；本看板不渲染全部节点。",
        "",
    ])


def record_and_refresh(
    root: Path,
    *,
    job_id: str,
    run_id: str,
    phase: str,
    status: str,
    receipt_paths: Iterable[str] = (),
    artifact_paths: Iterable[str] = (),
    automations_root: Path | None = None,
) -> dict[str, Any]:
    event_key = add_event(root, job_id, run_id, phase, status, receipt_paths, artifact_paths)
    graph = build_execution_graph(root, automations_root=automations_root, reason=f"event:{job_id}:{phase}")
    return {"event_key": event_key, "refresh_receipt": graph["refresh_receipt"], "status": normalize_status(status)}


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--automations-root", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--reason", default="manual")
    record = sub.add_parser("record")
    record.add_argument("--job-id", required=True)
    record.add_argument("--run-id", required=True)
    record.add_argument("--phase", choices=("started", "finished"), required=True)
    record.add_argument("--status", required=True)
    record.add_argument("--receipt", action="append", default=[])
    record.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "build":
        result = build_execution_graph(root, automations_root=args.automations_root, reason=args.reason)
        print(json.dumps({"status": "ok", "nodes": len(result["nodes"]), "edges": len(result["edges"]), "refresh_receipt": result["refresh_receipt"]}, ensure_ascii=False))
        return 0
    result = record_and_refresh(
        root,
        job_id=args.job_id,
        run_id=args.run_id,
        phase=args.phase,
        status=args.status,
        receipt_paths=args.receipt,
        artifact_paths=args.artifact,
        automations_root=args.automations_root,
    )
    print(json.dumps({"status": "ok", **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
