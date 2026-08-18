#!/usr/bin/env python3
"""Build a privacy-safe diff between two Waje release-experience observations.

The module compares observable experience facts, not gambling profitability. Financial
facts remain subject to server-side ledger and event reconciliation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from render_analysis_report_html import render_markdown_file


ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_KEYS = {
    "account_id",
    "bank_account",
    "cookie",
    "device_id",
    "email",
    "password",
    "phone_number",
    "token",
    "user_id",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def redact(value: Any) -> Any:
    """Remove accidentally supplied identifiers before an observation is diffed."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def stable_hash(value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def observation_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for item in payload.get("observations", []):
        observation_id = str(item.get("id") or "").strip()
        if observation_id:
            records[observation_id] = redact(item)
    return records


def context(payload: dict[str, Any]) -> dict[str, Any]:
    return redact(
        {
            "release_context": payload.get("release_context", {}),
            "source": payload.get("source"),
            "environment": payload.get("environment"),
            "sample_type": payload.get("sample_type"),
            "observed_at": payload.get("observed_at"),
        }
    )


def build_comparison(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    before = observation_map(baseline)
    after = observation_map(candidate)
    before_ids, after_ids = set(before), set(after)
    changed: list[dict[str, Any]] = []

    for observation_id in sorted(before_ids & after_ids):
        before_facts = before[observation_id].get("facts", {})
        after_facts = after[observation_id].get("facts", {})
        for key in sorted(set(before_facts) | set(after_facts)):
            old_value, new_value = before_facts.get(key), after_facts.get(key)
            if stable_hash(old_value) != stable_hash(new_value):
                changed.append(
                    {
                        "observation_id": observation_id,
                        "field": key,
                        "baseline": old_value,
                        "candidate": new_value,
                    }
                )

    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseline": context(baseline),
        "candidate": context(candidate),
        "summary": {
            "baseline_observation_count": len(before),
            "candidate_observation_count": len(after),
            "added_observations": len(after_ids - before_ids),
            "removed_observations": len(before_ids - after_ids),
            "changed_facts": len(changed),
        },
        "added_observations": [after[key] for key in sorted(after_ids - before_ids)],
        "removed_observations": [before[key] for key in sorted(before_ids - after_ids)],
        "changed_facts": changed,
        "guardrails": [
            "Experience differences are not causal business-impact estimates.",
            "Single-round results must not be used to infer RTP, probability or player profitability.",
            "Payment, reward and withdrawal facts require server-side event and ledger reconciliation.",
        ],
    }


def as_cell(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return text.replace("|", "\\|").replace("\n", " ")[:180]


def render_markdown(comparison: dict[str, Any], baseline_path: str, candidate_path: str) -> str:
    summary = comparison["summary"]
    baseline_ctx = comparison["baseline"]["release_context"]
    candidate_ctx = comparison["candidate"]["release_context"]
    lines = [
        "---",
        "type: release-experience-comparison",
        "domain: product",
        "status: generated",
        f"updated: {dt.datetime.now().astimezone().date().isoformat()}",
        "tags: [waje, release, h5, experience, reward-risk, comparison]",
        "---",
        "",
        f"# Waje 版本体验与数据对比｜{candidate_ctx.get('release_id', 'unknown-release')}",
        "",
        "## 1. 比对范围",
        "",
        f"- 基线：`{baseline_ctx.get('release_id', 'unknown')}` / 版本 `{baseline_ctx.get('version', 'unknown')}`。",
        f"- 候选：`{candidate_ctx.get('release_id', 'unknown')}` / 版本 `{candidate_ctx.get('version', 'unknown')}`。",
        f"- 基线观测：`{baseline_path}`。",
        f"- 候选观测：`{candidate_path}`。",
        "- 本文比较用户可见体验和记录字段；经营影响需另行用完整日、成熟 cohort 和服务端事实表验证。",
        "",
        "## 2. 结构化差异摘要",
        "",
        "| 指标 | 数量 |",
        "|---|---:|",
        f"| 基线观测项 | {summary['baseline_observation_count']} |",
        f"| 候选观测项 | {summary['candidate_observation_count']} |",
        f"| 新增观测项 | {summary['added_observations']} |",
        f"| 移除观测项 | {summary['removed_observations']} |",
        f"| 变更字段 | {summary['changed_facts']} |",
        "",
        "## 3. 已观察字段变更",
        "",
    ]
    changes = comparison["changed_facts"]
    if changes:
        lines.extend(["| 观测项 | 字段 | 基线 | 候选 |", "|---|---|---|---|"])
        lines.extend(
            f"| `{item['observation_id']}` | `{item['field']}` | {as_cell(item['baseline'])} | {as_cell(item['candidate'])} |"
            for item in changes
        )
    else:
        lines.append("- 当前结构化观测中未发现可直接比较的字段变化；不代表产品、配置或数据没有变化。")

    lines.extend(
        [
            "",
            "## 4. 发布后必须补齐的数据对比",
            "",
            "- 使用发布前后各 7 个完整自然日，剔除未完整日、全零异常日和未成熟 cohort。",
            "- 按 H5/APP、版本/构建、包体、渠道、地区、设备档位、网络、游戏、场次和资产类型切分。",
            "- 核对：启动/登录、游戏进入、可操作首帧、首注、匹配、GAMEEND、资产流水、充值、提现、任务/福利。",
            "- 同时报告样本量、分母、数据源、延迟、异常率和是否为 BQ 认证事实。",
            "",
            "## 5. 福利与数值风险验证门禁",
            "",
            "- 单账户、官方测试路径：同一活动在重复点击、刷新、重登、网络重试后最多产生一次奖励。",
            "- 资格与资产：新手、首充、每日、邀请、Coins、BonusChip 与现金资产的资格、有效期、可投注范围和提现限制一致。",
            "- 发布切换：版本/配置变更不能重置已领取状态，不能造成现金与奖励资产错账。",
            "- 结算：下注、游戏结束、奖励和流水应由 `round_id/unique_id + trace_id` 逐笔对账。",
            "- 任何疑似重复奖励、资格绕过或资产错账只在测试/预发环境复现并立即止损；不得在生产做多账号、并发、绕过或提现获利验证。",
            "",
            "## 6. 回归结论模板",
            "",
            "- [ ] 版本与配置 revision 已确认并可追溯。",
            "- [ ] 新手主线、福利、首局、钱包、充值/提现门槛均有体验证据。",
            "- [ ] 关键链路事件与 BQ/流水对账通过。",
            "- [ ] 奖励幂等、资格隔离、资产类型与版本切换回归通过。",
            "- [ ] 发布前后数据差异达到预定义质量门槛，未出现 P0 资金或结算异常。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="Baseline observation JSON, relative to project root or absolute")
    parser.add_argument("--candidate", required=True, help="Candidate observation JSON, relative to project root or absolute")
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--output-dir", default="data/outputs/release_experience")
    parser.add_argument("--knowledge-dir", default="knowledge/01-产品/版本体验")
    args = parser.parse_args()

    def resolve(raw: str) -> Path:
        path = Path(raw)
        return path if path.is_absolute() else ROOT / path

    baseline_path, candidate_path = resolve(args.baseline), resolve(args.candidate)
    comparison = build_comparison(load_json(baseline_path), load_json(candidate_path))
    output_dir, knowledge_dir = resolve(args.output_dir), resolve(args.knowledge_dir)
    write_json(output_dir / args.release_id / "experience-comparison.json", comparison)
    report_path = knowledge_dir / f"{args.release_id}-版本体验与数据对比.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(comparison, str(baseline_path.relative_to(ROOT)), str(candidate_path.relative_to(ROOT))), encoding="utf-8")
    html_path = render_markdown_file(report_path)
    print(
        json.dumps(
            {
                "status": "ok",
                "release_id": args.release_id,
                "report": str(report_path.relative_to(ROOT)),
                "html_report": str(html_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
