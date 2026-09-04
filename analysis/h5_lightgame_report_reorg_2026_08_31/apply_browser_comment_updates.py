#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC_ID = "GyZddVm2powgFBxLwH0l18Qzguf"
RECEIPT = ROOT / "browser_comment_update_receipt.json"

if RECEIPT.exists():
    raise SystemExit("comment update receipt exists; refusing duplicate insertion")


def call(args: list[str]) -> dict:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    result = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{result.stderr[-2000:]}")
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def update(command: str, *, block_id: str | None = None, content: str | None = None,
           pattern: str | None = None) -> dict:
    args = ["docs", "+update", "--doc", DOC_ID, "--command", command]
    if block_id is not None:
        args += ["--block-id", block_id]
    if content is not None:
        args += ["--content", content]
    if pattern is not None:
        args += ["--pattern", pattern]
    return call(args)


ops = []

# Data freshness: state the actual source cutoffs rather than silently claiming yesterday.
update(
    "str_replace",
    pattern="数据范围：历史留存为2026年6月16日—8月16日；当前行为为8月21—27日；跨来源共同完整日为8月26日。",
    content="数据范围：历史留存为2026年6月16日—8月16日；GA4行为最新完整日为8月27日；新增留存最新完整日为8月26日。",
)
freshness_xml = """
<callout emoji="⚠️" background-color="light-yellow" border-color="yellow">
  <p><b>数据延迟：</b>截至8月31日，GA4尚未生成8月28—30日正式日表，飞书新增留存表也尚未写入8月27—30日。缺失日期不是0；报告先更新至各控制源的最新完整日，待起源补数后再延长到昨日。</p>
</callout>
"""
freshness_blocks = update("block_insert_after", block_id="doxlg7eXZeJ4M7pnF4OS0Y1odBd", content=freshness_xml)
ops.append("freshness_callout")

# Compact long-term retention so D15 is visible on narrow screens.
historical_table_xml = """
<table>
  <thead><tr><th><p>渠道/运行形态</p></th><th><p>新增用户</p></th><th><p>D1 / D3 / D7 / D15 / D30</p></th></tr></thead>
  <tbody>
    <tr><td><p>H5自然</p></td><td><p>206,167</p></td><td><p>35.2% / 20.9% / 11.7% / 5.3% / 3.2%</p></td></tr>
    <tr><td><p>H5 Facebook</p></td><td><p>365,038</p></td><td><p>27.7% / 15.0% / 6.8% / 3.4% / 2.1%</p></td></tr>
    <tr><td><p>H5 Google</p></td><td><p>85,362</p></td><td><p>39.7% / 24.1% / 12.9% / 7.4% / 5.6%</p></td></tr>
    <tr><td><p>PWA自然</p></td><td><p>19,121</p></td><td><p>45.3% / 27.6% / 12.0% / 8.6% / 5.8%</p></td></tr>
  </tbody>
</table>
"""
update("block_replace", block_id="doxlgkXdh0ocoyPzEMZBqi4N7lF", content=historical_table_xml)
ops.append("historical_d15")

# Preserve the PWA comment anchor while adding D15 to the controlled comparison.
cell_updates = {
    "doxlgtrhfFUl2hF8HTA2KNWqbqd": "<p>D1 / D3 / D7 / D15变化</p>",
    "doxlgLQ3omy5tlZOCIQyJOXYXOG": "<p>+7.6pp / +4.8pp / +3.8pp / +1.7pp</p>",
    "doxlg8ImeO7DHzK7QhxLQYDWFgb": "<p>-1.8pp / -0.1pp / -0.2pp / +0.3pp</p>",
    "doxlgdO7wMy6uEqWXk1ZUKclJDh": "<p>+3.8pp / +4.0pp / +1.0pp / -0.2pp</p>",
    "doxlg0nNKOAxp9VNUEcqZYDjrNg": "<p><b><span background-color=\"light-yellow\">-2.4pp / -2.3pp / -3.1pp / -4.4pp</span></b></p>",
    "doxlgIQoZ9aFmLTebc6tWbnNabe": "<p>综合判断</p>",
    "doxlgAqGjcqDlfPcgN1Auxu7bSb": "<p>留存全面改善</p>",
    "doxlgTQUCEP7J5OchCk6Bnbvh1e": "<p>扩量未改善</p>",
    "doxlg2bnql80eNurJwpY43UeqGh": "<p>质量升、规模降</p>",
    "doxlgv79C39VSqpU3rUtXxlOjpb": "<p><b><span background-color=\"light-yellow\">扩量伴随留存下降</span></b></p>",
}
for block_id, content in cell_updates.items():
    update("block_replace", block_id=block_id, content=content)
ops.append("controlled_comparison_d15")

# Add latest-available post-launch tracking with metric-specific maturity cutoffs.
latest_post_xml = """
<h2>上线后累计追踪：截至最新可用日</h2>
<p>上线后累计从7月14日开始；不同留存指标只统计已经走满对应天数的注册用户。D1截至8月25日、D3截至8月23日、D7截至8月19日、D15截至8月11日。</p>
<table>
  <thead><tr><th><p>渠道/运行形态</p></th><th><p>D1</p></th><th><p>D3</p></th><th><p>D7</p></th><th><p>D15</p></th></tr></thead>
  <tbody>
    <tr><td><p>H5自然</p></td><td><p>40.7%</p></td><td><p>24.1%</p></td><td><p>14.1%</p></td><td><p>6.8%</p></td></tr>
    <tr><td><p>H5 Facebook</p></td><td><p>26.8%</p></td><td><p>14.7%</p></td><td><p>6.5%</p></td><td><p>3.3%</p></td></tr>
    <tr><td><p>H5 Google</p></td><td><p>43.1%</p></td><td><p>27.0%</p></td><td><p>14.0%</p></td><td><p>7.6%</p></td></tr>
    <tr><td><p>PWA自然</p></td><td><p>43.2%</p></td><td><p>26.0%</p></td><td><p>11.4%</p></td><td><p>5.9%</p></td></tr>
  </tbody>
</table>
<p><b>说明：</b>源表没有D14留存字段，正式长期观察点为D15；本报告不从D14推算D15。该表用于当前追踪，不替代上方两个等长28天的效果比较。</p>
"""
update("block_insert_after", block_id="doxlgEsURSX1yS1kpIRGV3uHwRe", content=latest_post_xml)
ops.append("latest_post_tracking")

# Release-stage table with D15. Current-period D15 has only two available channel-days, so keep N/A.
stage_table_xml = """
<table>
  <thead><tr><th><p>阶段</p></th><th><p>日期窗口</p></th><th><p>新增用户</p></th><th><p>D1 / D3 / D7 / D15</p></th></tr></thead>
  <tbody>
    <tr><td><p>上线前基线</p></td><td><p>6/16—7/13</p></td><td><p>306,491</p></td><td><p>31.2% / 17.6% / 8.9% / 4.5%</p></td></tr>
    <tr><td><p>Limbo上线/恢复</p></td><td><p>7/14—7/22</p></td><td><p>98,577</p></td><td><p>29.6% / 17.1% / 8.5% / 4.6%</p></td></tr>
    <tr><td><p>H5 2.1.14 / Keno</p></td><td><p>7/23—7/28</p></td><td><p>56,988</p></td><td><p>31.6% / 17.4% / 9.4% / 4.7%</p></td></tr>
    <tr><td><p>Color Dice</p></td><td><p>7/29—8/05</p></td><td><p>89,639</p></td><td background-color="light-green"><p>33.7% / 20.5% / 10.2% / 5.1%</p></td></tr>
    <tr><td><p>Opera埋点期</p></td><td><p>8/06—8/10</p></td><td><p>60,270</p></td><td><p>34.3% / 19.8% / 9.7% / 5.0%</p></td></tr>
    <tr><td><p>当前期</p></td><td><p>8/11—8/16</p></td><td><p>63,736</p></td><td><p>35.8% / 20.7% / 11.1% / N/A</p></td></tr>
  </tbody>
</table>
"""
update("block_replace", block_id="doxlg6dkWviVRpWXHuXDX3ZKLhg", content=stage_table_xml)
ops.append("stage_d15")

# Recent cohort table: D15 is explicitly immature.
recent_table_xml = """
<table>
  <thead><tr><th><p>8月25日注册批次</p></th><th><p>新增</p></th><th><p>D1</p></th><th><p>D3</p></th><th><p>D7</p></th><th><p>D15</p></th></tr></thead>
  <tbody>
    <tr><td><p>H5自然</p></td><td><p>2,898</p></td><td><p>49.3%</p></td><td><p>29.4%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
    <tr><td><p>H5 Facebook</p></td><td><p>5,108</p></td><td><p>28.6%</p></td><td><p>17.3%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
    <tr><td><p>H5 Google</p></td><td><p>898</p></td><td><p>40.8%</p></td><td><p>27.6%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
    <tr><td><p>PWA/PWW</p></td><td><p>613</p></td><td><p>43.2%</p></td><td><p>33.3%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
  </tbody>
</table>
"""
update("block_replace", block_id="doxlgK1yam9yiB9ipnQYXR9Xccb", content=recent_table_xml)
ops.append("recent_d15")

# Top9 game-page comparison. This is a GA4 page-entry ranking, not verified homepage-slot exposure.
top9_xml = """
<h2>首页相关游戏页Top9对照</h2>
<p>按8月21—27日进入游戏页的新访客排序。GA4目前不能识别用户是否从首页TopGame槽位进入，因此这里是“游戏页触达Top9”，不是首页曝光排名。</p>
<img path="@./analysis/h5_lightgame_report_reorg_2026_08_31/charts/06_GA4首页相关游戏页Top9.png" width="880" caption="首页相关游戏页Top9：新增访客触达"/>
<table>
  <thead><tr><th><p>排名</p></th><th><p>游戏/ID</p></th><th><p>新访客</p></th><th><p>页面浏览</p></th><th><p>人均浏览</p></th></tr></thead>
  <tbody>
    <tr><td><p>1</p></td><td><p>ID 9998（名称待映射）</p></td><td><p>1,600</p></td><td><p>13,281</p></td><td><p>8.30</p></td></tr>
    <tr><td><p>2</p></td><td><p>Whot（6001）</p></td><td><p>1,109</p></td><td><p>38,447</p></td><td><p>34.67</p></td></tr>
    <tr><td><p>3</p></td><td><p>转盘（2001）</p></td><td><p>761</p></td><td><p>4,340</p></td><td><p>5.70</p></td></tr>
    <tr><td><p>4</p></td><td><p>转瓶子（2003）</p></td><td><p>709</p></td><td><p>5,446</p></td><td><p>7.68</p></td></tr>
    <tr><td><p>5</p></td><td background-color="light-purple"><p><b>Limbo（9008）</b></p></td><td><p>647</p></td><td><p>3,341</p></td><td><p>5.16</p></td></tr>
    <tr><td><p>6</p></td><td><p>新转盘（2002）</p></td><td><p>506</p></td><td><p>2,950</p></td><td><p>5.83</p></td></tr>
    <tr><td><p>7</p></td><td><p>Fish（3001）</p></td><td><p>480</p></td><td><p>18,357</p></td><td><p>38.24</p></td></tr>
    <tr><td><p>8</p></td><td><p>ID 4203（名称待映射）</p></td><td><p>473</p></td><td><p>4,405</p></td><td><p>9.31</p></td></tr>
    <tr><td><p>9</p></td><td><p>ID 9001（名称待映射）</p></td><td><p>425</p></td><td><p>3,732</p></td><td><p>8.78</p></td></tr>
  </tbody>
</table>
<p><b>判断：</b>Limbo在全游戏页新访客中排第5；Whot和Fish的人均页面浏览异常高，可能包含重复进入、刷新或游戏内路由，不能直接解释为局数。</p>
"""
update("block_insert_after", block_id="doxlgrdu04YxmLSB0bxpiHnEThd", content=top9_xml)
ops.append("top9_comparison")

readback = call(["docs", "+fetch", "--doc", DOC_ID, "--scope", "outline", "--max-depth", "3", "--detail", "with-ids", "--format", "json"])
receipt = {
    "status": "partial_latest_available",
    "revision_id": readback["data"]["document"]["revision_id"],
    "operations": ops,
    "source_cutoff": {"ga4": "2026-08-27", "origin_retention": "2026-08-26"},
    "requested_cutoff": "2026-08-30",
    "blocked_days": ["2026-08-28", "2026-08-29", "2026-08-30"],
    "outline": readback["data"]["document"]["content"],
}
RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": receipt["status"], "revision_id": receipt["revision_id"], "operations": len(ops)}, ensure_ascii=False))
