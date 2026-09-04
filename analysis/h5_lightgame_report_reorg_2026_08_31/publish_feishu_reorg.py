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
DOC_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/QYbiws4OEit03Uke92rlfzmcgWb"

if (ROOT / "feishu_reorg_receipt.json").exists():
    raise SystemExit("already published; receipt exists, refusing duplicate insertion")


def call(args: list[str]) -> dict:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    result = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}\n{result.stderr[-2000:]}")
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def update(command: str, *, block_id: str | None = None, content: str | None = None,
           pattern: str | None = None, src_block_ids: list[str] | None = None) -> dict:
    args = ["docs", "+update", "--doc", DOC_ID, "--command", command]
    if block_id is not None:
        args += ["--block-id", block_id]
    if content is not None:
        args += ["--content", content]
    if pattern is not None:
        args += ["--pattern", pattern]
    if src_block_ids is not None:
        args += ["--src-block-ids", ",".join(src_block_ids)]
    return call(args)


def new_ids(payload: dict) -> list[str]:
    return [row["block_id"] for row in payload["data"]["document"].get("new_blocks", [])]


def media(path: str, caption: str) -> str:
    payload = call([
        "docs", "+media-insert", "--doc", DOC_ID,
        "--file", path, "--width", "880", "--align", "center", "--caption", caption,
    ])
    data = payload["data"]
    if "block_id" in data:
        return data["block_id"]
    return data["document"]["block_id"]


receipt: dict[str, object] = {"doc_id": DOC_ID, "doc_url": DOC_URL, "operations": []}

# 1. Reader-facing title and retained headings. str_replace preserves comment anchors.
replacements = [
    ("Waje H5轻量化游戏新增用户全链路与留存影响分析 V5（持续更新）",
     "Waje H5轻量化游戏新增用户行为与留存影响分析（持续更新）"),
    ("历史基线｜四渠道新增与留存对比", "历史留存结构：四渠道差异"),
    ("历史基线｜上线前后：H5自然和Google改善，Facebook与PWA未同步改善",
     "上线前后效果：H5自然和Google改善，Facebook与PWA未同步"),
    ("历史基线｜首周仍是最大流失区间", "留存衰减：首周仍是主要流失区间"),
    ("历史基线｜发布节点观察：Color Dice后整体D3/D7走高",
     "发布节点观察：阶段走势改善，但不能归因到单款游戏"),
    ("五款游戏页面触达与短期回访", "当前五款游戏：页面触达与短期回访"),
    ("局数与下注：仅有首充用户累计快照", "游戏深度：当前仅有首充用户累计快照"),
    ("近期新增留存与用户分群", "近期新增留存"),
    ("当前数据可用性与新增用户链路", "完整漏斗：可验证范围与数据缺口"),
    ("设备、性能与问题定位", "设备与体验：优先排查移动端"),
    ("数据质量与来源", "附录：数据质量与来源"),
]
for old, new in replacements:
    update("str_replace", pattern=old, content=new)

# 2. Remove obsolete intro and historical sections superseded by the refreshed body.
delete_ids = [
    "WE78dGgu3o9cSJx6mIKlgsLbgic", "PWUxdr27HoX8y4x0VwYlCfwcgHb",
    "K30udi8iPoV9FSxJgqilLtUtgfh", "doxlgaoARjO1s3uq6SLSZKO2CZc",
    "doxlgJKgHGaMg4x0H76AKZDWwZc",
    "doxlgmxJWOlQ5JVDHRtCo6DMsAd", "doxlg6K3mLE8bujn9b0TXl06BJc",
    "doxlg6FpHGIGbDDSjs5KEdpeY7d", "doxlgXcmGePx3spICb31gXwwrJe",
    "doxlg498cnpNO7N2f3Lu0Zt2hEb", "doxlg6n3zA4HjCtKgAnqGvcPB2g",
    "doxlgFP54mufWj9qVTqREdM9nye", "doxlghb7vtxDGZQd92aoztjpxsc",
    "doxlggb4PruCoapbsbPeRbKAuJd", "doxlgkzF9Kax63MXOOkx2fQATab",
    "doxlg7OISB4HP6U8SaOwKnFxP3d", "doxlgCokuIAyt8UlN9dszOfKWUc",
    "doxlgZygHhTOztDGCnT71yGlrMe", "doxlgRaoFIN8X64uJU5sKmtRTUh",
    "doxlgRhSpu6f7hUdcZrgzOdx4wB", "doxlgim6zyBzihGWiEJ3dmjSCNg",
    "doxlg4kyVe9G8aD5lxG7qCkFVje", "doxlgcgLg02D9ENjnCFHlUedJN9",
    "doxlgPE7Rohn6IFVMhXzQUKJ50d", "doxlgISv14o5qIJLxkYP3RE5vJg", "doxlgSyEUMWbKix0dYFa0jZyCtc", "doxlgMocKcIuSDTAhQu8pmWvYGm",
    "doxlgSWUtTs1B6q8k1g6tH1DACd", "doxlgCyyUjGRq8FKW875iPVQvL1", "doxlgtSgz2q4icYLOUldsSwVUNh", "doxlgbYy945YrCNfO4Mzc93yK7t", "doxlgQAC824L9i7pPGVvnP7pwlg",
    "doxlgDzMk6k2O1gApb25kxm1zWh", "doxlgd7JvuYEN31QYJwKRgKiwms",
    "doxlgzLDGo8sylIMvYb8kVp61wh",
    "doxlgMEyqJytvFTJfhiDYUsP7Bh", "doxlg4NKZjkWYlvnbdYAYdSoVJE", "doxlgkcpqDASnxkEbTU6b1C67pf", "doxlg2W9JEDhsIYrd3Dxwpil3cv", "doxlgsVcJPlrMRTmUD3JPsuYRiV", "doxlgnIRNYkNvMoM65YkC038qgb", "doxlgxjuyrHJClmLbXjKEe9qB5f",
]
update("block_delete", block_id=",".join(delete_ids))

# 3. Insert refreshed top summary.
intro_xml = """
<p><b>数据范围：</b>历史留存为2026年6月16日—8月16日；当前行为为8月21—27日；跨来源共同完整日为8月26日。</p>
<callout emoji="💡" background-color="light-blue" border-color="blue">
  <p><b>轻量化效果：</b>正向留存信号集中在H5自然和Google；Facebook扩量后未改善，PWA新增扩大97.6%的同时D7下降3.1个百分点。</p>
  <p><b>当前游戏表现：</b>Limbo页面触达最大，Plinko重复进入强度最高；Keno D1回访较高，但D1到D3衰减明显。</p>
  <p><b>首充用户：</b>上线后96.0%的首充用户7天内有游戏记录；Facebook仅90.2%，明显低于自然量和Google。</p>
  <p><b>数据边界：</b>H5加载与可玩事件仍缺；下注和结算服务端事实存在，但入口、游戏和局次关联尚未通过，不能计算完整漏斗。</p>
</callout>
"""
intro_ids = new_ids(update("block_insert_after", block_id=DOC_ID, content=intro_xml))

# 4. Replace current behavior evidence with the refreshed 8/21—8/27 window.
game_callout_xml = """
<callout emoji="💡" background-color="light-blue" border-color="blue">
  <p><b>核心发现：</b>8月21—27日Limbo触达规模最大，Plinko人均页面浏览最高。Keno D1回访最高，Plinko D3回访相对更稳；当前只能描述页面触达与应用回访关联，不能认定单款游戏提升留存。</p>
</callout>
"""
game_callout_ids = new_ids(update("block_replace", block_id="doxlgcRUgyDtjw0Ac1DgTwcA8jw", content=game_callout_xml))

game_table_xml = """
<table>
  <thead><tr><th><p>游戏</p></th><th><p>进入游戏页的新访客</p></th><th><p>人均页面浏览</p></th><th><p>D1回访</p></th><th><p>D3回访</p></th></tr></thead>
  <tbody>
    <tr><td><p>Limbo</p></td><td><p>647</p></td><td><p>5.16</p></td><td><p>29.0%</p></td><td><p>13.9%</p></td></tr>
    <tr><td><p>Color Dice</p></td><td><p>413</p></td><td><p>4.01</p></td><td><p>25.2%</p></td><td><p>15.7%</p></td></tr>
    <tr><td><p>Plinko</p></td><td><p>365</p></td><td background-color="light-green"><p><b>6.27</b></p></td><td><p>31.3%</p></td><td background-color="light-green"><p><b>17.3%</b></p></td></tr>
    <tr><td><p>Keno</p></td><td><p>271</p></td><td><p>5.51</p></td><td background-color="light-green"><p><b>36.4%</b></p></td><td><p>13.6%</p></td></tr>
    <tr><td><p>Hilo</p></td><td><p>184</p></td><td><p>4.52</p></td><td><p>34.4%</p></td><td><p>16.7%</p></td></tr>
  </tbody>
</table>
"""
game_table_ids = new_ids(update("block_replace", block_id="doxlgtBpiY0i8xTke0ow0Hub0yc", content=game_table_xml))
update(
    "str_replace",
    pattern="观察边界：D1仅纳入8月25日及以前首次访问，D3仅纳入8月23日及以前首次访问；所有游戏D7均为N/A。用户可能进入多款游戏，各游戏人数不能相加为整体用户数量。",
    content="观察边界：D1仅纳入8月26日及以前首次访问，D3仅纳入8月24日及以前首次访问；所有游戏D7均为N/A。用户可能进入多款游戏，各游戏人数不能相加为整体用户数量。",
)
update(
    "str_replace",
    pattern="共同完整日截至2026年8月26日。GA4近7日记录1,149,317条Web事件和7,056名首次访问用户，但没有游戏加载、可玩、下注、结算或性能事件。缺失环节统一标记为blocked，不计为用户流失。",
    content="跨来源共同完整日截至2026年8月26日；GA4行为数据更新至8月27日。近7日记录1,140,489条Web事件和7,513名首次访问用户。H5加载与可玩事件缺失；下注、结算服务端事实存在，但入口、游戏和局次关联未通过。缺失环节不计为用户流失。",
)

availability_table_xml = """
<table>
  <thead><tr><th><p>阶段</p></th><th><p>状态</p></th><th><p>当前能回答什么</p></th></tr></thead>
  <tbody>
    <tr><td><p>新增注册、H5访问</p></td><td background-color="light-green"><p>可用</p></td><td><p>注册规模、页面访问和短期回访</p></td></tr>
    <tr><td><p>游戏页面进入</p></td><td background-color="light-yellow"><p>部分可用</p></td><td><p>表示路由进入，不代表点击或开局</p></td></tr>
    <tr><td><p>入口曝光/点击</p></td><td background-color="light-red"><p>blocked</p></td><td><p>H5来源、入口和game_id关联未通过</p></td></tr>
    <tr><td><p>GAME_LOAD / GAME_READY / BET_READY</p></td><td background-color="light-red"><p>blocked</p></td><td><p>H5专用事件尚未落地</p></td></tr>
    <tr><td><p>GAMESTART</p></td><td background-color="light-yellow"><p>覆盖不完整</p></td><td><p>不能把未命中解释为未玩</p></td></tr>
    <tr><td><p>有效下注</p></td><td background-color="light-yellow"><p>部分可用</p></td><td><p>仅有首充用户累计快照</p></td></tr>
    <tr><td><p>首局结算</p></td><td background-color="light-red"><p>blocked</p></td><td><p>GAMEEND异常约6.13%，尚未完成服务端对账</p></td></tr>
    <tr><td><p>D1/D3应用回访</p></td><td background-color="light-green"><p>可用</p></td><td><p>GA4首次访问批次的后续访问</p></td></tr>
    <tr><td><p>D7/D15</p></td><td background-color="light-yellow"><p>分源/未成熟</p></td><td><p>历史渠道留存可用；当前单游戏为N/A</p></td></tr>
  </tbody>
</table>
"""
availability_table_ids = new_ids(update("block_replace", block_id="doxlgL1GAKOKSXM3OMA9JCW5EJh", content=availability_table_xml))

quality_table_xml = """
<table>
  <thead><tr><th><p>数据项</p></th><th><p>状态</p></th><th><p>说明</p></th></tr></thead>
  <tbody>
    <tr><td><p>GA4日表</p></td><td background-color="light-yellow"><p>provisional</p></td><td><p>8月21—27连续7日；每日24类事件；全部WEB</p></td></tr>
    <tr><td><p>GA4用户级关联</p></td><td background-color="light-red"><p>blocked</p></td><td><p>user_id事件覆盖2.79%</p></td></tr>
    <tr><td><p>GA4性能与游戏过程</p></td><td background-color="light-red"><p>blocked</p></td><td><p>无GAME_LOAD/READY、Web Vitals和错误事件</p></td></tr>
    <tr><td><p>Origin GAMESTART / GAMEEND</p></td><td background-color="light-red"><p>blocked</p></td><td><p>GAMESTART覆盖不完整；GAMEEND异常约6.13%</p></td></tr>
    <tr><td><p>Metabase游戏深度</p></td><td background-color="light-yellow"><p>provisional</p></td><td><p>首充用户累计快照，不是首次开局时序</p></td></tr>
    <tr><td><p>新增留存</p></td><td background-color="light-green"><p>部分认证</p></td><td><p>起源验收到8月26；8月25批次D1/D3可用，D7未成熟</p></td></tr>
  </tbody>
</table>
"""
quality_table_ids = new_ids(update("block_replace", block_id="doxlgRqbtucf1FG4ngHSdrvCIru", content=quality_table_xml))

# 5. Insert the first-pay cohort section requested in comments.
firstpay_a_xml = """
<h1>首充用户专项：从首充日观察游戏参与</h1>
<p>首充日记为T0。当前用户主表只有日期粒度，能判断首充当日及7天内是否有游戏记录，不能判断同一天内“先付费还是先开局”。</p>
<table>
  <thead><tr><th><p>渠道/运行形态</p></th><th><p>上线后首充用户</p></th><th><p>首充后7天有游戏</p></th><th><p>7天无游戏</p></th><th><p>较上线前</p></th></tr></thead>
  <tbody>
    <tr><td><p>H5自然</p></td><td><p>21,194</p></td><td background-color="light-green"><p><b>99.0%</b></p></td><td><p>1.0%</p></td><td><p>+0.1pp</p></td></tr>
    <tr><td><p>H5 Facebook</p></td><td><p>14,980</p></td><td background-color="light-yellow"><p><b>90.2%</b></p></td><td background-color="light-red"><p><b>9.8%</b></p></td><td><p>-1.1pp</p></td></tr>
    <tr><td><p>H5 Google</p></td><td><p>4,853</p></td><td background-color="light-green"><p><b>98.8%</b></p></td><td><p>1.2%</p></td><td><p>+0.7pp</p></td></tr>
    <tr><td><p>PWA自然（映射待核验）</p></td><td><p>463</p></td><td><p>99.6%</p></td><td><p>0.4%</p></td><td><p>+1.0pp</p></td></tr>
    <tr><td><p>全部H5/PWA</p></td><td><p>51,409</p></td><td><p>96.0%</p></td><td><p>4.0%</p></td><td><p>-0.9pp</p></td></tr>
  </tbody>
</table>
<p><b>判断：</b>首充用户不玩游戏不是全局性问题；Facebook首充用户7天无游戏比例约为自然量和Google的8—10倍，应优先排查投放人群、首充成功页返回大厅及游戏入口承接。</p>
"""
firstpay_a_ids = new_ids(update("block_insert_after", block_id="-1", content=firstpay_a_xml))

firstpay_b_xml = """
<p><b>新增首充与新增未付费对照：</b></p>
<table>
  <thead><tr><th><p>渠道</p></th><th><p>新增首充7天有游戏</p></th><th><p>新增未付费7天有游戏</p></th><th><p>差距</p></th></tr></thead>
  <tbody>
    <tr><td><p>H5自然</p></td><td><p>98.9%</p></td><td><p>46.1%</p></td><td><p>+52.8pp</p></td></tr>
    <tr><td><p>H5 Facebook</p></td><td><p>89.3%</p></td><td><p>35.3%</p></td><td><p>+54.0pp</p></td></tr>
    <tr><td><p>H5 Google</p></td><td><p>98.8%</p></td><td><p>43.2%</p></td><td><p>+55.6pp</p></td></tr>
    <tr><td><p>H5其他</p></td><td><p>95.6%</p></td><td><p>48.9%</p></td><td><p>+46.7pp</p></td></tr>
  </tbody>
</table>
<p>该差异反映用户结构，不代表付费导致游戏参与；“当日新增未付费”也不等于永久免费用户。</p>
"""
firstpay_b_ids = new_ids(update("block_insert_after", block_id="-1", content=firstpay_b_xml))

action_xml = """
<h1>结论与行动</h1>
<ol>
  <li><b>P0｜优先修复Facebook承接。</b>用同媒体计划、同入口和同设备条件复测“注册→首充→返回大厅→游戏页→7天有游戏”。</li>
  <li><b>P0｜补齐H5前端链路。</b>上报入口曝光/点击、GAME_LOAD、GAME_READY、BET_READY、错误、重试和恢复，并携带game_id、入口、会话、H5版本和配置版本。</li>
  <li><b>P0｜建立认证游戏过程事实。</b>按注册日×游戏×渠道输出首日进入、有效下注、首局结算、局数分层及D1/D3/D7复玩。</li>
  <li><b>P0｜修复GAMEEND并完成服务端对账。</b>GAMESTART→GAMEEND→BETREWARD→ASSET关联通过、异常率降至1%以下后，再恢复首局完成和结算漏斗。</li>
  <li><b>P1｜继续追踪Hilo/Plinko。</b>D7/D15成熟后按相同上线年龄比较；小样本和未成熟结果继续显示N/A。</li>
  <li><b>P1｜分开复盘扩量与产品效果。</b>PWA和Facebook关注扩量后的用户质量，Google关注规模下滑原因，自然量验证留存改善能否持续。</li>
</ol>
"""
action_ids = new_ids(update("block_insert_after", block_id="-1", content=action_xml))

# 6. Upload refreshed and cohort-specific charts, then remove stale current-window charts.
reach_img = media("./analysis/h5_lightgame_report_reorg_2026_08_31/charts/02_新访客游戏页面触达.png", "8月21—27日首次访问用户的游戏页面触达")
return_img = media("./analysis/h5_lightgame_report_reorg_2026_08_31/charts/03_游戏页新访客D1D3回访.png", "进入游戏页的新访客D1/D3应用回访")
firstpay_img = media("./analysis/h5_lightgame_first_pay_path_v5_2026_08_28/charts/10_首充用户7天无游戏记录复核.png", "首充用户7天无游戏记录复核")
paid_free_img = media("./analysis/h5_lightgame_first_pay_path_v5_2026_08_28/charts/11_新增首充与新增未付费7天游戏参与.png", "新增首充与新增未付费的7天游戏参与")
update("block_delete", block_id="doxlgY9beu7YJhhO61EViKKJD2e,doxlgWbHAzfnDN2U4QTkXk3wLaf")

# 7. Reorder all retained blocks into one coherent reading path.
ordered = [
    *intro_ids,
    # Historical structure and pre/post effects. Commented blocks are moved intact.
    "doxlge17K0NG8rWNNgqaE1EADme", "doxlgkXdh0ocoyPzEMZBqi4N7lF", "doxlgYlbhMfAu8IOd3uaTyUUvCe", "doxlgo3bdysGjM5gH6KQ51p2tHc",
    "doxlgOnJxaPzrQsEqckPYCXDiBh", "doxlgH0gh6anBfB6irNTZJFO3Qb", "doxlgEsURSX1yS1kpIRGV3uHwRe", "doxlgeIb9IUCXkNoVr0pA6qIu1b", "doxlghy8QZ2qThdDlvTzPHKuPrb", "doxlgQ6nCmra57EUGc99FNTPlHb", "doxlgsXivWjXpwDZ5uJf2FJb0Yb",
    "doxlgapdHc8ZCDjOA1lEAdTtDmg", "doxlgrPLsn1XjK3mbGVsQD4qrfh", "doxlgsQ5Hqrr2gptt2vLPWP49Sd", "doxlgbGgqvlFyUEBWeESQECeoPf", "doxlgnxMnxY44q38iNKyjO57JdC", "doxlgRsoQnB3jo6mMVx8jBC4xhd",
    "doxlg0WwlSciS5vZe7bkSDnCs4c", "doxlg6dkWviVRpWXHuXDX3ZKLhg", "doxlgXyatalD8YSpKRyG8y3e3yd", "doxlgZOeFWwz2lwR5u1LB8hlUbc",
    # Recent certified cohort.
    "doxlgKug97e8sBpfFtBbMgX4rDg", "doxlgK1yam9yiB9ipnQYXR9Xccb", "doxlgcaL3wj6EsHmX5Js9d4itIc",
    # Current five-game behavior.
    "doxlgIRH18Hpio4HpF2RfFlHSUb", *game_callout_ids, reach_img, *game_table_ids, return_img, "doxlgrdu04YxmLSB0bxpiHnEThd",
    # Current depth snapshot.
    "doxlg0Lz2SFS4Qv0l3I5JB0Fg9b", "doxlgeVyZVVv8vF8zl6nNASXpju", "doxlgqdBXhKuEF4G1BOFQBXK40b", "doxlgzB4zYDwe30pVtAcuj2a0Xb",
    # First-pay cohort requested by comments.
    firstpay_a_ids[0], firstpay_a_ids[1], firstpay_a_ids[2], firstpay_img, *firstpay_a_ids[3:],
    firstpay_b_ids[0], firstpay_b_ids[1], paid_free_img, *firstpay_b_ids[2:],
    # Data availability after findings, not before them.
    "doxlg9sesWX8hLDnG4lxC3nBM0f", "doxlgcgz0UuN6TkvLf7Fn8i2sfd", "doxlgqIgyRQM9iJlAvwy2uHYT4c", *availability_table_ids,
    "doxlgrsaB0XKnptxocFXYZZmtnf", "doxlgSSWYSjI1llQ70hftXbm1df", "doxlgbMGh9e8La2ABPtRYSuiosd",
    *action_ids,
    "doxlghCz3gaS64NkY8BqAeIki6b", *quality_table_ids,
]
update("block_move_after", block_id=DOC_ID, src_block_ids=ordered)

receipt["operations"] = {
    "intro_blocks": intro_ids,
    "game_callout_blocks": game_callout_ids,
    "game_table_blocks": game_table_ids,
    "availability_table_blocks": availability_table_ids,
    "quality_table_blocks": quality_table_ids,
    "firstpay_a_blocks": firstpay_a_ids,
    "firstpay_b_blocks": firstpay_b_ids,
    "action_blocks": action_ids,
    "media_blocks": [reach_img, return_img, firstpay_img, paid_free_img],
    "ordered_blocks": len(ordered),
}

# 8. Readback.
readback = call(["docs", "+fetch", "--doc", DOC_ID, "--scope", "outline", "--max-depth", "3", "--detail", "with-ids", "--format", "json"])
receipt["readback"] = {
    "revision_id": readback["data"]["document"]["revision_id"],
    "outline": readback["data"]["document"]["content"],
}
(ROOT / "feishu_reorg_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "ok", "revision_id": receipt["readback"]["revision_id"], "ordered_blocks": len(ordered)}, ensure_ascii=False))
