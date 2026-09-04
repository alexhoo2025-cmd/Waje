#!/usr/bin/env python3
"""Audit and revise the H5 lightweight-game Feishu report in place.

The report keeps its existing reading order and evidence, but applies the
Waje Dn Day convention, corrects the game-id chart mapping, and makes the
source/grain/coverage of every external data section explicit.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC_ID = "GyZddVm2powgFBxLwH0l18Qzguf"
RECEIPT = ROOT / "full_document_optimization_receipt_2026_09_01.json"


def call(args: list[str]) -> dict:
    env = os.environ.copy()
    env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    result = subprocess.run([CLI, *args, "--as", "user"], cwd=PROJECT, env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-2000:])
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True:
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    return payload


def fetch() -> tuple[str, int]:
    payload = call(["docs", "+fetch", "--doc", DOC_ID, "--detail", "with-ids", "--format", "json"])
    document = payload["data"]["document"]
    return document["content"], document["revision_id"]


def root(xml: str) -> ET.Element:
    return ET.fromstring("<root>" + xml + "</root>")


def text_of(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def normalized(value: str) -> str:
    return "".join(value.split())


def target_id(tag: str, needle: str) -> str:
    xml, _ = fetch()
    for element in root(xml):
        if element.tag == tag and normalized(needle) in normalized(text_of(element)):
            return element.attrib["id"]
    raise KeyError(f"Cannot find <{tag}> containing {needle}")


def image_id(name: str) -> str:
    xml, _ = fetch()
    for element in root(xml):
        if element.tag == "img" and element.attrib.get("name") == name:
            return element.attrib["id"]
    raise KeyError(f"Cannot find image {name}")


def replace(block_id: str, content: str) -> None:
    call(["docs", "+update", "--doc", DOC_ID, "--command", "block_replace", "--block-id", block_id, "--content", content])


def replace_target(tag: str, needle: str, content: str) -> None:
    replace(target_id(tag, needle), content)


def replace_image(old_name: str, new_path: str, caption: str) -> None:
    replace(image_id(old_name), f'<img path="@./{new_path}" width="880" caption="{caption}"/>')


def insert_after(block_id: str, content: str) -> None:
    call(["docs", "+update", "--doc", DOC_ID, "--command", "block_insert_after", "--block-id", block_id, "--content", content])


if RECEIPT.exists():
    raise SystemExit("receipt exists; refusing duplicate full-document update")

# Start with the source horizon and the executive summary.
xml, _ = fetch()
if "数据来源与 Dn Day 口径" not in xml:
    replace_target(
        "p", "数据范围：",
        "<p><b>数据范围与来源：</b>起源新增用户留存覆盖2026年6月16日—8月29日；历史对照统一使用6月16日—8月16日。GA4游戏页面行为覆盖2026年8月21日—27日；外部生产Metabase仅提供近期首充用户的累计游戏快照。所有数据均为脱敏聚合结果。</p>",
    )
    replace_target(
        "callout", "数据截止差异：",
        "<callout emoji=\"⚠️\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>来源截止日不同：</b>起源新增留存已完整至8月29日；GA4页面行为仅完整至8月27日；外部生产Metabase为累计快照。不得把来源缺失、未达到观察日或数据延迟显示为0。</p></callout>",
    )
    replace_target(
        "callout", "轻量化效果：",
        """
<callout emoji="💡" background-color="light-blue" border-color="blue">
  <p><b>起源注册留存：</b>正向信号集中在H5自然和Google；Facebook扩量后未改善，PWA新增扩大97.6%的同时D7 Day下降3.1个百分点。</p>
  <p><b>GA4游戏页观察：</b>Limbo页面触达最大；Keno的D2 Day应用回访最高；Plinko的人均页面浏览较高。旧 GA4 的“D3”实际是D4 Day，不能当作Waje D3 Day解释。</p>
  <p><b>数据边界：</b>页面触达不等于开局；H5加载、可玩、可下注事件未采集。下注和结算服务端事实存在，但尚未与入口、游戏和局次稳定关联。</p>
</callout>
""",
    )

# Insert one reader-facing metric/source contract before any findings.
xml, _ = fetch()
if "数据来源与 Dn Day 口径" not in xml:
    insert_after(
        target_id("callout", "起源注册留存："),
        """
<h1>数据来源与 Dn Day 口径</h1>
<table>
  <thead><tr><th><p>来源</p></th><th><p>用于什么</p></th><th><p>时间范围</p></th><th><p>业务显示与状态</p></th></tr></thead>
  <tbody>
    <tr><td><p>起源 BQ-新增付费用户分析</p></td><td><p>注册批次留存、渠道与阶段对照</p></td><td><p>6/16—8/29</p></td><td><p>D2 Day=次日；D3 Day=第3个自然日；可用</p></td></tr>
    <tr><td><p>GA4 BigQuery（外部平台）</p></td><td><p>首次访问、游戏页触达、应用回访、设备结构</p></td><td><p>8/21—8/27</p></td><td><p>D2 Day可用；旧D0+3结果标为D4 Day；标准D3 Day待重算</p></td></tr>
    <tr><td><p>外部生产 Metabase</p></td><td><p>近期首充用户×游戏的累计局数与下注快照</p></td><td><p>累计快照</p></td><td><p>仅作首充分群观察，不代表首日漏斗</p></td></tr>
    <tr><td><p>Firebase Web 配置（外部平台）</p></td><td><p>核验Web App、Analytics和Performance接入</p></td><td><p>配置快照</p></td><td><p>Web App已注册；未关联Analytics流；无Performance Web指标</p></td></tr>
    <tr><td><p>起源服务端事件</p></td><td><p>GAMESTART、下注、结算与资产事实</p></td><td><p>按报表完整日</p></td><td><p>入口—游戏—局次关联未通过，完整漏斗blocked</p></td></tr>
  </tbody>
</table>
<callout emoji="📌" background-color="light-yellow" border-color="yellow"><p><b>统一留存日：</b>D1 Day为注册/首次访问当天；D2 Day为次日；D3 Day为第3个自然日。`Dn Day = cohort_date + (n - 1) 天`。不同平台原始D1/D3字段未映射前，不得横向比较。</p></callout>
""",
    )

# Origin registration-retention sections: relabel legacy D1 fields as D2 Day.
xml, _ = fetch()
if "历史注册留存：四渠道差异（来源：起源）" not in xml:
    replace_target("h1", "历史留存结构：", "<h1>历史注册留存：四渠道差异（来源：起源）</h1>")
replace_target(
    "table", "渠道/运行形态新增用户D2/ D3 / D7 / D15 / D30",
    """
<table><thead><tr><th><p>渠道/运行形态</p></th><th><p>新增用户</p></th><th><p>D2 Day / D3 Day / D7 Day / D15 Day / D30 Day</p></th></tr></thead>
<tbody>
<tr><td><p>H5自然</p></td><td><p>206,167</p></td><td><p>35.2% / 20.9% / 11.7% / 5.3% / 3.2%</p></td></tr>
<tr><td><p>H5 Facebook</p></td><td><p>365,038</p></td><td><p>27.7% / 15.0% / 6.8% / 3.4% / 2.1%</p></td></tr>
<tr><td><p>H5 Google</p></td><td><p>85,362</p></td><td><p>39.7% / 24.1% / 12.9% / 7.4% / 5.6%</p></td></tr>
<tr><td><p>PWA自然</p></td><td><p>19,121</p></td><td><p>45.3% / 27.6% / 12.0% / 8.6% / 5.8%</p></td></tr>
</tbody></table>
""",
)
replace_target("p", "H5 Google在各留存节点", "<p><b>解读：</b>H5 Google在各留存节点领先标准H5 Facebook；PWA自然在D2 Day、D3 Day保持领先，但到D7 Day与H5自然接近。PWA与标准H5的入口、运行形态和流量结构不同，不能直接下产品定论。</p>")
replace_image("62日窗口留存对比.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/01_起源四渠道DnDay留存对比.png", "来源：起源 BQ-新增付费用户分析；四渠道 Dn Day 注册留存对比")

replace_target("table", "渠道/运行形态 新增变化 次留/ D3 / D7 / D15变化", """
<table><thead><tr><th><p>渠道/运行形态</p></th><th><p>新增变化</p></th><th><p>D2 Day / D3 Day / D7 Day / D15 Day变化</p></th><th><p>综合判断</p></th></tr></thead>
<tbody>
<tr><td><p>H5自然</p></td><td><p>-5.1%</p></td><td><p>+7.6pp / +4.8pp / +3.8pp / +1.7pp</p></td><td><p>留存全面改善</p></td></tr>
<tr><td><p>H5 Facebook</p></td><td><p>+16.6%</p></td><td><p>-1.8pp / -0.1pp / -0.2pp / +0.3pp</p></td><td><p>扩量未改善</p></td></tr>
<tr><td><p>H5 Google</p></td><td><p>-52.3%</p></td><td><p>+3.8pp / +4.0pp / +1.0pp / -0.2pp</p></td><td><p>质量升、规模降</p></td></tr>
<tr><td><p>PWA自然</p></td><td><p>+97.6%</p></td><td><p>-2.4pp / -2.3pp / -3.1pp / -4.4pp</p></td><td><p>扩量伴随留存下降</p></td></tr>
</tbody></table>
""")
replace_target("p", "上线后累计从7月14日开始", "<p><b>来源：起源 BQ-新增付费用户分析。</b>上线后累计从7月14日开始，以8月29日为观察日。D2 Day截至8月28日、D3 Day截至8月26日、D7 Day截至8月22日、D15 Day截至8月14日。</p>")
replace_target("table", "渠道/运行形态 D1 D3 D7 D15", """
<table><thead><tr><th><p>渠道/运行形态</p></th><th><p>D2 Day</p></th><th><p>D3 Day</p></th><th><p>D7 Day</p></th><th><p>D15 Day</p></th></tr></thead>
<tbody>
<tr><td><p>H5自然</p></td><td><p>41.1%</p></td><td><p>24.3%</p></td><td><p>14.1%</p></td><td><p>6.8%</p></td></tr>
<tr><td><p>H5 Facebook</p></td><td><p>26.9%</p></td><td><p>14.8%</p></td><td><p>6.5%</p></td><td><p>3.3%</p></td></tr>
<tr><td><p>H5 Google</p></td><td><p>43.4%</p></td><td><p>26.8%</p></td><td><p>14.0%</p></td><td><p>7.6%</p></td></tr>
<tr><td><p>PWA自然</p></td><td><p>43.2%</p></td><td><p>26.3%</p></td><td><p>11.4%</p></td><td><p>5.9%</p></td></tr>
</tbody></table>
""")
replace_target("callout", "D15观察边界：", "<callout emoji=\"📌\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>D15 Day观察边界：</b>仅纳入7月14日—8月14日注册、截至观察日已完整达到D15 Day统计口径的用户。各渠道上线后样本为17—20个注册批次，少于D2 Day/D3 Day/D7 Day的28日窗口；D15 Day仅用于方向性追踪。</p></callout>")
replace_image("上线前后D1-D15留存变化.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/02_起源上线前后DnDay留存变化.png", "来源：起源 BQ-新增付费用户分析；上线前后 D2 Day / D3 Day / D7 Day 留存变化")

replace_target("h1", "留存衰减：", "<h1>留存衰减：D2 Day 至 D30 Day 的主要流失区间（来源：起源）</h1>")
replace_image("四渠道同批注册用户D1-D30留存曲线.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/03_起源同批注册DnDay留存曲线.png", "来源：起源 BQ-新增付费用户分析；同批注册用户 Dn Day 留存曲线")
replace_target("table", "渠道/运行形态 D1→D3衰减", """
<table><thead><tr><th><p>渠道/运行形态</p></th><th><p>D2 Day→D3 Day衰减</p></th><th><p>D3 Day→D7 Day衰减</p></th><th><p>D7 Day→D15 Day衰减</p></th><th><p>D15 Day→D30 Day衰减</p></th></tr></thead>
<tbody>
<tr><td><p>H5 Facebook</p></td><td><p>46.1%</p></td><td><p>55.0%</p></td><td><p>50.0%</p></td><td><p>36.9%</p></td></tr>
<tr><td><p>H5 Google</p></td><td><p>38.8%</p></td><td><p>46.4%</p></td><td><p>41.3%</p></td><td><p>22.3%</p></td></tr>
<tr><td><p>H5自然</p></td><td><p>40.3%</p></td><td><p>42.5%</p></td><td><p>51.7%</p></td><td><p>30.9%</p></td></tr>
<tr><td><p>PWA自然</p></td><td><p>39.9%</p></td><td><p>55.8%</p></td><td><p>29.9%</p></td><td><p>39.3%</p></td></tr>
</tbody></table>
""")
replace_target("p", "Facebook和PWA自然的最大短板", "<p><b>解读：</b>Facebook和PWA自然的最大短板在D3 Day→D7 Day；H5自然在D7 Day后衰减较快。入口、首局和复玩查询应围绕这些阶段优先展开。</p>")
replace_image("四渠道分阶段留存衰减率.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/04_起源DnDay留存衰减.png", "来源：起源 BQ-新增付费用户分析；四渠道 Dn Day 分阶段留存衰减")

replace_target("table", "阶段 日期窗口 新增用户 次留/ D3 / D7 / D15", """
<table><thead><tr><th><p>阶段</p></th><th><p>日期窗口</p></th><th><p>新增用户</p></th><th><p>D2 Day / D3 Day / D7 Day / D15 Day</p></th></tr></thead>
<tbody>
<tr><td><p>上线前基线</p></td><td><p>6/16—7/13</p></td><td><p>306,491</p></td><td><p>31.2% / 17.6% / 8.9% / 4.5%</p></td></tr>
<tr><td><p>Limbo上线/恢复</p></td><td><p>7/14—7/22</p></td><td><p>98,577</p></td><td><p>29.6% / 17.1% / 8.5% / 4.6%</p></td></tr>
<tr><td><p>H5 2.1.14 / Keno</p></td><td><p>7/23—7/28</p></td><td><p>56,988</p></td><td><p>31.6% / 17.4% / 9.4% / 4.7%</p></td></tr>
<tr><td><p>Color Dice</p></td><td><p>7/29—8/05</p></td><td><p>89,639</p></td><td><p>33.7% / 20.5% / 10.2% / 5.1%</p></td></tr>
<tr><td><p>Opera埋点期</p></td><td><p>8/06—8/10</p></td><td><p>60,270</p></td><td><p>34.3% / 19.8% / 9.7% / 5.0%</p></td></tr>
<tr><td><p>当前期</p></td><td><p>8/11—8/16</p></td><td><p>63,736</p></td><td><p>35.8% / 20.7% / 11.1% / N/A</p></td></tr>
</tbody></table>
""")
replace_image("轻量化更新节点D3留存折线.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/05_起源轻量化节点D3Day留存.png", "来源：起源 BQ-新增付费用户分析 + 飞书更新记录；四渠道 D3 Day 留存变化")

# Latest cohort and the GA4 sections.
replace_target("table", "8月26日注册批次 新增 D1 D3 D7 D15", """
<table><thead><tr><th><p>8月26日注册批次</p></th><th><p>新增</p></th><th><p>D2 Day</p></th><th><p>D3 Day</p></th><th><p>D7 Day</p></th><th><p>D15 Day</p></th></tr></thead>
<tbody>
<tr><td><p>H5自然</p></td><td><p>3,284</p></td><td><p>48.7%</p></td><td><p>27.6%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
<tr><td><p>H5 Facebook</p></td><td><p>4,818</p></td><td><p>27.0%</p></td><td><p>18.9%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
<tr><td><p>H5 Google</p></td><td><p>1,111</p></td><td><p>42.7%</p></td><td><p>21.4%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
<tr><td><p>PWA/PWW</p></td><td><p>595</p></td><td><p>45.2%</p></td><td><p>26.9%</p></td><td><p>N/A</p></td><td><p>N/A</p></td></tr>
</tbody></table>
""")
replace_target("h1", "近期五款游戏：", "<h1>近期五款游戏：页面触达与短期回访（来源：GA4 BigQuery）</h1>")
replace_target("callout", "短期观察：", "<callout emoji=\"💡\" background-color=\"light-blue\" border-color=\"blue\"><p><b>短期观察：</b>GA4在8月21日—27日显示，Limbo页面触达最大；Keno的D2 Day应用回访最高；Plinko人均页面浏览较高。旧查询的D0+3结果仅作为D4 Day展示，标准D3 Day待重算。</p></callout>")
replace_image("02_新访客游戏页面触达.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/02_新访客游戏页面触达_DnDay修正.png", "来源：GA4 BigQuery；近期五款游戏页面触达，Limbo=9008，Keno=9010")
replace_target("table", "游戏 Game ID 进入游戏页的新访客", """
<table><thead><tr><th><p>游戏</p></th><th><p>Game ID</p></th><th><p>新访客</p></th><th><p>人均页面浏览</p></th><th><p>D2 Day应用回访</p></th><th><p>D4 Day应用回访（旧GA4+3日）</p></th></tr></thead>
<tbody>
<tr><td><p>Limbo</p></td><td><p>9008</p></td><td><p>647</p></td><td><p>5.16</p></td><td><p>29.0%（n=544）</p></td><td><p>13.9%（n=316）</p></td></tr>
<tr><td><p>Color Dice</p></td><td><p>9003</p></td><td><p>413</p></td><td><p>4.01</p></td><td><p>25.2%（n=325）</p></td><td><p>15.7%（n=102）</p></td></tr>
<tr><td><p>Plinko</p></td><td><p>9016</p></td><td><p>365</p></td><td><p>6.27</p></td><td><p>31.3%（n=310）</p></td><td><p>17.3%（n=196）</p></td></tr>
<tr><td><p>Keno</p></td><td><p>9010</p></td><td><p>270</p></td><td><p>5.53</p></td><td><p>36.4%（n=231）</p></td><td><p>13.6%（n=140）</p></td></tr>
<tr><td><p>Hilo</p></td><td><p>9011</p></td><td><p>184</p></td><td><p>4.52</p></td><td><p>34.4%（n=151）</p></td><td><p>16.7%（n=78）</p></td></tr>
</tbody></table>
""")
replace_image("03_游戏页新访客D1D3回访.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/03_游戏页新访客D2D4回访.png", "来源：GA4 BigQuery；D2 Day应用回访与旧查询 D4 Day应用回访")
replace_target("p", "观察边界：D1仅纳入", "<p><b>GA4口径：</b>新访客为首次访问当天进入对应游戏页的去重用户；D2 Day仅纳入8月26日及以前首次访问，D4 Day仅纳入8月24日及以前首次访问。标准D3 Day（首次访问后第2天）待按新SQL重算；应用回访不等同回到同一游戏或形成下注。</p>")

replace_target("p", "分组：轻量化4款为CoinFlip", "<p><b>来源与分组：</b>来源为GA4 BigQuery 8月21日—27日的游戏页聚合。轻量化4款为CoinFlip、Limbo、Keno、ColorDice；非轻量化5款为Whot、Hilo、Plinko、Tower、Bottle spin。D2 Day/D4 Day分母只纳入达到相应观察日的新访客。</p>")
replace_target("table", "分组 游戏 / ID 新访客 D1应用回访", """
<table><thead><tr><th><p>分组</p></th><th><p>游戏 / ID</p></th><th><p>新访客</p></th><th><p>D2 Day应用回访</p></th><th><p>D4 Day应用回访（旧GA4+3日）</p></th><th><p>观察状态</p></th></tr></thead>
<tbody>
<tr><td><p>非轻量化</p></td><td><p>Whot / 6001</p></td><td><p>1,109</p></td><td><p>30.6%（n=935）</p></td><td><p>14.0%（n=529）</p></td><td><p>可观察</p></td></tr>
<tr><td><p>轻量化</p></td><td><p>Limbo / 9008</p></td><td><p>647</p></td><td><p>29.0%（n=544）</p></td><td><p>13.9%（n=316）</p></td><td><p>可观察</p></td></tr>
<tr><td><p>轻量化</p></td><td><p>CoinFlip / 9001</p></td><td><p>425</p></td><td><p>31.6%（n=351）</p></td><td><p>17.6%（n=204）</p></td><td><p>可观察</p></td></tr>
<tr><td><p>轻量化</p></td><td><p>Keno / 9010</p></td><td><p>270</p></td><td><p>36.4%（n=231）</p></td><td><p>13.6%（n=140）</p></td><td><p>可观察</p></td></tr>
<tr><td><p>轻量化</p></td><td><p>ColorDice / 9003</p></td><td><p>413</p></td><td><p>25.2%（n=325）</p></td><td><p>15.7%（n=102）</p></td><td><p>可观察</p></td></tr>
<tr><td><p>非轻量化</p></td><td><p>Hilo / 9011</p></td><td><p>184</p></td><td><p>34.4%（n=151）</p></td><td><p>16.7%（n=78）</p></td><td><p>小样本</p></td></tr>
<tr><td><p>非轻量化</p></td><td><p>Plinko / 9016</p></td><td><p>365</p></td><td><p>31.3%（n=310）</p></td><td><p>17.3%（n=196）</p></td><td><p>可观察</p></td></tr>
<tr><td><p>非轻量化</p></td><td><p>Tower / 9013</p></td><td><p>122</p></td><td><p>38.1%（n=84）</p></td><td><p>N/A</p></td><td><p>未达到D4 Day统计口径</p></td></tr>
<tr><td><p>非轻量化</p></td><td><p>Bottle spin / 2003</p></td><td><p>709</p></td><td><p>31.4%（n=601）</p></td><td><p>11.0%（n=353）</p></td><td><p>可观察</p></td></tr>
</tbody></table>
""")
replace_image("07_产品TopGames九款_D1D3回访.png", "analysis/h5_lightgame_report_reorg_2026_08_31/charts/07_产品TopGames九款_D2D4回访.png", "来源：GA4 BigQuery；Top Games九款 D2 Day / D4 Day 应用回访")
replace_target("p", "判断：Top Games是产品配置分组", "<p><b>判断：</b>Top Games是产品配置分组，不是流量排名。Whot触达最大，Bottle spin第二；Limbo页面触达高于Keno。D2 Day/D4 Day为应用回访，不代表同游戏复玩；当前不能据此判断轻量化整体优于或弱于其他游戏。</p>")

replace_target("h1", "游戏深度：", "<h1>游戏深度：近期首充用户累计快照（来源：外部生产 Metabase）</h1>")
replace_target("p", "该数据来自外部生产Metabase", "<p><b>来源与口径：</b>外部生产Metabase的用户×游戏聚合快照，统计近期首充用户的累计局数与下注。`update_at`不是首次开局时间，因此该表不代表全体新增用户首日漏斗，也不能判断付费前后顺序。</p>")
replace_target("p", "首充日记为T0", "<p><b>来源与口径：</b>起源服务端用户主表与订单事实的首充日期聚合。T0为首次成功现金充值日；当前只有日期粒度，能判断首充当日及7天内是否有游戏记录，不能判断同一天内“先付费还是先开局”。</p>")
replace_target("p", "跨来源共同完整日", "<p><b>来源与状态：</b>GA4页面行为完整至8月27日，起源新增留存完整至8月29日，服务端游戏事件按各报表完整日提供。H5加载与可玩事件缺失；下注、结算服务端事实存在，但入口、游戏和局次关联未通过。缺失环节不计为用户流失。</p>")
replace_target("h1", "设备与体验：", "<h1>设备与体验：外部 GA4 行为结构与 Firebase 配置审计</h1>")
replace_target("p", "GA4设备基线显示", "<p><b>来源：GA4 BigQuery（外部平台）。</b>移动端事件占97.94%，Android占73.85%；Chrome与Safari合计96.68%；Tecno、Infinix、itel合计占移动端事件35.38%。这些指标只描述行为量，不能判断加载速度或失败率。</p>")
replace_target("callout", "Firebase边界：", "<callout emoji=\"📌\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>Firebase配置审计（外部平台）：</b>H5 Web App已注册，但未关联Google Analytics数据流；Firebase Performance没有H5 Web指标。Firebase在本报告中只用于接入状态核验，不作为页面触达、留存、下注或结算数据来源。</p></callout>")
replace_target("ol", "P0｜优先修复Facebook承接", """
<ol>
  <li><b>P0｜修复Facebook承接。</b>使用同媒体计划、同入口、同设备条件复测注册→首充→大厅→游戏页→7天内任意游戏记录。</li>
  <li><b>P0｜补齐H5前端链路。</b>上报入口曝光/点击、GAME_LOAD、GAME_READY、BET_READY、错误、重试和恢复；事件带game_id、入口、会话、H5版本和配置版本。</li>
  <li><b>P0｜重算GA4 D3 Day。</b>恢复只读BigQuery认证后，以首次访问后第2天重算D3 Day；替换当前仅作过渡展示的D4 Day结果。</li>
  <li><b>P0｜完成服务端事件对账。</b>建立注册日×游戏×渠道的首日进入、有效下注、首局结算、局数分层及Dn Day复玩；GAMEEND异常率降至1%以下前不形成完成漏斗。</li>
  <li><b>P1｜持续观察新游戏。</b>Hilo、Plinko、Tower按相同上线年龄比较；小样本或未达到Dn Day统计口径时不下结论。</li>
</ol>
""")

# Source appendix replaces a mixed, abbreviated status table.
replace_target("table", "数据项 状态 说明", """
<table><thead><tr><th><p>数据来源</p></th><th><p>统计内容</p></th><th><p>截止日 / 窗口</p></th><th><p>状态与限制</p></th></tr></thead>
<tbody>
<tr><td><p>起源 BQ-新增付费用户分析</p></td><td><p>注册批次 Dn Day 留存、渠道、阶段</p></td><td><p>完整至8/29；历史对照6/16—8/16</p></td><td><p>可用；次留映射D2 Day、3日留映射D3 Day</p></td></tr>
<tr><td><p>GA4 BigQuery（外部）</p></td><td><p>首次访问、游戏页触达、应用回访、设备</p></td><td><p>8/21—8/27</p></td><td><p>D2 Day可用；标准D3 Day待重算；user_id覆盖不足以做用户级关联</p></td></tr>
<tr><td><p>Firebase Web 配置（外部）</p></td><td><p>Web App、Analytics、Performance接入核验</p></td><td><p>配置快照</p></td><td><p>未提供H5业务指标或Performance Web数据</p></td></tr>
<tr><td><p>外部生产 Metabase</p></td><td><p>首充用户×游戏累计局数、下注</p></td><td><p>累计快照</p></td><td><p>仅首充分群；不是首次开局时序</p></td></tr>
<tr><td><p>起源服务端事件</p></td><td><p>GAMESTART、下注、结算、资产</p></td><td><p>按报表完整日</p></td><td><p>入口—游戏—局次未关联；完整漏斗blocked</p></td></tr>
</tbody></table>
""")

xml, revision = fetch()
required = [
    "数据来源与 Dn Day 口径",
    "D2 Day=次日",
    "D4 Day",
    "Limbo页面触达高于Keno",
    "Firebase配置审计",
    "标准D3 Day待重算",
    "外部生产 Metabase",
]
missing = [item for item in required if item not in xml]
if missing:
    raise RuntimeError(f"Readback missing: {missing}")
RECEIPT.write_text(json.dumps({
    "status": "ok",
    "revision_id": revision,
    "sources": ["Origin BQ-新增付费用户分析", "GA4 BigQuery", "Firebase Web configuration", "external production Metabase", "Origin server events"],
    "dn_day_rule": "D1 Day=cohort day; D2 Day=cohort+1; D3 Day=cohort+2",
    "ga4_legacy_rule": "existing D0+3 result is D4 Day and not D3 Day",
    "required": required,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "ok", "revision_id": revision}, ensure_ascii=False))
