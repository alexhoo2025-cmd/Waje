#!/usr/bin/env python3
"""Audit local Gemini receipts, not cloud-wide usage. Never copy raw model output."""
import argparse
import collections
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(root, end):
    start = end - dt.timedelta(days=13)
    records, boundary = [], []
    paths = sorted((root / "data/outputs/gemini").glob("*/*/receipt.json"))
    for path in paths:
        d = json.loads(path.read_text())
        date = (d.get("started_at") or d.get("report_date") or path.parents[1].name)[:10]
        if not start.isoformat() <= date <= end.isoformat() and date != (start - dt.timedelta(days=1)).isoformat():
            continue
        result_path = path.with_name("result.json")
        result = json.loads(result_path.read_text()) if result_path.exists() else {}
        pre = d.get("preflight") or {}
        attempts = d.get("model_attempts")
        invoked = bool(attempts) if attempts is not None else (False if pre.get("status") == "blocked" and not d.get("stages") else None)
        # Older receipts record CLI timeout/IAM outcomes but no per-attempt ledger.
        if invoked is None and (d.get("status") == "blocked_iam" or "timed out" in d.get("error", "").lower()):
            invoked = True
        record = {"date": date, "task_id": d.get("task_id", path.parent.name), "task_type": d.get("task_type", "competitor_trial"),
            "status": d.get("status", "unknown"), "reason": pre.get("reason") or d.get("error", "unknown"),
            "cli_attempted": invoked, "model_attempt_count": len(attempts) if attempts is not None else None,
            "has_model_result": bool(result), "source_count": len(result.get("sources", [])),
            "metrics_count": len(result.get("metrics", [])), "duration_seconds": d.get("duration_seconds"),
            "receipt": str(path.relative_to(root)), "verified_downstream_consumption": False if not result else None}
        (records if start.isoformat() <= date <= end.isoformat() else boundary).append(record)
    cfg = json.loads((root / "config/gemini-enterprise.json").read_text())
    jobs = json.loads((root / "jobs/manifest.json").read_text())
    stages = [s.get("id") for s in jobs.get("stages", []) if "gemini" in str(s.get("script", "")).lower()]
    extra = []
    for base in (root / "analysis", root / "data/outputs"):
        for path in base.rglob("*.json"):
            name = str(path.relative_to(root))
            if "/gemini/" not in name and any(x in name.lower() for x in ("gemini", "vertex", "enterprise", "agent")) and any(x in path.name.lower() for x in ("receipt", "preflight", "run-log")):
                # Discovery only. These are not automatically model runs.
                extra.append(name)
    return {"status": "partial", "window": {"from": start.isoformat(), "to": end.isoformat(), "timezone": "Asia/Hong_Kong", "basis": "14 calendar dates, current date partial"},
        "coverage": "local persisted receipts only; cloud/web executions and unrecorded dispatches unknown",
        "records": records, "boundary_context_not_in_denominator": boundary,
        "summary": {"recorded_tasks": len(records), "statuses": dict(collections.Counter(r["status"] for r in records)),
            "cli_attempted_tasks": sum(r["cli_attempted"] is True for r in records), "usable_results": sum(r["has_model_result"] for r in records)},
        "configuration": {"gemini_manifest_stages": stages, "generic_allowed_datasets": len(cfg.get("allowed_datasets", [])),
            "generic_allowed_views": len(cfg.get("allowed_views", [])), "agent_platform_safe_views": len(cfg.get("agent_platform", {}).get("safe_views", [])),
            "note": "Agent Platform candidate safe views do not populate the generic bridge allowlist; their presence does not prove deployment or IAM."},
        "other_candidate_receipts": sorted(set(extra)), "generated_at": dt.datetime.now(dt.timezone.utc).isoformat()}


def render(d):
    s = d["summary"]
    lines = ["# Gemini 专用流程近两周评估", "", f"窗口：{d['window']['from']} 至 {d['window']['to']}，香港时间；今天为未完整日。", "",
        f"**已记录任务 {s['recorded_tasks']} 次，可用模型结果 {s['usable_results']} 份。当前本地证据不支持继续默认优先委派 Gemini。**", "",
        "这不是账户全量调用统计。网页 Agent、云端任务及未落盘分派的执行量未知；不将缺失回执计成零。", "",
        "|日期|任务|状态|调用情况|结果|", "|---|---|---|---|---|"]
    for r in d["records"]:
        lines.append(f"|{r['date']}|{r['task_id']}|{r['status']}|{'尝试CLI' if r['cli_attempted'] else '未知/未调用'}|{'存在，待审计' if r['has_model_result'] else '无可用结果'}|")
    lines += ["", "## 核心判断与调整", "",
        "- 公开检索遇 IAM 拒绝，企业 BQ 分析遇超时；这是调用链路和可用性问题，无法据此评价 Gemini 模型本身的分析能力。",
        "- 旧回执缺少结束时间和逐次调用记录，不能计算可信平均耗时、Token效率或整体成功率。",
        "- 通用桥接允许数据集/视图为空；Agent Platform 候选 safe views 是另一套配置，不能当成当前已可查询的授权。",
        "- 项目任务清单没有 Gemini 专用脚本调度项；配置中的 Agent 名称、计划时间不证明云端任务已部署或运行。",
        "- 通用公开资料分析、材料拆解、报告和代码审查转交 Claude；主 Agent 负责来源采集、聚合查询和最终审计。",
        "- Gemini 通用自动分派关闭；企业 BQ / Agent Platform 专项保留。正常桥接调用暂停，恢复测试需显式 recovery-probe。",
        "- 恢复顺序：企业身份 → Vertex推理 → 允许视图/只读查询（BQ任务）→ 真实结构化结果 → 下游消费回读。恢复成功后再显式调整可用性配置。",
        "- 不改云端部署、IAM、账户或专用数据权限；CLI/网页可用性分别记录，不互相替代。", "", "## 边界补充（不计入两周分母）", ""]
    for r in d["boundary_context_not_in_denominator"]:
        lines.append(f"- {r['date']}：{r['task_id']}，{r['status']}；{r['reason']}。")
    lines += ["", "## 回执来源", ""]
    for r in d["records"] + d["boundary_context_not_in_denominator"]:
        lines.append(f"- [{r['task_id']}](../../{r['receipt']})")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(); p.add_argument("--date", default=dt.date.today().isoformat()); p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(); d = audit(ROOT, dt.date.fromisoformat(a.date))
    a.output.mkdir(parents=True, exist_ok=True)
    for name, text in (("audit.json", json.dumps(d, ensure_ascii=False, indent=2)), ("report.md", render(d))):
        with (a.output / name).open("x", encoding="utf-8") as f:
            f.write(text)
    print(json.dumps(d["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
