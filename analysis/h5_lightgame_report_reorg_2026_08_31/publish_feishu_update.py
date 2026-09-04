#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = Path("/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli")
DOC = "https://ksg964l11fam.sg.larksuite.com/wiki/QYbiws4OEit03Uke92rlfzmcgWb"
ANCHOR = "doxlg2tgFTz641f6z6aAt2vWdBh"


def run(args: list[str], *, yes: bool = False) -> dict:
    command = [str(CLI), *args, "--as", "user"]
    command.extend(["--format", "json"])
    completed = subprocess.run(
        command,
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        payload = {"raw": output}
    if completed.returncode != 0 or not payload.get("ok", False):
        raise RuntimeError(f"lark-cli failed exit={completed.returncode}: {output[:1600]}")
    return payload


def fetch_keyword(keyword: str) -> dict:
    return run([
        "docs", "+fetch", "--doc", DOC,
        "--scope", "keyword", "--keyword", keyword,
        "--detail", "with-ids",
    ])


def str_replace(pattern: str, content: str) -> dict:
    return run([
        "docs", "+update", "--doc", DOC,
        "--command", "str_replace",
        "--pattern", pattern,
        "--content", content,
    ], yes=True)


def main() -> int:
    receipt: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "doc": DOC,
        "operations": [],
    }
    existing = fetch_keyword("当前数据可用性与新增用户链路")
    existing_content = existing["data"]["document"].get("content", "")
    if "当前数据可用性与新增用户链路" not in existing_content:
        insert_xml = (ROOT / "feishu_insert.xml").read_text("utf-8")
        result = run([
            "docs", "+update", "--doc", DOC,
            "--command", "block_insert_after",
            "--block-id", ANCHOR,
            "--content", insert_xml,
        ], yes=True)
        receipt["operations"].append({"operation": "insert_refresh_sections", "result": result["data"].get("result")})
    else:
        receipt["operations"].append({"operation": "insert_refresh_sections", "result": "skipped_existing"})

    replacements = [
        (
            "Waje H5轻量化游戏上线后留存与活跃度效果分析 V4（阶段性）",
            "Waje H5轻量化游戏新增用户全链路与留存影响分析 V4（持续更新）",
        ),
        (
            "当前只收集到整体留存和应用加载的部分数据，缺失游戏行为数据和应用设备和性能数据；基于当前可获取的数据进行了初步分析，后续收集更多数据更新和充实报告，持续追踪轻量化游戏效果",
            "当前已补入GA4游戏页面触达、D1/D3应用回访、外部生产Metabase首充用户局数与下注快照；入口点击、GAME_LOAD/GAME_READY/BET_READY和首局结算仍缺失，报告按可验证阶段持续更新。",
        ),
        (
            "数据窗口：2026年6月16日—8月16日｜观察日：2026年8月19日｜对象：H5自然、PWA自然、H5 Facebook、H5 Google。",
            "历史留存窗口：2026年6月16日—8月16日｜当前行为窗口：2026年8月20日—26日｜共同完整日：2026年8月26日。",
        ),
    ]
    for pattern, content in replacements:
        result = str_replace(pattern, content)
        receipt["operations"].append({"operation": "str_replace", "pattern": pattern[:40], "result": result["data"].get("result")})

    callout = (
        '<callout emoji="💡" background-color="light-blue" border-color="blue">'
        '<p><b>核心判断：</b>新增用户的轻量化游戏页面触达和D1/D3应用回访已经可以横向比较，但完整的加载、可玩、下注和结算漏斗仍被数据缺口阻断。'
        'Limbo触达规模最大；Plinko人均页面浏览较高；Keno D1回访最高；Hilo D3回访较高但样本小。'
        '历史留存改善仍集中在H5自然和Google，Facebook与PWA未同步改善。当前证据只支持关联观察，不支持单游戏因果结论。</p>'
        '</callout>'
    )
    result = run([
        "docs", "+update", "--doc", DOC,
        "--command", "block_replace",
        "--block-id", ANCHOR,
        "--content", callout,
    ], yes=True)
    receipt["operations"].append({"operation": "replace_core_callout", "result": result["data"].get("result")})

    old_titles = [
        "四渠道新增与留存对比",
        "上线前后：H5自然和Google改善，Facebook与PWA未同步改善",
        "首周仍是最大流失区间",
        "发布节点观察：Color Dice后整体D3/D7走高",
        "活跃与游戏参与：当前可见边界",
        "GA4页面活跃快照",
        "游戏游玩与下注数据：H5筛选验收未通过",
        "修复后可补入的正式数据",
        "下一步：先把数据查准，再分析单游戏",
        "统计范围与来源",
    ]
    for title in old_titles:
        result = str_replace(title, f"历史基线｜{title}")
        receipt["operations"].append({"operation": "rename_history_section", "pattern": title, "result": result["data"].get("result")})

    verify = fetch_keyword("当前数据可用性与新增用户链路|五款游戏页面触达与短期回访|数据质量与来源")
    verify_content = verify["data"]["document"].get("content", "")
    expected = ["当前数据可用性与新增用户链路", "五款游戏页面触达与短期回访", "数据质量与来源"]
    receipt["verification"] = {
        "revision_id": verify["data"]["document"].get("revision_id"),
        "all_expected_present": all(x in verify_content for x in expected),
        "expected": expected,
    }
    receipt["status"] = "ok" if receipt["verification"]["all_expected_present"] else "failed"
    (ROOT / "feishu_publish_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": receipt["status"], "revision": receipt["verification"]["revision_id"]}, ensure_ascii=False))
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
