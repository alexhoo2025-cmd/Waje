#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
D = json.loads((ROOT / "analysis-results.json").read_text())


def esc(v): return html.escape(str(v), quote=True)
def pct(v, d=2): return "N/A" if v is None else f"{v*100:.{d}f}%"
def pp(v, d=2): return "N/A" if v is None else f"{v:+.{d}f}pp"
def amount(v):
    if v is None: return "N/A"
    if abs(v) >= 100_000_000: return f"{v/100_000_000:.2f}亿"
    if abs(v) >= 10_000: return f"{v/10_000:.2f}万"
    return f"{v:,.0f}"
def chg(v): return "N/A" if v is None else f"{v:+.2%}"

def movement_bg(value, strong_threshold):
    if value is None: return "light-gray"
    if value >= strong_threshold: return "light-green"
    if value >= 0: return "light-blue"
    if value <= -strong_threshold: return "light-red"
    return "light-orange"

def movement_cell(value, display, strong_threshold):
    return f'<td background-color="{movement_bg(value, strong_threshold)}" vertical-align="middle"><p><b>{esc(display)}</b></p></td>'

def highlight_cell(display, background="light-blue"):
    return f'<td background-color="{background}" vertical-align="middle"><p><b>{esc(display)}</b></p></td>'

def visual_bar(value, values, segments=8):
    low, high = min(values), max(values)
    position = 0 if high == low else (value-low)/(high-low)
    filled = 1 + round(position*(segments-1))
    return "█"*filled, "░"*(segments-filled), position

def level_cell(value, values, display):
    filled, empty, position = visual_bar(value, values)
    color = "light-green" if position >= .75 else "light-blue" if position >= .5 else "light-yellow" if position >= .25 else "light-red"
    return f'<td background-color="{color}" vertical-align="middle"><p><span text-color="blue">{filled}</span><span text-color="gray">{empty}</span> <b>{esc(display)}</b></p></td>'


def table(headers, rows, widths=None):
    cols = "" if not widths else "<colgroup>" + "".join(f'<col width="{w}"/>' for w in widths) + "</colgroup>"
    head = "<thead><tr>" + "".join(f'<th background-color="medium-gray"><p><b>{esc(x)}</b></p></th>' for x in headers) + "</tr></thead>"
    def render_cell(x):
        return x if isinstance(x,str) and x.lstrip().startswith("<td") else f'<td vertical-align="middle"><p>{x}</p></td>'
    body = "<tbody>" + "".join("<tr>" + "".join(render_cell(x) for x in row) + "</tr>" for row in rows) + "</tbody>"
    return "<table>" + cols + head + body + "</table>"


def img(key, caption):
    return f'<img path="@./{esc(D["charts"][key])}" caption="{esc(caption)}" name="{esc(caption)}.png"/>'


tc=D["tc"]; gp=D["game_overall"]; prev=tc["previous"]; curr=tc["current"]
coverage_delta=(gp["current"]["expected_coverage"]-gp["previous"]["expected_coverage"])*100
tc_direction = "上升" if tc["change_pp"] >= 0 else "下降"
bet_direction = "增长" if gp["bet_change_pct"] >= 0 else "下降"
rtp_relative_change = gp["current"]["actual_rtp"] / gp["previous"]["actual_rtp"] - 1
rtp_direction = "上升" if rtp_relative_change >= 0 else "下降"

summary = [
    f'<li><b>TC小幅下降，但资金规模增长。</b>本周TC为<b><span text-color="blue">{pct(curr["tc"])}</span></b>，较上周<span text-color="orange">{tc_direction}{abs(tc["change_pp"]):.2f}个百分点</span>；成功充值由{amount(prev["recharge"])}提升至{amount(curr["recharge"])}，<b><span text-color="green">增长{pct(tc["recharge_change_pct"])}</span></b>；成功提现由{amount(prev["withdraw"])}提升至{amount(curr["withdraw"])}，<b><span text-color="green">增长{pct(tc["withdraw_change_pct"])}</span></b>。</li>',
    f'<li><b>游戏规模增长，整体RTP基本稳定。</b>完全下注额由{amount(gp["previous"]["complete_bet"])}提升至{amount(gp["current"]["complete_bet"])}，<b><span text-color="green">{bet_direction}{pct(abs(gp["bet_change_pct"]))}</span></b>；实际RTP由{pct(gp["previous"]["actual_rtp"],3)}降至{pct(gp["current"]["actual_rtp"],3)}，<span text-color="blue">相对{rtp_direction}{pct(abs(rtp_relative_change),3)}</span>。</li>',
    '<li><b>下注增量高度集中在Tada和Fish。</b>Tada贡献本周下注增量的<b><span text-color="green">55.61%</span></b>，Fish贡献<b><span text-color="green">28.87%</span></b>，两者合计84.48%；BottleSpin减少1.21亿，抵消总增量的8.68%。</li>',
    '<li><b>重点复核EasyWin、Tower和Hilo。</b>EasyWin本周RTP 115.75%，Tower 100.61%，Hilo 90.24%；三者下注规模和偏离方向不同，应分别核对最终派奖、有效局数、配置版本和Bonus。</li>',
]

def metric_cell(label, value, note, colspan=None):
    span = "" if colspan is None else f' colspan="{colspan}"'
    return (
        f'<td background-color="light-blue" vertical-align="middle"{span}>'
        f'<p><b>{esc(label)}</b></p>'
        f'<p><b><span text-color="blue">{esc(value)}</span></b></p>'
        f'<p>{esc(note)}</p></td>'
    )

cards_module = (
    '<table><colgroup><col width="190"/><col width="190"/><col width="190"/><col width="190"/></colgroup><tbody><tr>'
    + metric_cell("本周TC", pct(curr["tc"]), f"较上周{tc_direction}{abs(tc['change_pp']):.2f}个百分点")
    + metric_cell("成功充值", amount(curr["recharge"]), f"增长{pct(tc['recharge_change_pct'])}")
    + metric_cell("成功提现", amount(curr["withdraw"]), f"增长{pct(tc['withdraw_change_pct'])}")
    + metric_cell("完全下注额", amount(gp["current"]["complete_bet"]), f"{bet_direction}{pct(abs(gp['bet_change_pct']))}")
    + '</tr><tr>'
    + metric_cell("实际RTP", pct(gp["current"]["actual_rtp"]), f"相对{rtp_direction}{pct(abs(rtp_relative_change),3)}", colspan=2)
    + metric_cell("可比范围RTP差异", f'{gp["current"]["rtp_gap_pp"]:+.2f}个百分点', "实际RTP减预期RTP", colspan=2)
    + '</tr></tbody></table>'
)

tc_week_rows=[
    ["成功充值",esc(amount(prev["recharge"])),highlight_cell(amount(curr["recharge"])),movement_cell(tc["recharge_change_pct"],chg(tc["recharge_change_pct"]),.05)],
    ["成功提现",esc(amount(prev["withdraw"])),highlight_cell(amount(curr["withdraw"])),movement_cell(tc["withdraw_change_pct"],chg(tc["withdraw_change_pct"]),.05)],
    ["TC",esc(pct(prev["tc"])),highlight_cell(pct(curr["tc"])),movement_cell(tc["change_pp"],pp(tc["change_pp"]),1)],
]
daily_values = [r for r in tc["daily"] if "2026-08-26" <= r["date"] <= "2026-09-07"]

def visual_cell(value, values, display):
    low, high = min(values), max(values)
    position = 0 if high == low else (value - low) / (high - low)
    filled = 1 + round(position * 7)
    bar = "█" * filled
    remainder = "░" * (8 - filled)
    if position >= 0.75:
        color = "light-green"
    elif position >= 0.50:
        color = "light-blue"
    elif position >= 0.25:
        color = "light-yellow"
    else:
        color = "light-red"
    return f'<td background-color="{color}" vertical-align="middle"><p><span text-color="blue">{bar}</span><span text-color="gray">{remainder}</span> {esc(display)}</p></td>'

recharge_values = [r["recharge"] for r in daily_values]
withdraw_values = [r["withdraw"] for r in daily_values]
tc_values = [r["tc"] for r in daily_values]
daily_body = []
for r in daily_values:
    daily_body.append(
        '<tr>'
        f'<td vertical-align="middle"><p>{esc(r["date"])}</p></td>'
        + visual_cell(r["recharge"], recharge_values, amount(r["recharge"]))
        + visual_cell(r["withdraw"], withdraw_values, amount(r["withdraw"]))
        + visual_cell(r["tc"], tc_values, pct(r["tc"]))
        + '</tr>'
    )
daily_table = (
    '<p><span text-color="gray">展示说明：条形长度按各指标在8月26日—9月7日内的最小值至最大值归一化；'
    '色阶为绿色（高位）、蓝色（中高位）、黄色（中低位）、红色（低位），仅用于观察区间内相对变化。</span></p>'
    '<table><colgroup><col width="155"/><col width="230"/><col width="230"/><col width="210"/></colgroup>'
    '<thead><tr><th background-color="medium-gray"><p><b>业务日</b></p></th>'
    '<th background-color="medium-gray"><p><b>成功充值</b></p></th>'
    '<th background-color="medium-gray"><p><b>成功提现</b></p></th>'
    '<th background-color="medium-gray"><p><b>TC</b></p></th></tr></thead><tbody>'
    + ''.join(daily_body)
    + '</tbody></table>'
)
channel_tc_values=[r["tc_curr"] for r in tc["channels"]]
channel_share_values=[r.get("recharge_share_curr",r["recharge_curr"]/curr["recharge"]) for r in tc["channels"]]
channel_rows=[]
for r in tc["channels"]:
    recharge_change=r.get("recharge_change_pct",r["recharge_curr"]/r["recharge_prev"]-1)
    recharge_share=r.get("recharge_share_curr",r["recharge_curr"]/curr["recharge"])
    channel_rows.append([
        esc(r["channel"]),esc(pct(r["tc_prev"])),level_cell(r["tc_curr"],channel_tc_values,pct(r["tc_curr"])),
        movement_cell(r["tc_change_pp"],pp(r["tc_change_pp"]),2),esc(amount(r["recharge_prev"])),esc(amount(r["recharge_curr"])),
        movement_cell(recharge_change,chg(recharge_change),.15),level_cell(recharge_share,channel_share_values,pct(recharge_share)),
    ])

game_rows=[]
for r in D["game_comparison"][:15]:
    game_rows.append([esc(r["game"]),esc(amount(r["complete_bet_prev"])),esc(amount(r["complete_bet_curr"])),movement_cell(r["bet_change_pct"],chg(r["bet_change_pct"]),.10),esc(pct(r["actual_rtp_prev"])),esc(pct(r["actual_rtp_curr"])),movement_cell(r["rtp_change_pp"],pp(r["rtp_change_pp"]),1),movement_cell(r["rtp_gap_curr_pp"],pp(r["rtp_gap_curr_pp"]),1),esc(f'{r["rank_prev"]} → {r["rank_curr"]}')])

new_rows=[]
for name,item in D["new_games"].items():
    w=next(r for r in D["game_comparison"] if r["game"]==name)
    new_rows.append([esc(name),esc(item["launch"]),esc(amount(w["complete_bet_curr"])),movement_cell(w["bet_change_pct"],chg(w["bet_change_pct"]),.20),esc(pct(w["actual_rtp_curr"])),movement_cell(w["rtp_gap_curr_pp"],pp(w["rtp_gap_curr_pp"]),3),esc(pct(item["actual_rtp"])),movement_cell(item["rtp_gap_pp"],pp(item["rtp_gap_pp"]),3)])

life_rows=[]
for r in D["new_game_lifecycle"]:
    life_rows.append([esc(r["game"]),esc(r["lifecycle"]),esc(amount(r["complete_bet"])),movement_cell(r["rtp_gap_pp"],pct(r["actual_rtp"]),3),esc(pct(r["expected_rtp"])),movement_cell(r["rtp_gap_pp"],pp(r["rtp_gap_pp"]),3)])

fixed_actions={
    "EasyWin":"核对最终派奖、有效局数和取消/退款；高回报在两周均持续，但下注规模较小。",
    "Tower":"复核层数、Cash Out、封顶触发和倍率分布；本周下注下降但RTP高于预期。",
    "Hilo":"复核猜测、Skip、Cash Out与赔率分布；本周RTP明显下降。",
    "Blackjack":"保持小样本观察；当前下注不足以支持系统性结论。",
    "JacksBetterRb":"保持小样本观察并核对最终结算；不升级为全盘风险。",
}
anomaly_rows=[]
for r in D["anomalies"]:
    w=next(x for x in D["game_comparison"] if x["game"]==r["game"])
    anomaly_rows.append([esc(r["game"]),esc(amount(r["complete_bet"])),movement_cell(w["bet_change_pct"],chg(w["bet_change_pct"]),.20),movement_cell(r["rtp_gap_pp"],pct(r["actual_rtp"]),3),esc(pct(r["expected_rtp"])),movement_cell(r["rtp_gap_pp"],pp(r["rtp_gap_pp"]),3),esc(fixed_actions.get(r["game"],"继续观察并核对最终结算。"))])

xml=[
    '<title>Waje 全产品TC与新上线游戏RTP周度对比分析 V3｜截至2026年9月7日</title>',
    '<h1 seq="auto">汇总结论（Executive Summary）</h1><callout background-color="light-blue" border-color="blue"><ol>'+''.join(summary)+'</ol></callout>',
    cards_module,
    f'<h1 seq="auto">TC小幅下降，充值与提现规模同步增长</h1><p><b>TC下降来自提现增速略低于充值增速。</b>成功充值由{amount(prev["recharge"])}提升至{amount(curr["recharge"])}，<b><span text-color="green">增长{pct(tc["recharge_change_pct"])}</span></b>；成功提现由{amount(prev["withdraw"])}提升至{amount(curr["withdraw"])}，<b><span text-color="green">增长{pct(tc["withdraw_change_pct"])}</span></b>，带动加权TC<span text-color="orange">下降0.37个百分点</span>。TC仍受历史余额、跨日结算和提现节奏影响，本节只解释资金口径变化。</p>',
    table(["指标","8月25日—31日","9月1日—7日","周变化"],tc_week_rows,[160,190,190,150]),
    '<p><b>日趋势显示波动仍明显。</b>8月30日TC为74.27%，9月7日回升至79.78%；单日波动不应替代两个7天窗口的加权结果。</p>',img("tc_trend","全产品TC日趋势（8月26日—9月7日）"),
    daily_table,
    '<h1 seq="auto">渠道变化分化，PAWAJEH5和iOS下降更明显</h1><p><b>资金增长由头部渠道与数个H5/包体标签共同贡献。</b>WajeSpecial、PAWAJEBETH5、PAWAJEPALM2和PAPAWAJEH5GA合计贡献本周充值增量的<span text-color="blue"><b>70.35%</b></span>；PAWAJEH5和PAWAJEIOS的TC分别<span text-color="red">下降4.07和2.63个百分点</span>，PAPAWAJEH5GA<span text-color="green">上升4.76个百分点</span>。渠道为注册渠道聚合，不等同广告事件归因。</p>',img("channel_delta","Top 7渠道TC周变化"),
    '<p><span text-color="gray">表格说明：本周TC与充值占比使用列内数值条和高—低色阶；变化列正向为绿/蓝，负向为橙/红。</span></p>'+table(["渠道","上周TC","本周TC","TC变化","上周充值","本周充值","充值环比","本周充值占比"],channel_rows,[175,90,155,105,130,130,105,165]),
    f'<h1 seq="auto">游戏下注增长8.43%，增量主要来自Tada和Fish</h1><p><b>本周下注增加13.95亿，其中84.48%由Tada和Fish贡献。</b>Tada下注增加<span text-color="green"><b>7.76亿</b></span>，贡献总增量的55.61%；Fish增加<span text-color="green"><b>4.03亿</b></span>，贡献28.87%；BottleSpin减少<span text-color="red"><b>1.21亿</b></span>，抵消总增量的8.68%。实际RTP由{pct(gp["previous"]["actual_rtp"],3)}降至{pct(gp["current"]["actual_rtp"],3)}，相对{rtp_direction}{pct(abs(rtp_relative_change),3)}。资金侧H5/包体标签同步增长，但现有游戏下注表不含渠道/包体字段、渠道表不含游戏字段，不能把充值变化直接归因为某款游戏的下注来源。</p>',
    img("game_scatter","本周游戏RTP偏离与下注规模"),
    '<p><b>头部份额迁移集中在少数游戏。</b>Fish下注<span text-color="green">增长18.52%</span>、份额增加1.22个百分点；BottleSpin下注<span text-color="red">下降14.22%</span>、份额下降1.08个百分点；Tada仍排名第1，占本周下注50.69%。</p>',img("share_delta","头部游戏下注占比周变化"),
    '<p><span text-color="gray">色阶说明：下注和RTP正向变化使用绿/蓝，负向变化使用橙/红；颜色仅表示方向与幅度，不等同业务好坏。</span></p>'+table(["游戏","上周下注","本周下注","下注变化","上周RTP","本周RTP","RTP变化","本周实际-预期","排名"],game_rows,[140,125,125,110,100,100,105,125,80]),
    '<h1 seq="auto">Plinko规模增长，Tower和Hilo回报方向相反</h1><p><b>三款新游戏的规模与回报方向明显分化。</b>Plinko本周下注<span text-color="green"><b>增长85.40%</b></span>，实际RTP 97.39%；Tower下注<span text-color="red"><b>下降33.52%</b></span>，实际RTP 100.61%、较预期高3.78个百分点；Hilo下注下降8.37%，实际RTP 90.24%、较预期低6.28个百分点。三款仍处于上线后早期观察。</p>',
    table(["游戏","上线日","本周下注","周变化","本周RTP","本周实际-预期","上线后RTP","上线后实际-预期"],new_rows,[110,115,120,95,95,120,100,125]),
    img("new_game_daily","新游戏逐日实际与预期RTP"),
    '<p><b>生命周期偏离并非同向。</b>Hilo在生命周期1—3<span text-color="red">均低于预期</span>；Tower在生命周期2—4<span text-color="green">高于预期</span>；Plinko生命周期2—3高于预期。需要玩法参数与最终结算数据才能判断机制原因。</p>',img("lifecycle","新游戏生命周期RTP偏离"),
    '<p><span text-color="gray">生命周期色阶：实际高于预期为绿/蓝，低于预期为橙/红；绝对偏离达到3个百分点使用强色阶。</span></p>'+table(["游戏","生命周期","完全下注额","实际RTP","预期RTP","差异"],life_rows,[110,100,145,115,105,115]),
    '<h1 seq="auto">重点偏离游戏需按规模和机制分层复核</h1><p><b>优先级应同时考虑偏离幅度与下注规模。</b>EasyWin两周持续高回报，Tower下注规模更大且实际RTP超过100%；Hilo与Blackjack为明显负向偏离，但规模较小。以下均为观察信号，不是结算故障结论。</p>',img("focus_daily","重点游戏逐日RTP观察"),
    table(["游戏","本周下注","周变化","实际RTP","预期RTP","差异","处理建议"],anomaly_rows,[110,115,90,95,95,95,300]),
    '<h1 seq="auto">下一步：先核对高影响游戏，再补齐结算事实</h1><ol><li><b>P0：</b>优先复核EasyWin、Tower和Hilo的有效局数、最终派奖、取消/退款、免费注/Bonus和配置版本。</li><li><b>P1：</b>确认Fish份额上升与BottleSpin份额下降是否来自入口、版本、渠道或用户结构变化。</li><li><b>P1：</b>持续跟踪PAWAJEH5与PAWAJEIOS资金结构，避免把注册渠道变化解释为广告效果。</li></ol>',
    '<h1 seq="auto">仍需回答的问题</h1><ul><li>EasyWin高回报是否由少量大额派奖主导？</li><li>Tower高RTP是否集中在特定层数、Cash Out或封顶触发？</li><li>Fish下注份额增加是否来自流量入口变化，还是玩家参与深度上升？</li></ul>',
    '<h1 seq="auto">口径与边界</h1><callout background-color="light-yellow" border-color="yellow"><p><b>比较口径：</b>本周为9月1日—7日，上周为8月25日—31日，均为7个完整自然日，时区Asia/Hong_Kong。正文日趋势为8月26日—9月7日。</p><p><b>指标口径：</b>TC=成功提现÷成功现金充值；实际RTP=1−完全实际盈利÷完全下注额。预期RTP仅在预期值有效的下注范围内计算。</p><p><b>限制：</b>当前缺少有效局数、最终结算状态、取消/退款、Bonus、配置版本和用户级大额派奖分布；RTP与TC的同步变化不代表因果关系。</p></callout>',
]
content="\n\n".join(xml)+"\n"
draft=PROJECT/sys.argv[1]
draft.write_text(content)
(ROOT/"report.xml").write_text(content)

md=f"""# Waje 全产品TC与新上线游戏RTP周度对比分析 V3｜截至2026年9月7日

## 汇总结论

- 本周TC为{pct(curr['tc'])}，较上周{tc_direction}{abs(tc['change_pp']):.2f}个百分点；成功充值由{amount(prev['recharge'])}提升至{amount(curr['recharge'])}，增长{pct(tc['recharge_change_pct'])}；成功提现由{amount(prev['withdraw'])}提升至{amount(curr['withdraw'])}，增长{pct(tc['withdraw_change_pct'])}。
- 游戏完全下注额由{amount(gp['previous']['complete_bet'])}提升至{amount(gp['current']['complete_bet'])}，{bet_direction}{pct(abs(gp['bet_change_pct']))}；实际RTP由{pct(gp['previous']['actual_rtp'],3)}降至{pct(gp['current']['actual_rtp'],3)}，相对{rtp_direction}{pct(abs(rtp_relative_change),3)}。
- 下注增量主要来自Tada（55.61%）和Fish（28.87%），两者合计贡献84.48%；BottleSpin减少1.21亿。
- 优先复核EasyWin、Tower和Hilo；偏离均为观察信号，不是结算故障结论。

完整正文、可编辑表格和7张图表见飞书文档草稿及report.xml。
"""
(ROOT/"report.md").write_text(md)
chart_map=[
    {"section":"TC日趋势","type":"line","source":"Metabase日聚合","claim":"展示13个完整日波动"},
    {"section":"渠道周变化","type":"diverging bar","source":"Metabase渠道聚合","claim":"识别Top7渠道TC变化；正负方向使用绿红色并直接标值"},
    {"section":"游戏规模与偏离","type":"scatter","source":"Lifecycle分游戏汇总","claim":"同时观察下注规模和RTP偏离；两端异常游戏直接标名和偏离值"},
    {"section":"下注份额变化","type":"diverging bar","source":"Lifecycle分游戏汇总","claim":"定位结构迁移"},
    {"section":"新游戏逐日","type":"small-multiple line","source":"Lifecycle分游戏汇总","claim":"观察实际与预期RTP；标注最高、最低和最新值"},
    {"section":"新游戏生命周期","type":"matrix","source":"Lifecycle详细奖池","claim":"定位偏离生命周期；正向绿蓝、负向橙红"},
    {"section":"重点游戏逐日","type":"small-multiple line","source":"Lifecycle分游戏汇总","claim":"核对持续性与单日波动；标注最高、最低和最新值"},
]
(ROOT/"chart-map.json").write_text(json.dumps(chart_map,ensure_ascii=False,indent=2))
print(json.dumps({"draft":str(draft),"chars":len(content),"tables":content.count('<table>'),"images":content.count('<img ')},ensure_ascii=False))
