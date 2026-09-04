#!/usr/bin/env python3
"""Create the 2026-09-01 complete refresh for the TC + new game RTP report."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
ASSETS = ROOT / "assets"
RTP = json.loads((ROOT / "report_data.json").read_text(encoding="utf-8"))
TC = json.loads((ROOT / "metabase_tc_2026_09_01.json").read_text(encoding="utf-8"))
DRILL = json.loads((ROOT / "deviation_game_summary_2026_08_26_09_01.json").read_text(encoding="utf-8"))
DRILL_DAILY = json.loads((ROOT / "deviation_game_daily_2026_08_26_09_01.json").read_text(encoding="utf-8"))
GAME_SHEETS = json.loads((ROOT / "deviation_game_sheets_2026_09_01.json").read_text(encoding="utf-8"))["sheets"]
HTML_OUT = PROJECT / "output/html/Waje-全产品TC与新上线游戏RTP追踪分析-V2-2026-09-02.html"
MD_OUT = PROJECT / "knowledge/02-数据/Waje-全产品TC与新上线游戏RTP追踪分析-V2-2026-09-02.md"
XML_OUT = ROOT / "feishu_overwrite_20260901.xml"
DATA_OUT = ROOT / "report_refresh_20260901.json"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
INK, MUTED, GRID, PAPER = "#17324D", "#637A90", "#DCE8F0", "#F6FBFE"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT, size=size, index=1 if bold else 0)


def pct(value, digits=2):
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def pp(value, digits=2):
    return "N/A" if value is None else f"{value:+.{digits}f}pp"


def amount(value):
    if value is None:
        return "N/A"
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:.2f}亿"
    if abs(value) >= 10_000:
        return f"{value / 10_000:.2f}万"
    return f"{value:,.0f}"


def data_uri(path: Path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def html_table(headers, rows):
    head = "".join(f"<th>{html.escape(str(x))}</th>" for x in headers)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(x))}</td>" for x in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def xml_table(headers, rows):
    head = "".join(f'<th background-color="light-gray"><p>{html.escape(str(x))}</p></th>' for x in headers)
    body = "".join("<tr>" + "".join(f"<td><p>{html.escape(str(x))}</p></td>" for x in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def tc_trend_chart(rows):
    path = ASSETS / "04_全产品完整日TC趋势_20260819_0901.png"
    image = Image.new("RGB", (1600, 860), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((64, 42), "全产品完整日 TC 趋势", fill=INK, font=font(38, True))
    draw.text((64, 100), "来源：外部生产 Metabase / whot_center.order_log；仅成功充值（type=1,status=3）与成功提现（type=2,status=103）。", fill=MUTED, font=font(18))
    left, right, top, bottom = 160, 1510, 170, 640
    values = [row["tc"] for row in rows]
    low, high = min(values) - 0.015, max(values) + 0.015
    for i in range(5):
        value = low + (high - low) * i / 4
        y = bottom - int((bottom - top) * (value - low) / (high - low))
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((72, y - 10), pct(value, 0), fill=MUTED, font=font(17))
    pts = []
    for i, row in enumerate(rows):
        x = left + int((right - left) * i / (len(rows) - 1))
        y = bottom - int((bottom - top) * (row["tc"] - low) / (high - low))
        pts.append((x, y))
        draw.text((x - 24, bottom + 20), row["date"][5:].replace("-", "/"), fill=MUTED, font=font(15))
    draw.line(pts, fill="#2D89C8", width=5)
    for (x, y), row in zip(pts, rows):
        draw.ellipse((x-7, y-7, x+7, y+7), fill="#2D89C8")
        draw.text((x - 25, y - 35), pct(row["tc"], 1), fill=INK, font=font(15, True))
    draw.text((160, 740), "8月29日—9月1日四日加权 TC 为 76.97%，较8月25日—28日的78.15%下降1.18pp。", fill=INK, font=font(20, True))
    image.save(path, "PNG", optimize=True)
    return path


def main():
    daily = TC["daily"]
    recent_daily = [row for row in daily if row["date"] >= "2026-08-26"]
    compare = TC["period_comparison"]
    current = compare["after_0829_0901"]
    previous = compare["before_0825_0828"]
    overall = RTP["overall_7d"]
    games = RTP["all_games_7d"]
    new_games = RTP["new_games"]
    tc_chart = tc_trend_chart(recent_daily)
    rtp_scatter = ASSETS / "02_近7日全游戏回报偏离与下注规模.png"
    rtp_daily = ASSETS / "01_新游戏逐日实际与预期回报比.png"
    rtp_lifecycle = ASSETS / "03_新游戏生命周期回报偏离.png"
    rtp_drill = ASSETS / "05_偏离游戏逐日RTP与全产品TC.png"

    tc_daily_rows = [[row["date"], amount(row["success_recharge_amount"]), amount(row["success_withdraw_amount"]), pct(row["tc"])] for row in recent_daily]
    channel_rows = [[
        row["channel"], pct(row["tc_0825_0828"]), pct(row["tc_0829_0901"]), pp(row["tc_change_pp"]), amount(row["recharge_0829_0901"])
    ] for row in TC["top_channels"]]
    game_rows = [[
        row["game"], amount(row["complete_bet"]), pct(row["actual_rtp"]), pct(row["expected_rtp"]), pp(row["rtp_gap_pp"]), pct(row["expected_coverage"]), pp(row["adjustment_pp"]), "可比" if row["rtp_gap_pp"] is not None else "N/A·预期缺失"
    ] for row in games]
    new_rows = [[
        name, item["game_id"], f'{item["launch"][5:]}—09/01', f'{item["days"]}天', amount(item["complete_bet"]), pct(item["actual_rtp"]), pct(item["expected_rtp"]), pp(item["rtp_gap_pp"]), amount(item["profit_vs_expected"]), pp(item["adjustment_pp"]), "持续观察"
    ] for name, item in new_games.items()]
    drill_rows = [[
        row["game"], row["reason"], amount(row["complete_bet"]), pct(row["actual_rtp"]), pct(row["expected_rtp"]), pp(row["rtp_gap_pp"]), pp(row["vs_all_product_pp"])
    ] for row in DRILL]
    drill_daily_rows = [[
        row["date"], row["game"], pct(row["all_product_tc"]), amount(row["complete_bet"]), pct(row["actual_rtp"]), pct(row["expected_rtp"]), pp(row["rtp_gap_pp"])
    ] for row in DRILL_DAILY]

    current_label = "8月29日—9月1日"
    previous_label = "8月25日—28日"
    overview = {
        "tc_current": current,
        "tc_previous": previous,
        "rtp_overall": overall,
        "new_games": new_games,
        "source": {"metabase_cutoff": "2026-09-01", "lifecycle_revision": RTP["source"]["workbook_revision"], "lifecycle_cutoff": RTP["source"]["as_of"]},
    }
    DATA_OUT.write_text(json.dumps(overview, ensure_ascii=False, indent=2), encoding="utf-8")

    body = f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Waje 全产品TC与新上线游戏RTP追踪分析 V2｜截至2026年9月1日</title><style>
:root{{--ink:#17324D;--muted:#60788E;--line:#DCE8F0;--paper:#F6FBFE;--blue:#2D89C8;--green:#1FA187;--gold:#E29B14;--purple:#7C72C9;--red:#D95E5E}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,\"PingFang SC\",\"Microsoft YaHei\",sans-serif;line-height:1.65}}.page{{max-width:1200px;margin:auto;padding:32px 24px 80px}}header{{background:linear-gradient(115deg,#113E66,#2D89A1);color:#fff;border-radius:22px;padding:36px 42px;margin-bottom:24px}}h1{{font-size:34px;line-height:1.25;margin:0 0 10px}}header p{{font-size:17px;margin:0}}.chips{{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}}.chip{{border:1px solid rgba(255,255,255,.35);padding:5px 12px;border-radius:20px;font-size:13px}}section{{background:white;border:1px solid var(--line);border-radius:18px;padding:28px 32px;margin:20px 0}}h2{{font-size:26px;margin:0 0 10px}}p{{margin:8px 0}}.callout{{background:#EEF7FE;border-left:4px solid var(--blue);padding:16px 18px;border-radius:12px;margin:14px 0}}.warn{{background:#FFF9E9;border-color:var(--gold)}}.risk{{background:#FFF1F1;border-color:var(--red)}}.kpis{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}.kpi{{border:1px solid var(--line);background:#FBFDFF;border-radius:12px;padding:14px}}.kpi small{{display:block;color:var(--muted)}}.kpi strong{{font-size:26px;display:block;margin-top:4px}}.table-wrap{{overflow-x:auto;margin:14px 0}}table{{width:100%;border-collapse:collapse;min-width:780px;font-size:14px}}th{{background:#EEF4F8;color:#35526A;text-align:left}}th,td{{padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap}}figure{{margin:18px 0;background:#F8FCFF;border:1px solid var(--line);padding:10px;border-radius:12px}}figure img{{display:block;width:100%;height:auto}}figcaption{{color:var(--muted);font-size:13px;padding:6px 2px 0}}ol{{padding-left:22px}}.muted{{color:var(--muted)}}@media(max-width:760px){{.page{{padding:16px 10px 40px}}header{{padding:24px 20px}}h1{{font-size:27px}}section{{padding:22px 16px}}.kpis{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
</style></head><body><main class=\"page\"><header><h1>Waje 全产品 TC 与新上线游戏 RTP 追踪分析 V2</h1><p>截至 2026 年 9 月 1 日｜全产品 TC 使用外部生产 Metabase 完整日聚合；游戏 RTP 使用 GM Lifecycle Pool V2（Joint）修订{RTP['source']['workbook_revision']}。</p><div class=\"chips\"><span class=\"chip\">TC完整日：截至9月1日</span><span class=\"chip\">全游戏RTP：8月26日—9月1日</span><span class=\"chip\">Hilo/Plinko：8月21日—9月1日</span><span class=\"chip\">Tower：8月25日—9月1日</span></div></header>
<section><h2>核心结论</h2><div class=\"kpis\"><div class=\"kpi\"><small>{current_label} 全产品TC</small><strong>{pct(current['tc'])}</strong><small>成功提现 ÷ 成功充值</small></div><div class=\"kpi\"><small>较{previous_label}</small><strong>{pp(compare['tc_change_pp'])}</strong><small>四日加权比较</small></div><div class=\"kpi\"><small>近7日全游戏RTP观察值</small><strong>{pct(overall['actual_rtp'])}</strong><small>生命周期池完全口径</small></div><div class=\"kpi\"><small>预期字段下注覆盖</small><strong>{pct(overall['expected_coverage'])}</strong><small>仅覆盖范围可比</small></div></div>
<div class=\"callout\"><b>TC结论：</b>{current_label}四日加权TC为<b>{pct(current['tc'])}</b>，低于{previous_label}的<b>{pct(previous['tc'])}</b>（{pp(compare['tc_change_pp'])}）。因此，8月26—28日的部分日/同窗口上行不再代表当前完整日资金趋势。</div>
<div class=\"callout warn\"><b>新游戏结论：</b>Hilo 12日回报比<b>{pct(new_games['Hilo']['actual_rtp'])}</b>（较预期{pp(new_games['Hilo']['rtp_gap_pp'])}）；Plinko为<b>{pct(new_games['Plinko']['actual_rtp'])}</b>（{pp(new_games['Plinko']['rtp_gap_pp'])}）；Tower为<b>{pct(new_games['Tower']['actual_rtp'])}</b>（{pp(new_games['Tower']['rtp_gap_pp'])}）。三款均仅构成持续观察信号，不能单独解释全站TC或判定故障。</div></section>
<section><h2>1. 全产品 TC：完整日已更新至9月1日</h2><p class=\"muted\">来源：外部生产 Metabase / <code>whot_center.order_log</code>；仅统计成功现金充值（type=1,status=3）和成功提现（type=2,status=103），时区 Asia/Hong_Kong。</p>{html_table(['业务日','成功充值','成功提现','TC'], tc_daily_rows)}<figure><img src=\"{data_uri(tc_chart)}\" alt=\"全产品完整日TC趋势\"><figcaption>8月26日—9月1日完整日TC；不混入部分日或小时窗口。</figcaption></figure></section>
<section><h2>2. 8月29日—9月1日：与前四日对比</h2>{html_table(['期间','成功充值','成功提现','四日加权TC'], [[previous_label,amount(previous['recharge']),amount(previous['withdraw']),pct(previous['tc'])],[current_label,amount(current['recharge']),amount(current['withdraw']),pct(current['tc'])],['变化',amount(current['recharge']-previous['recharge']),amount(current['withdraw']-previous['withdraw']),pp(compare['tc_change_pp'])]])}<p><b>渠道对比：</b>按注册渠道聚合；用于识别结构变化，不等同事件时点广告归因。</p>{html_table(['渠道','8/25—8/28 TC','8/29—9/1 TC','变化','后段成功充值'], channel_rows)}</section>
<section><h2>3. 全游戏近7日回报与下注：8月26日—9月1日</h2><p>完全下注额为<b>{amount(overall['complete_bet'])}</b>，生命周期池完全实际回报比为<b>{pct(overall['actual_rtp'])}</b>。在预期字段覆盖的{pct(overall['expected_coverage'])}下注范围内，实际回报比{pct(overall['actual_rtp_expected_subset'])}，较预期{pct(overall['expected_rtp'])}{pp(overall['rtp_gap_pp'])}。</p><figure><img src=\"{data_uri(rtp_scatter)}\" alt=\"全游戏回报偏离与下注规模\"><figcaption>横轴为预期字段有效范围内的完全实际回报比减完全预期回报比；纵轴为完全下注额（对数刻度）。</figcaption></figure>{html_table(['游戏','完全下注额','完全实际回报比','完全预期回报比','RTP差异','预期覆盖','调整影响','状态'], game_rows)}</section>
<section><h2>4. Hilo、Plinko、Tower：上线后专项</h2>{html_table(['游戏','Game ID','统计期间','完整日','完全下注额','实际回报比','预期回报比','RTP差异','实际减预期盈利','调整影响','状态'],new_rows)}<figure><img src=\"{data_uri(rtp_daily)}\" alt=\"新游戏逐日回报比\"><figcaption>各色线为完全实际回报比，黄色线为完全预期回报比；Hilo/Plinko统计8月21日—9月1日，Tower统计8月25日—9月1日。</figcaption></figure><figure><img src=\"{data_uri(rtp_lifecycle)}\" alt=\"新游戏生命周期回报偏离\"><figcaption>生命周期1—4拆解。颜色表示方向和幅度，不代表最终结算故障等级。</figcaption></figure></section>
<section><h2>5. 与TC的关系、数据边界与行动</h2><div class=\"callout risk\"><b>边界：</b>RTP与TC相关但非线性。历史余额、大奖分布、Bonus、资产转换、退款、跨日结算和提现节奏均会影响TC。只有高回报偏离、高调整影响和高下注额同时出现时，才升级为优先核查对象。</div><ol><li><b>P0：</b>补齐游戏×配置版本×有效局数×最终派奖×取消/退款×免费注/Bonus的聚合事实，验证生命周期池观察值与最终结算一致。</li><li><b>P0：</b>对Plinko补充难度、ROW、球数、倍率分布；对Tower补充层数、Cash Out/失败和封顶触发；对Hilo补充猜测、Skip、Cash Out和赔率分布。</li><li><b>P1：</b>将完整日TC、成功充值/提现、全游戏回报观察值、新游戏逐日偏离固定为日更看板；不输出用户或订单明细。</li></ol><p class=\"muted\"><b>数据来源：</b>外部生产Metabase（全产品TC，截止9月1日）与 GM Lifecycle Pool V2（Joint）修订{RTP['source']['workbook_revision']}（游戏回报，截止9月1日）。预期回报比为0、Infinity、缺失或无有效下注时，下注规模保留，RTP差异标记为N/A·预期缺失。当前不含最终结算、退款、免费注、配置版本和用户级大奖分布，因此不输出故障结论。</p></section></main></body></html>"""
    drill_html = f"""<section><h2>5. 明显偏离游戏：逐日下钻</h2><p>入选条件为：近7日实际/预期偏离绝对值达到3pp，或新游戏实际回报比高于全盘约2pp。下表与图中的“全产品TC”是同日全站指标，<b>不是该游戏自身的TC</b>。</p>{html_table(['游戏','入选原因','近7日完全下注额','实际回报比','预期回报比','实际-预期','较全盘RTP'], drill_rows)}<div class=\"callout risk\"><b>优先定位：</b>EasyWin在8月31日的完全实际回报比为<b>204.70%</b>，完全下注额<b>64.48万</b>，同日全产品TC为<b>79.57%</b>。该单日高回报不等同于全站TC异常，但应优先核验有效局数、最终派奖、取消/退款和配置版本。</div><figure><img src=\"{data_uri(rtp_drill)}\" alt=\"偏离游戏逐日RTP与全产品TC\"><figcaption>每个小图展示该游戏逐日RTP与预期RTP；日期下方为同日全产品TC，便于观察是否同步，但不代表因果关系。</figcaption></figure>{html_table(['日期','游戏','同日全产品TC','完全下注额','实际回报比','预期回报比','RTP差异'], drill_daily_rows)}</section>"""
    drill_html = "<section><h2>5. 明显偏离游戏：逐日下钻</h2><p>每款游戏单独展示。节点标注为实际RTP，黄色线为该窗口的加权预期RTP基线；日期下方的全产品TC仅做同日对照，不代表游戏自身TC或因果关系。</p>"
    for game in ("EasyWin", "Blackjack", "Tower", "Plinko"):
        sheet = GAME_SHEETS[game]
        period = sheet["period"]
        rows = [[r["date"], pct(r["all_product_tc"]), amount(r["complete_bet"]), pct(r["actual_rtp"]), pct(r["expected_rtp"]), pp(r["rtp_gap_pp"])] for r in sheet["rows"]]
        label = "30日" if game == "EasyWin" else "近7日"
        drill_html += f"<h3>{game}｜{label}独立观察</h3><p><b>加权平均实际RTP：</b>{pct(period['actual_rtp'])}；<b>预期基线：</b>{pct(period['expected_rtp'])}；<b>平均偏离：</b>{pp(period['rtp_gap_pp'])}；<b>完全下注额：</b>{amount(period['complete_bet'])}。</p>"
        if game == "EasyWin":
            drill_html += '<div class="callout risk"><b>优先核验：</b>8月31日实际RTP 204.70%，完全下注64.48万，较预期+107.74pp；同日全产品TC 79.57%。先核验最终派奖、有效局数、取消/退款与配置版本。</div>'
        drill_html += f"<figure><img src=\"{data_uri(PROJECT / sheet['chart'])}\" alt=\"{game}逐日RTP\"><figcaption>{game}逐日RTP：节点数值与预期基线。</figcaption></figure>{html_table(['日期','同日全产品TC','完全下注额','实际RTP','预期RTP','RTP差异'], rows)}"
    drill_html += "</section>"
    body = body.replace('<section><h2>5. 与TC的关系、数据边界与行动</h2>', drill_html + '<section><h2>6. 与TC的关系、数据边界与行动</h2>', 1)
    body = body.replace('<li><b>P0：</b>补齐游戏×配置版本×有效局数×最终派奖×取消/退款×免费注/Bonus的聚合事实，验证生命周期池观察值与最终结算一致。</li>', '<li><b>P0：</b>优先完成EasyWin 8月31日的最终结算、有效局数、取消/退款和配置版本核验；同时复核Tower与Plinko的玩法参数和倍率分布。</li><li><b>P0：</b>补齐游戏×配置版本×有效局数×最终派奖×取消/退款×免费注/Bonus的聚合事实，验证生命周期池观察值与最终结算一致。</li>', 1)
    HTML_OUT.write_text(body, encoding="utf-8")

    md = f"""---
type: tc-rtp-tracking-report
status: published_observational
as_of: 2026-09-01
sources:
  - production Metabase / whot_center.order_log
  - GM Lifecycle Pool V2 (Joint) revision {RTP['source']['workbook_revision']}
---

# Waje 全产品TC与新上线游戏RTP追踪分析 V2｜截至2026年9月1日

## 核心结论

- **8月29日—9月1日全产品TC为{pct(current['tc'])}，较8月25日—28日的{pct(previous['tc'])}{pp(compare['tc_change_pp'])}。** 当前完整日聚合未延续8月26—28日部分窗口的上行表述。
- 近7日生命周期池完全实际回报比为 **{pct(overall['actual_rtp'])}**；预期字段覆盖 **{pct(overall['expected_coverage'])}** 的下注额，可比范围差异为 **{pp(overall['rtp_gap_pp'])}**。
- Hilo / Plinko / Tower 分别观察12 / 12 / 8个完整自然日，均为早期RTP观察，不构成最终结算故障结论。

## 核心数据

| 指标 | {previous_label} | {current_label} | 变化 |
|---|---:|---:|---:|
| 成功充值 | {amount(previous['recharge'])} | {amount(current['recharge'])} | {amount(current['recharge']-previous['recharge'])} |
| 成功提现 | {amount(previous['withdraw'])} | {amount(current['withdraw'])} | {amount(current['withdraw']-previous['withdraw'])} |
| TC | {pct(previous['tc'])} | {pct(current['tc'])} | {pp(compare['tc_change_pp'])} |

## 新游戏上线后观察

| 游戏 | 窗口 | 完全下注额 | 实际回报比 | 预期回报比 | RTP差异 | 调整影响 |
|---|---|---:|---:|---:|---:|---:|
""" + "\n".join(f"| {name} | {item['launch'][5:]}—09/01 | {amount(item['complete_bet'])} | {pct(item['actual_rtp'])} | {pct(item['expected_rtp'])} | {pp(item['rtp_gap_pp'])} | {pp(item['adjustment_pp'])} |" for name, item in new_games.items()) + f"""

## 口径与边界

- TC = 成功提现（type=2,status=103）÷ 成功现金充值（type=1,status=3）。
- 生命周期池完全实际回报比 = `1 − Σ完全实际盈利 ÷ Σ完全下注额`；预期缺失记录不参与实际/预期差异比较。
- 所有结果均为脱敏聚合数据；无用户、订单、银行卡、设备或身份明细。

## 工件

- `analysis/tc_game_rtp_tracking_2026_09_02/metabase_tc_2026_09_01.json`
- `analysis/tc_game_rtp_tracking_2026_09_02/report_data.json`
- `analysis/tc_game_rtp_tracking_2026_09_02/quality_checks.json`
"""
    drill_md = """## 明显偏离游戏：逐日下钻

入选条件：近7日实际/预期偏离绝对值达到3pp，或新游戏实际回报比高于全盘约2pp。表中的全产品TC是同日全站指标，不是游戏自身TC。

| 游戏 | 入选原因 | 完全下注额 | 实际回报比 | 预期回报比 | 实际-预期 | 较全盘RTP |
|---|---|---:|---:|---:|---:|---:|
""" + "\n".join(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} |" for row in drill_rows) + """

**重点：** EasyWin 在8月31日实际回报比为 **204.70%**、完全下注 **64.48万**，同日全产品TC为 **79.57%**。应优先核验该游戏的有效局数、最终派奖、取消/退款和配置版本；该单日现象不等同于全站TC异常。

| 日期 | 游戏 | 同日全产品TC | 完全下注额 | 实际回报比 | 预期回报比 | RTP差异 |
|---|---|---:|---:|---:|---:|---:|
""" + "\n".join(f"| {' | '.join(map(str, row))} |" for row in drill_daily_rows) + """

"""
    drill_md = "## 明显偏离游戏：逐日下钻\n\n每款游戏单独展示。节点标注为实际RTP，基线为该窗口的加权预期RTP；同日全产品TC只作日期对照。\n\n"
    for game in ("EasyWin", "Blackjack", "Tower", "Plinko"):
        sheet = GAME_SHEETS[game]
        period = sheet["period"]
        label = "30日" if game == "EasyWin" else "近7日"
        drill_md += f"### {game}｜{label}独立观察\n\n加权平均实际RTP **{pct(period['actual_rtp'])}**；预期基线 **{pct(period['expected_rtp'])}**；平均偏离 **{pp(period['rtp_gap_pp'])}**；完全下注额 **{amount(period['complete_bet'])}**。\n\n"
        if game == "EasyWin":
            drill_md += "重点：8月31日实际RTP **204.70%**、完全下注 **64.48万**、较预期 **+107.74pp**；同日全产品TC **79.57%**。先核验最终派奖、有效局数、取消/退款与配置版本。\n\n"
        drill_md += "| 日期 | 同日全产品TC | 完全下注额 | 实际RTP | 预期RTP | RTP差异 |\n|---|---:|---:|---:|---:|---:|\n"
        drill_md += "\n".join(f"| {r['date']} | {pct(r['all_product_tc'])} | {amount(r['complete_bet'])} | {pct(r['actual_rtp'])} | {pct(r['expected_rtp'])} | {pp(r['rtp_gap_pp'])} |" for r in sheet["rows"]) + "\n\n"
    md = md.replace("## 口径与边界", drill_md + "## 口径与边界", 1)
    MD_OUT.write_text(md, encoding="utf-8")

    xml = f"""<title>Waje 全产品TC与新上线游戏RTP追踪分析 V2｜截至2026年9月1日</title>
<callout emoji=\"🎯\" background-color=\"light-blue\" border-color=\"blue\"><p><b>分析范围：</b>全产品TC更新至2026年9月1日完整自然日；全游戏RTP使用GM Lifecycle Pool V2（Joint）修订{RTP['source']['workbook_revision']}，窗口为8月26日—9月1日；Hilo/Plinko统计8月21日—9月1日，Tower统计8月25日—9月1日。</p></callout>
<h1>核心结论</h1><ol><li><b>全产品TC回落。</b>{current_label}四日加权TC为<b>{pct(current['tc'])}</b>，较{previous_label}的{pct(previous['tc'])}{pp(compare['tc_change_pp'])}。</li><li><b>近7日全游戏回报稳定在观察范围。</b>完全实际回报比{pct(overall['actual_rtp'])}；预期字段覆盖{pct(overall['expected_coverage'])}下注额，可比范围内较预期{pp(overall['rtp_gap_pp'])}。</li><li><b>新游戏均为早期观察。</b>Hilo {pct(new_games['Hilo']['actual_rtp'])}（{pp(new_games['Hilo']['rtp_gap_pp'])}）、Plinko {pct(new_games['Plinko']['actual_rtp'])}（{pp(new_games['Plinko']['rtp_gap_pp'])}）、Tower {pct(new_games['Tower']['actual_rtp'])}（{pp(new_games['Tower']['rtp_gap_pp'])}）；不能直接推导全站TC或故障。</li></ol>
<h1>全产品 TC：完整日更新至9月1日</h1><p>来源：外部生产 Metabase / <code>whot_center.order_log</code>；成功充值为type=1,status=3，成功提现为type=2,status=103，时区Asia/Hong_Kong。</p>{xml_table(['业务日','成功充值','成功提现','TC'], tc_daily_rows)}<img path=\"@./analysis/tc_game_rtp_tracking_2026_09_02/assets/04_全产品完整日TC趋势_20260819_0901.png\" caption=\"全产品完整日TC趋势（8月26日—9月1日）\"/>
<h1>8月29日—9月1日：与前四日对比</h1>{xml_table(['期间','成功充值','成功提现','四日加权TC'], [[previous_label,amount(previous['recharge']),amount(previous['withdraw']),pct(previous['tc'])],[current_label,amount(current['recharge']),amount(current['withdraw']),pct(current['tc'])],['变化',amount(current['recharge']-previous['recharge']),amount(current['withdraw']-previous['withdraw']),pp(compare['tc_change_pp'])]])}<p><b>渠道对比：</b>按注册渠道聚合，用于观察资金结构，不替代事件时点归因。</p>{xml_table(['渠道','8/25—8/28 TC','8/29—9/1 TC','变化','后段成功充值'], channel_rows)}
<h1>全游戏近7日回报与下注</h1><p>统计窗口：8月26日—9月1日。完全下注额{amount(overall['complete_bet'])}；完全实际回报比{pct(overall['actual_rtp'])}；预期字段覆盖{pct(overall['expected_coverage'])}。</p><img path=\"@./analysis/tc_game_rtp_tracking_2026_09_02/assets/02_近7日全游戏回报偏离与下注规模.png\" caption=\"全游戏回报偏离与完全下注规模\"/>{xml_table(['游戏','完全下注额','完全实际回报比','完全预期回报比','RTP差异','预期覆盖','调整影响','状态'], game_rows)}
<h1>Hilo、Plinko、Tower：上线后专项</h1>{xml_table(['游戏','Game ID','统计期间','完整日','完全下注额','实际回报比','预期回报比','RTP差异','实际减预期盈利','调整影响','状态'], new_rows)}<img path=\"@./analysis/tc_game_rtp_tracking_2026_09_02/assets/01_新游戏逐日实际与预期回报比.png\" caption=\"新游戏逐日完全实际/预期回报比\"/><img path=\"@./analysis/tc_game_rtp_tracking_2026_09_02/assets/03_新游戏生命周期回报偏离.png\" caption=\"新游戏生命周期1—4回报偏离\"/>
<h1>数据边界与下一步</h1><callout emoji=\"🔎\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>RTP与TC相关但非线性：</b>历史余额、大奖、Bonus、资产转换、退款、跨日结算和提现节奏均会影响TC。只有高回报偏离、高调整影响和高下注额同时出现时，才升级为优先核查对象。</p></callout><ol><li><b>P0：</b>补齐游戏×配置版本×有效局数×最终派奖×取消/退款×免费注/Bonus聚合事实。</li><li><b>P0：</b>分别补齐Hilo猜测/Skip/Cash Out、Plinko难度/ROW/球数/倍率、Tower层数/Cash Out/封顶触发等玩法维度。</li><li><b>P1：</b>日更完整日TC、成功充值/提现、全游戏RTP观察值和新游戏逐日偏离；不输出用户或订单明细。</li></ol><p>预期回报比为0、Infinity、缺失或无有效下注时，仅保留下注规模，RTP差异标记为N/A·预期缺失。当前无最终结算、退款、免费注、配置版本和用户级大奖分布，不输出故障结论。</p>"""
    drill_xml = f"""<h1>明显偏离游戏：逐日下钻</h1><p>入选条件：近7日实际/预期偏离绝对值达到3pp，或新游戏实际回报比高于全盘约2pp。下表与图中的“全产品TC”是同日全站指标，<b>不是该游戏自身的TC</b>。</p>{xml_table(['游戏','入选原因','近7日完全下注额','实际回报比','预期回报比','实际-预期','较全盘RTP'], drill_rows)}<callout emoji=\"🔎\" background-color=\"light-red\" border-color=\"red\"><p><b>优先定位：</b>EasyWin在8月31日的完全实际回报比为<b>204.70%</b>，完全下注额<b>64.48万</b>，同日全产品TC为<b>79.57%</b>。该单日高回报不等同于全站TC异常，但应优先核验有效局数、最终派奖、取消/退款和配置版本。</p></callout><img path=\"@./analysis/tc_game_rtp_tracking_2026_09_02/assets/05_偏离游戏逐日RTP与全产品TC.png\" caption=\"明显偏离游戏：逐日RTP与全产品TC\"/>{xml_table(['日期','游戏','同日全产品TC','完全下注额','实际回报比','预期回报比','RTP差异'], drill_daily_rows)}"""
    drill_xml = "<h1>明显偏离游戏：逐日下钻</h1><p>每款游戏单独展示。节点标注为实际RTP，黄色线为该窗口的加权预期RTP基线；日期下方的全产品TC仅做同日对照，不代表游戏自身TC或因果关系。</p>"
    for game in ("EasyWin", "Blackjack", "Tower", "Plinko"):
        sheet = GAME_SHEETS[game]
        period = sheet["period"]
        label = "30日" if game == "EasyWin" else "近7日"
        table_rows = [[r["date"], pct(r["all_product_tc"]), amount(r["complete_bet"]), pct(r["actual_rtp"]), pct(r["expected_rtp"]), pp(r["rtp_gap_pp"])] for r in sheet["rows"]]
        drill_xml += f"<h2>{game}｜{label}独立观察</h2><p><b>加权平均实际RTP：</b>{pct(period['actual_rtp'])}；<b>预期基线：</b>{pct(period['expected_rtp'])}；<b>平均偏离：</b>{pp(period['rtp_gap_pp'])}；<b>完全下注额：</b>{amount(period['complete_bet'])}。</p>"
        if game == "EasyWin":
            drill_xml += "<callout emoji=\"🔎\" background-color=\"light-red\" border-color=\"red\"><p><b>优先核验：</b>8月31日实际RTP 204.70%，完全下注64.48万，较预期+107.74pp；同日全产品TC 79.57%。先核验最终派奖、有效局数、取消/退款与配置版本。</p></callout>"
        drill_xml += f"<img path=\"@./analysis/tc_game_rtp_tracking_2026_09_02/assets/06_{game}_逐日RTP观察.png\" caption=\"{game}逐日RTP：节点数值与预期基线\"/>" + xml_table(['日期','同日全产品TC','完全下注额','实际RTP','预期RTP','RTP差异'], table_rows)
    xml = xml.replace('<h1>数据边界与下一步</h1>', drill_xml + '<h1>数据边界与下一步</h1>', 1)
    xml = xml.replace('<li><b>P0：</b>补齐游戏×配置版本×有效局数×最终派奖×取消/退款×免费注/Bonus聚合事实。</li>', '<li><b>P0：</b>优先完成EasyWin 8月31日的最终结算、有效局数、取消/退款和配置版本核验；同时复核Tower与Plinko的玩法参数和倍率分布。</li><li><b>P0：</b>补齐游戏×配置版本×有效局数×最终派奖×取消/退款×免费注/Bonus聚合事实。</li>', 1)
    XML_OUT.write_text(xml, encoding="utf-8")
    print(json.dumps({"status": "ok", "html": str(HTML_OUT), "markdown": str(MD_OUT), "xml": str(XML_OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
