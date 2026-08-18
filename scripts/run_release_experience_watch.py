#!/usr/bin/env python3
"""Watch for confirmed Waje releases and create a safe experience-comparison task.

Confirmed release manifests are the primary trigger. A configuration revision change is
recorded as a candidate signal only, because configuration edits are not production
release proof.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def resolve(path: str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_manifests(directory: Path, required_fields: list[str]) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            continue
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            continue
        if str(payload.get("status")).lower() != "released":
            continue
        manifests.append(
            {
                "release_id": str(payload["release_id"]),
                "version": str(payload["version"]),
                "surfaces": payload.get("surfaces", []),
                "released_at": payload["released_at"],
                "source": payload["source"],
                "change_summary": payload.get("change_summary", []),
                "path": display_path(path),
                "content_hash": file_hash(path),
            }
        )
    return manifests


def configuration_signal(index_path: Path) -> dict[str, Any]:
    index = load_json(index_path)
    return {
        "available": bool(index),
        "revision": index.get("revision"),
        "content_hash": index.get("content_hash"),
        "fetched_at": index.get("fetched_at"),
    }


def render_release_task(release: dict[str, Any], baseline: dict[str, Any], signal: dict[str, Any]) -> str:
    summary = release.get("change_summary") or ["发布清单未提供变更摘要；先核对需求、配置与版本说明。"]
    summary_lines = "\n".join(f"- {str(item)}" for item in summary)
    return f"""---
type: release-experience-task
domain: product
status: pending-experience
updated: {dt.datetime.now().astimezone().date().isoformat()}
tags: [waje, release, h5, experience, reward-risk, regression]
---

# Waje 版本体验与数据对比任务｜{release['release_id']}

## 发布证据

- 版本：`{release['version']}`。
- 端/范围：`{', '.join(map(str, release['surfaces']))}`。
- 发布时间：`{release['released_at']}`。
- 来源：`{release['source']}`。
- 发布清单：`{release['path']}`。
- 当前配置 revision：`{signal.get('revision')}`（只作辅助证据）。
- 对比基线：`{baseline.get('release_id', 'unknown')}` / `{baseline.get('experience_report_path', 'missing')}`。

## 已声明变更

{summary_lines}

## 体验矩阵

- [ ] 新建 Day 0 测试样本：注册/登录、欢迎资产、新手引导、Daily Chip、任务与 Mail。
- [ ] 留存样本：大厅、搜索、分类、运营弹窗、账户中心、客服与帮助。
- [ ] 每种高优先级玩法至少一条正常最小闭环：进入、加载、选场、下注、局内操作、GAMEEND、流水、余额。
- [ ] 福利按一次官方路径验证：曝光、资格、领取、奖励到账、资产类型、可用范围与失效规则。
- [ ] 充值/提现只在测试/沙箱且有明确授权时验证；生产不得输入真实支付资料或提交外部付款。

## 奖励与数值风险验证

- [ ] 重复点击、刷新、重登、网络重试后，同一 `user + campaign + claim_period` 最多产生一笔奖励。
- [ ] 首充、每日、邀请、Coins、BonusChip 与现金的资格、限额、有效期和提现限制可由服务端确认。
- [ ] 版本/热更/配置切换不会重置已领取状态或导致资产错账。
- [ ] `BET → GAMEEND → reward → ledger` 可按 round_id/trace_id 对账。
- [ ] 所有疑似漏洞只在测试/预发通过单账户、受控数据复现；禁止多账号、身份绕过、并发重复领取、自动化批量操作或外部提现获利。

## 发布后数据对比

- [ ] 发布前后各 7 个完整日；剔除未完整日、零值异常日和未成熟 cohort。
- [ ] 首屏/登录/游戏加载/首局/首注/结算/资产、充值、提现、任务福利按版本、包、渠道、设备、网络和游戏切分。
- [ ] 标明样本量、分母、BQ 事实来源、数据延迟与异常率；不能仅用单局体验判断 RTP 或商业化效果。
"""


def run_watch(config_path: Path, date: str) -> dict[str, Any]:
    config = load_json(config_path)
    manifest_dir = resolve(config["release_manifest_dir"])
    state_path = resolve(config["state_path"])
    output_dir = resolve(config["output_dir"])
    knowledge_dir = resolve(config["knowledge_dir"])
    baseline = load_json(resolve(config["baseline_manifest_path"]))
    manifests = release_manifests(manifest_dir, list(config["release_manifest_required_fields"]))
    signal = configuration_signal(resolve(config["configuration_index_path"]))
    old_state = load_json(state_path)
    known = set(old_state.get("known_release_ids", []))
    detected = [item for item in manifests if item["release_id"] not in known]

    if not old_state:
        status = "release_detected" if detected else "initialized"
    elif detected:
        status = "release_detected"
    elif signal != old_state.get("configuration_signal"):
        status = "config_changed_needs_release_manifest"
    else:
        status = "unchanged"

    task_paths: list[str] = []
    for release in detected:
        task_path = knowledge_dir / f"{release['release_id']}-版本体验与数据对比任务.md"
        task_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.write_text(render_release_task(release, baseline, signal), encoding="utf-8")
        task_paths.append(display_path(task_path))

    result = {
        "schema_version": 1,
        "date": date,
        "status": status,
        "configuration_signal": signal,
        "detected_releases": detected,
        "created_tasks": task_paths,
        "policy": config["policy"],
    }
    write_json(output_dir / date / "release-watch.json", result)
    write_json(
        state_path,
        {
            "schema_version": 1,
            "updated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "known_release_ids": sorted(known | {item["release_id"] for item in detected}),
            "configuration_signal": signal,
        },
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/release_experience_watch.json")
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    args = parser.parse_args()
    result = run_watch(resolve(args.config), args.date)
    print(json.dumps({"status": result["status"], "detected": len(result["detected_releases"]), "tasks": result["created_tasks"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
