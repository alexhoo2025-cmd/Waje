#!/usr/bin/env python3
"""Complete the 8/29 report refresh after Feishu regenerated block IDs.

The first pass already updated the source date, latest-retention values, and
release-event appendix. This recovery only writes the remaining requested
sections and fetches the document before every targeted change.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC_ID = "GyZddVm2powgFBxLwH0l18Qzguf"
RECEIPT = ROOT / "refresh_2026_08_29_receipt.json"


def run(args: list[str]) -> dict:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    result = subprocess.run(
        [CLI, *args, "--as", "user"], cwd=PROJECT, env=env,
        text=True, capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def fetch() -> tuple[str, int]:
    payload = run(["docs", "+fetch", "--doc", DOC_ID, "--detail", "with-ids", "--format", "json"])
    doc = payload["data"]["document"]
    return doc["content"], doc["revision_id"]


def tag_id_before_text(xml: str, text: str, tag: str | None = None) -> str:
    tag_pattern = tag or r"[a-z0-9_-]+"
    match = re.search(rf"<({tag_pattern})\b[^>]*\bid=\"([^\"]+)\"[^>]*>[\s\S]*?{re.escape(text)}", xml)
    if not match:
        raise KeyError(f"Cannot locate block containing: {text}")
    return match.group(2)


def next_table_id(xml: str, heading_text: str) -> str:
    position = xml.find(heading_text)
    if position < 0:
        raise KeyError(f"Cannot locate heading: {heading_text}")
    match = re.search(r"<table\b[^>]*\bid=\"([^\"]+)\"", xml[position:])
    if not match:
        raise KeyError(f"Cannot locate table after: {heading_text}")
    return match.group(1)


def replace(block_id: str, content: str) -> None:
    run(["docs", "+update", "--doc", DOC_ID, "--command", "block_replace", "--block-id", block_id, "--content", content])


def insert_after(block_id: str, content: str) -> None:
    run(["docs", "+update", "--doc", DOC_ID, "--command", "block_insert_after", "--block-id", block_id, "--content", content])


xml, _ = fetch()

# Make the previous-versus-current comparison explicit beside the existing
# first-pay / unpaid statement. Do not call either value lightweight-game play.
if "新增首充与新增未付费：与上线前对比" not in xml:
    paragraph_id = tag_id_before_text(xml, "分群观察：")
    replace(
        paragraph_id,
        "<p><b>分群对比：</b>上线后当日新增首充用户7天内有任意游戏记录为95.4%，较上线前96.5%下降1.1个百分点；当日新增未付费为42.1%，较上线前42.3%下降0.2个百分点。两组差距基本不变，该指标用于用户结构对照，不等同轻量化游戏参与率。</p>",
    )
    xml, _ = fetch()
    paragraph_id = tag_id_before_text(xml, "分群对比：")
    insert_after(
        paragraph_id,
        """
<h2>新增首充与新增未付费：与上线前对比</h2>
<table>
  <thead><tr><th><p>用户组</p></th><th><p>上线前：注册当日有游戏</p></th><th><p>上线后：注册当日有游戏</p></th><th><p>上线前：7天内有游戏</p></th><th><p>上线后：7天内有游戏</p></th></tr></thead>
  <tbody>
    <tr><td><p>当日新增首充</p></td><td><p>95.9%</p></td><td><p>94.5%</p></td><td><p>96.5%</p></td><td><p>95.4%</p></td></tr>
    <tr><td><p>当日新增未付费</p></td><td><p>40.7%</p></td><td><p>40.4%</p></td><td><p>42.3%</p></td><td><p>42.1%</p></td></tr>
  </tbody>
</table>
""",
    )

# The five-game section remains a short-term tracking view, while the nine-game
# section below becomes the product-defined contrast set requested by product.
xml, _ = fetch()
heading_id = tag_id_before_text(xml, "当前五款游戏：页面触达与短期回访", tag="h1")
replace(heading_id, "<h1>近期五款游戏：页面触达与短期回访</h1>")
xml, _ = fetch()
callout_id = tag_id_before_text(xml, "核心发现：8月21—27日Keno触达规模最大", tag="callout")
replace(
    callout_id,
    """
<callout emoji="💡" background-color="light-blue" border-color="blue">
  <p><b>短期观察：</b>8月21—27日，Keno在这五款追踪游戏中页面触达最大，Plinko人均页面浏览最高；Limbo的D1应用回访较高，Plinko的D3相对更稳。</p>
  <p><b>判断边界：</b>页面进入与应用回访只能说明相关性，不能据此认定单款游戏提升了留存。</p>
</callout>
""",
)

# Product-defined Top Games 9: retain the existing reach chart, then replace the
# table with four lightweight and five non-lightweight games plus D1/D3 values.
xml, _ = fetch()
h2_id = tag_id_before_text(xml, "产品定义的Top Games九款对照", tag="h2")
replace(h2_id, "<h2>产品Top Games九款：轻量化4款与非轻量化5款对照</h2>")
xml, _ = fetch()
description_id = tag_id_before_text(xml, "Top Games固定为Whot、Limbo、CoinFlip、Keno、ColorDice、Hilo、Plinko、Tower和Bottle spin")
replace(
    description_id,
    "<p><b>分组：</b>轻量化4款为CoinFlip、Limbo、Keno、ColorDice；非轻量化5款为Whot、Hilo、Plinko、Tower、Bottle spin。页面触达统计至8月27日；D1、D3分别只纳入已达到对应观察天数的新访客。</p>",
)
xml, _ = fetch()
top_table_id = next_table_id(xml, "产品Top Games九款：轻量化4款与非轻量化5款对照")
insert_after(
    top_table_id,
    '<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/07_产品TopGames九款_D1D3回访.png" width="880" caption="产品Top Games九款D1/D3应用回访；紫色标签代表轻量化4款"/>',
)
xml, _ = fetch()
top_table_id = next_table_id(xml, "产品Top Games九款：轻量化4款与非轻量化5款对照")
replace(
    top_table_id,
    """
<table>
  <thead><tr><th><p>分组</p></th><th><p>游戏 / ID</p></th><th><p>新访客</p></th><th><p>D1应用回访</p></th><th><p>D3应用回访</p></th><th><p>观察状态</p></th></tr></thead>
  <tbody>
    <tr><td><p>非轻量化</p></td><td><p>Whot / 6001</p></td><td><p>1,109</p></td><td><p>30.6%（n=935）</p></td><td><p>14.0%（n=529）</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>Limbo / 9008</p></td><td><p>647</p></td><td><p>29.0%（n=544）</p></td><td><p>13.9%（n=316）</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>CoinFlip / 9001</p></td><td><p>425</p></td><td><p>31.6%（n=351）</p></td><td><p>17.6%（n=204）</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>Keno / 9010</p></td><td><p>270</p></td><td><p>36.4%（n=231）</p></td><td><p>13.6%（n=140）</p></td><td><p>可观察</p></td></tr>
    <tr><td background-color="light-purple"><p>轻量化</p></td><td><p>ColorDice / 9003</p></td><td><p>413</p></td><td><p>25.2%（n=325）</p></td><td><p>15.7%（n=102）</p></td><td><p>可观察</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Hilo / 9011</p></td><td><p>184</p></td><td><p>34.4%（n=151）</p></td><td><p>16.7%（n=78）</p></td><td><p>小样本</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Plinko / 9016</p></td><td><p>365</p></td><td><p>31.3%（n=310）</p></td><td><p>17.3%（n=196）</p></td><td><p>可观察</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Tower / 9013</p></td><td><p>122</p></td><td><p>38.1%（n=84）</p></td><td><p>N/A</p></td><td><p>8/25上线，D3未成熟</p></td></tr>
    <tr><td><p>非轻量化</p></td><td><p>Bottle spin / 2003</p></td><td><p>709</p></td><td><p>31.4%（n=601）</p></td><td><p>11.0%（n=353）</p></td><td><p>可观察</p></td></tr>
  </tbody>
</table>
""",
)

xml, _ = fetch()
old_judgement_id = tag_id_before_text(xml, "解读：Top Games是产品固定分组")
replace(
    old_judgement_id,
    "<p><b>解读：</b>轻量化4款的D1范围为25.2%—36.4%，D3范围为13.6%—17.6%；非轻量化5款中Tower仅有D1样本，Hilo的D3分母为78人。当前只能做同窗口对照，不能据此判断轻量化整体优于或弱于非轻量化游戏。</p>",
)

xml, revision = fetch()
required = [
    "新增留存最新完整日为8月29日",
    "统计期间关键更新与干扰项",
    "新增首充与新增未付费：与上线前对比",
    "产品Top Games九款：轻量化4款与非轻量化5款对照",
    "轻量化4款为CoinFlip、Limbo、Keno、ColorDice",
    "Tower / 9013",
]
missing = [item for item in required if item not in xml]
if missing:
    raise RuntimeError(f"Readback missing expected content: {missing}")
RECEIPT.write_text(json.dumps({
    "status": "ok",
    "revision_id": revision,
    "retention_cutoff": "2026-08-29",
    "ga4_cutoff": "2026-08-27",
    "source_revisions": {"new_user_sheet": 732, "update_records": 1830, "game_code_technical_doc": 790},
    "validated_strings": required,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "ok", "revision_id": revision}, ensure_ascii=False))
