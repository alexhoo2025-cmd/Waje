#!/usr/bin/env python3
"""Build the lightweight-game historical inventory and recent-change analysis."""
from __future__ import annotations

import html
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/lark/2026-08-18"
OUT_HTML = ROOT / "output/html/Waje-轻量化游戏历史数据盘点与近30天专题分析框架-2026-08-18.html"
OUT_MD = ROOT / "knowledge/01-产品/Waje-轻量化游戏历史数据盘点与近30天专题分析框架-2026-08-18.md"
OUT_DATA = ROOT / "analysis/lightgame_topic_2026_08_18/analysis.json"
ASSET_DIR = ROOT / "analysis/lightgame_topic_2026_08_18/assets"
EXCEL_EPOCH = datetime(1899, 12, 30)

BLUE = "#2378BF"
GREEN = "#2FA377"
AMBER = "#D99B20"
RED = "#D85A65"
NAVY = "#173A5E"
MUTED = "#58718A"
GRID = "#DDEAF4"


def serial_to_date(value: Any) -> date:
    return (EXCEL_EPOCH + timedelta(days=float(value))).date()


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def pp(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.1f}pp"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size, index=0)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, draw_font: ImageFont.ImageFont, max_width: int) -> list[str]:
    rows: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if draw.textlength(candidate, font=draw_font) <= max_width:
            current = candidate
        else:
            rows.append(current)
            current = char
    if current:
        rows.append(current)
    return rows or [""]


def save_click_png(rows: list[dict[str, Any]], pre: list[dict[str, Any]], post: list[dict[str, Any]]) -> Path:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSET_DIR / "历史点击率趋势.png"
    image = Image.new("RGB", (1500, 760), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title_font, text_font, small_font = font(32), font(22), font(18)
    draw.text((70, 45), "H5 新注册用户游戏入口点击率：5月历史快照", fill=NAVY, font=title_font)
    draw.text((70, 94), "口径：游戏入口点击用户数 ÷ 当日新增人数；5/11 为轻量化上线日。", fill=MUTED, font=text_font)
    left, top, right, bottom = 110, 170, 1420, 620
    for tick in [0.2, 0.3, 0.4, 0.5, 0.6]:
        y = bottom - (tick - 0.2) / 0.4 * (bottom - top)
        draw.line((left, y, right, y), fill="#E4EEF5", width=2)
        draw.text((30, y - 12), pct(tick, 0), fill=MUTED, font=small_font)
    points: list[tuple[float, float]] = []
    for idx, row in enumerate(rows):
        x = left + (right - left) * idx / max(1, len(rows) - 1)
        y = bottom - (row["点击用户占比"] - 0.2) / 0.4 * (bottom - top)
        points.append((x, y))
        draw.text((x - 20, bottom + 14), row["date"].strftime("%m/%d"), fill=MUTED, font=small_font)
    draw.line(points, fill=BLUE, width=5)
    for x, y in points:
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=BLUE)
    launch_idx = next(i for i, row in enumerate(rows) if row["date"] == date(2026, 5, 11))
    x = points[launch_idx][0]
    draw.line((x, top, x, bottom), fill=AMBER, width=4)
    draw.text((x + 14, top + 10), "5/11 轻量化上线", fill=AMBER, font=text_font)
    pre_rate = sum(r["事件用户数"] for r in pre) / sum(r["新增人数"] for r in pre)
    post_rate = sum(r["事件用户数"] for r in post) / sum(r["新增人数"] for r in post)
    draw.rounded_rectangle((90, 665, 690, 735), radius=12, fill="#EAF5FE")
    draw.text((120, 684), f"上线前（5/1–5/10）：{pct(pre_rate)}", fill=NAVY, font=text_font)
    draw.rounded_rectangle((750, 665, 1410, 735), radius=12, fill="#FFF4E2")
    draw.text((780, 684), f"上线后（5/12–5/17）：{pct(post_rate)}，{pp(post_rate-pre_rate)}", fill="#945F02", font=text_font)
    image.save(path)
    return path


def save_channel_png() -> Path:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSET_DIR / "历史渠道首局与非0局对比.png"
    image = Image.new("RGB", (1500, 800), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title_font, text_font, small_font = font(30), font(22), font(18)
    draw.text((70, 38), "5.11 上线前后：0局率与非0局率历史快照", fill=NAVY, font=title_font)
    draw.text((70, 86), "注意：0局与非0局来自不同页面/窗口，仅作方向性历史基线，不作为同一漏斗的严格互补关系。", fill=MUTED, font=text_font)
    items = [
        ("wajeH5", 0.8129, 0.8177, 0.182, 0.189),
        ("WajeBet H5", 0.6363, 0.6373, 0.363, 0.369),
        ("PWW", 0.6171, 0.6188, 0.381, 0.392),
    ]
    groups = [("0局率（越低越好）", 0.0, 0.9, 160, RED), ("非0局率（越高越好）", 0.0, 0.5, 500, GREEN)]
    for label, lo, hi, top, color in groups:
        draw.text((80, top - 45), label, fill=NAVY, font=text_font)
        left, right, base = 260, 1400, top + 180
        for tick in [0, 0.2, 0.4, 0.6, 0.8]:
            if tick > hi: continue
            x = left + (right-left)*(tick-lo)/(hi-lo)
            draw.line((x, top, x, base), fill="#E4EEF5", width=1)
            draw.text((x-12, base+10), pct(tick,0), fill=MUTED, font=small_font)
        for idx, (name, zero_pre, zero_post, nz_pre, nz_post) in enumerate(items):
            y = top + 5 + idx*55
            draw.text((80, y+8), name, fill=NAVY, font=small_font)
            a, b = (zero_pre, zero_post) if label.startswith("0局") else (nz_pre, nz_post)
            for value, offset, shade in [(a,0,"#B8CEE1"),(b,23,color)]:
                x2 = left + (right-left)*(value-lo)/(hi-lo)
                draw.rounded_rectangle((left,y+offset,x2,y+offset+17),radius=8,fill=shade)
                draw.text((x2+8,y+offset-2),pct(value),fill=NAVY,font=small_font)
    draw.text((270, 736), "浅色=上线前；深色=上线后。标准 H5 的0局率仍在80%以上，首局问题未被历史改造解决。", fill=MUTED, font=small_font)
    image.save(path)
    return path


def save_timeline_png(timeline: list[dict[str, str]]) -> Path:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSET_DIR / "近30天轻量化游戏变更时间轴.png"
    image = Image.new("RGB", (1500, 1210), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    title_font, text_font, small_font = font(30), font(20), font(17)
    draw.text((70, 38), "近30天：轻量化游戏及其干扰事件", fill=NAVY, font=title_font)
    draw.text((70, 84), "数据来源：更新记录（2026-07-14—2026-08-12）。蓝=直接游戏事件；黄=版本/埋点；红=故障或强干扰。", fill=MUTED, font=text_font)
    xline, start_y, step = 250, 150, 74
    draw.line((xline, start_y-20, xline, start_y+step*(len(timeline)-1)+20), fill="#C7D9E8", width=5)
    colors = {"direct": BLUE, "instrument": AMBER, "confounder": RED}
    for i, item in enumerate(timeline):
        y = start_y + i*step
        color = colors[item["kind"]]
        draw.ellipse((xline-12,y-12,xline+12,y+12),fill=color)
        draw.text((70,y-12),item["date"],fill=NAVY,font=small_font)
        wrapped = wrap(draw,item["label"],small_font,1100)
        for j,line in enumerate(wrapped[:2]):
            draw.text((290,y-15+j*23),line,fill="#24455F",font=small_font)
    image.save(path)
    return path


def svg_click(rows: list[dict[str, Any]], pre_rate: float, post_rate: float) -> str:
    left, top, width, height = 70, 42, 900, 270
    out = [f'<svg viewBox="0 0 1040 380" role="img" aria-label="H5新注册用户点击率趋势">']
    for tick in [0.2, 0.3, 0.4, 0.5, 0.6]:
        y = top + height * (1 - (tick-0.2)/0.4)
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+width}" y2="{y:.1f}" class="gridline"/><text x="18" y="{y+5:.1f}" class="axis">{pct(tick,0)}</text>')
    pts=[]
    for i,row in enumerate(rows):
        x=left+width*i/(len(rows)-1)
        y=top+height*(1-(row['点击用户占比']-0.2)/0.4)
        pts.append((x,y))
        out.append(f'<text x="{x:.1f}" y="{top+height+30}" class="axis" text-anchor="middle">{row["date"].strftime("%-m/%-d")}</text>')
    out.append('<path class="line-blue" d="M '+' L '.join(f'{x:.1f} {y:.1f}' for x,y in pts)+'"/>')
    for x,y in pts: out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.4" fill="{BLUE}"/>')
    launch_x=pts[10][0]
    out.append(f'<line x1="{launch_x:.1f}" y1="{top}" x2="{launch_x:.1f}" y2="{top+height}" stroke="{AMBER}" stroke-width="3" stroke-dasharray="6 5"/><text x="{launch_x+8:.1f}" y="62" class="event-label">5/11 上线</text>')
    out.append(f'<text x="{left}" y="360" class="summary-label">上线前加权点击率 <tspan class="summary-number">{pct(pre_rate)}</tspan></text><text x="{left+420}" y="360" class="summary-label">上线后加权点击率 <tspan class="summary-number warning">{pct(post_rate)}（{pp(post_rate-pre_rate)}）</tspan></text></svg>')
    return ''.join(out)


def svg_history_bars() -> str:
    items=[("标准H5",.8129,.8177,.182,.189),("WajeBet H5",.6363,.6373,.363,.369),("PWW",.6171,.6188,.381,.392)]
    out=['<svg viewBox="0 0 1040 480" role="img" aria-label="历史渠道首局与非0局对比">']
    out.append('<text x="60" y="34" class="chart-title">0局率（越低越好）</text><text x="550" y="34" class="chart-title">非0局率（越高越好）</text>')
    for i,(name,zpre,zpost,npre,npost) in enumerate(items):
        y=70+i*115
        out.append(f'<text x="30" y="{y+26}" class="bar-label">{esc(name)}</text>')
        for value, yy, color in [(zpre,y,'#B9CCDD'),(zpost,y+28,RED)]:
            width=value/.9*360
            out.append(f'<rect x="160" y="{yy}" width="{width:.1f}" height="19" rx="9" fill="{color}"/><text x="{165+width:.1f}" y="{yy+15}" class="bar-value">{pct(value)}</text>')
        for value, yy, color in [(npre,y,'#B9DCCF'),(npost,y+28,GREEN)]:
            width=value/.5*360
            out.append(f'<rect x="650" y="{yy}" width="{width:.1f}" height="19" rx="9" fill="{color}"/><text x="{655+width:.1f}" y="{yy+15}" class="bar-value">{pct(value)}</text>')
    out.append('<text x="160" y="445" class="axis">浅色：上线前；深色：上线后。不同报告窗口/口径不能把两列视为严格互补。</text></svg>')
    return ''.join(out)


def svg_timeline(timeline: list[dict[str,str]]) -> str:
    colors={"direct":BLUE,"instrument":AMBER,"confounder":RED}
    out=['<svg viewBox="0 0 1040 720" role="img" aria-label="近30天更新时间轴">']
    out.append('<line x1="260" y1="56" x2="260" y2="635" stroke="#C9DBEA" stroke-width="5"/>')
    for i,item in enumerate(timeline):
        y=65+i*42
        color=colors[item['kind']]
        out.append(f'<circle cx="260" cy="{y}" r="8" fill="{color}"/><text x="40" y="{y+5}" class="axis">{item["date"]}</text><text x="284" y="{y+5}" class="timeline-text">{esc(item["label"])}</text>')
    out.append('<rect x="70" y="675" width="12" height="12" rx="3" fill="#2378BF"/><text x="90" y="686" class="axis">直接游戏/可用性</text><rect x="290" y="675" width="12" height="12" rx="3" fill="#D99B20"/><text x="310" y="686" class="axis">版本/埋点</text><rect x="490" y="675" width="12" height="12" rx="3" fill="#D85A65"/><text x="510" y="686" class="axis">故障/风控干扰</text></svg>')
    return ''.join(out)


def main() -> None:
    click_json=json.loads((RAW/'lightgame_h5_newuser_click_stats.json').read_text())['sheets'][0]
    columns=click_json['columns']
    rows=[]
    for item in click_json['data']:
        record=dict(zip(columns,item))
        record['date']=serial_to_date(record['日期'])
        rows.append(record)
    rows.sort(key=lambda r:r['date'])
    pre=[r for r in rows if date(2026,5,1)<=r['date']<=date(2026,5,10)]
    post=[r for r in rows if date(2026,5,12)<=r['date']<=date(2026,5,17)]
    pre_rate=sum(r['事件用户数'] for r in pre)/sum(r['新增人数'] for r in pre)
    post_rate=sum(r['事件用户数'] for r in post)/sum(r['新增人数'] for r in post)

    timeline=[
        {'date':'07/14','label':'Limbo 9008 上线','kind':'direct'},
        {'date':'07/15','label':'Limbo 9008 下线','kind':'confounder'},
        {'date':'07/16','label':'Limbo 恢复；传音包激活、注册/首充上报完善','kind':'instrument'},
        {'date':'07/20','label':'Aviator 维护下线','kind':'confounder'},
        {'date':'07/21','label':'Aviator 恢复；配套短信/站内信触达','kind':'confounder'},
        {'date':'07/23','label':'H5 2.1.14、App 2.16；Keno 上线','kind':'instrument'},
        {'date':'07/26','label':'risk 配置修复 501/502 刷子问题','kind':'confounder'},
        {'date':'07/27','label':'KYC 首充带币门槛 900→500；体彩故障4小时','kind':'confounder'},
        {'date':'07/28','label':'risk 配置增加，解决 501 等问题','kind':'confounder'},
        {'date':'07/29','label':'Color Dice 9003 上线','kind':'direct'},
        {'date':'07/30','label':'Tada 世界杯游戏页签与 Banner 关闭','kind':'confounder'},
        {'date':'08/06','label':'Opera 渠道 H5 注册/埋点自动上报','kind':'instrument'},
        {'date':'08/11','label':'App 2.17；iOS Firebase；上线8个 Tada 游戏','kind':'instrument'},
        {'date':'08/12','label':'sbsz4 悬空资产核心逻辑（游戏对接未发）','kind':'confounder'},
    ]
    source_registry=[
        {'source':'H5新注册用户点击行为统计','type':'Sheet','window':'2026-05-01—05-17','use':'入口点击历史基线','status':'已复算','url':'https://ksg964l11fam.sg.larksuite.com/wiki/LgpHwtqsBilsDukZWrxlJ9ctgIb'},
        {'source':'轻量化游戏新注册玩家非0局游戏人数分析','type':'Docx','window':'2026-05-01—05-17','use':'非0局与深度参与历史判断','status':'已复核正文','url':'https://ksg964l11fam.sg.larksuite.com/wiki/BrNEwQyZviJ2gLkf0JYll4Gagdf'},
        {'source':'轻量化游戏上线前后0局玩家占比变化分析','type':'Docx','window':'2026-05-01—05-15','use':'首局门槛历史判断','status':'已复核正文','url':'https://ksg964l11fam.sg.larksuite.com/wiki/UWFpwiDtQi8TRYkRhqYllmjqgSc'},
        {'source':'轻量化游戏分析结论','type':'Docx','window':'2026-05','use':'历史解释与产品假设','status':'结论与源表数值需二次对账','url':'https://ksg964l11fam.sg.larksuite.com/wiki/KDbAwMRXTiI8Uxk5mTClBNiGgad'},
        {'source':'更新记录·新包','type':'Sheet','window':'2026-07-14—08-12','use':'近30天变更/干扰时间轴','status':'已完整读取A1:D389','url':'https://ksg964l11fam.sg.larksuite.com/sheets/KmZcs6cdMhd6MQtHRDgl9jTNg5c?sheet=0owUxS'},
        {'source':'轻量化游戏标准 V1.2','type':'Docx','window':'生效 2026-08-12','use':'性能与资源验收标准','status':'已复核正文','url':'https://ksg964l11fam.sg.larksuite.com/wiki/HpNOwkIqliWq6ckZE9clfeXdg4b'},
        {'source':'COLOR GAME游戏 / AI数值分析','type':'Docx','window':'历史设计','use':'RTP、结算与数值观测','status':'机制已读，线上结果待取数','url':'https://ksg964l11fam.sg.larksuite.com/wiki/JPg2whFxXih8KikLUgblPzxjgOQ'},
        {'source':'JADE游戏改造 / 统一逻辑','type':'Docx','window':'历史设计','use':'未付费限制、资产/弹窗/引导观测','status':'机制已读，线上结果待取数','url':'https://ksg964l11fam.sg.larksuite.com/wiki/EzqQw504UiUC7UkFQTslUbJugSg'},
    ]
    payload={
        'generated_at':'2026-08-18',
        'scope':{'history':'2026-05-01—05-17','recent_change_window':'2026-07-14—2026-08-12'},
        'click':{'pre_rate':pre_rate,'post_rate':post_rate,'delta_pp':(post_rate-pre_rate)*100,'pre_new':sum(r['新增人数'] for r in pre),'post_new':sum(r['新增人数'] for r in post),'daily':[{'date':r['date'].isoformat(),'click_rate':r['点击用户占比'],'new_users':r['新增人数'],'click_users':r['事件用户数']} for r in rows]},
        'timeline':timeline,
        'source_registry':source_registry,
        'data_gaps':['近30天未发现可按 game_id×版本×端×渠道下钻的行为、性能、结算与付费事实表。','更新记录是变更日志，不是用户表现数据，不能用于证明上线效果。','历史“轻量化效果显著成功”与“入口兴趣下降”结论来自不同口径/窗口，必须统一重算。']
    }
    OUT_DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2))

    click_png=save_click_png(rows,pre,post)
    channel_png=save_channel_png()
    timeline_png=save_timeline_png(timeline)

    sources=''.join(f'<tr><td>{esc(x["source"])}</td><td>{esc(x["type"])}</td><td>{esc(x["window"])}</td><td>{esc(x["use"])}</td><td><span class="status">{esc(x["status"])}</span></td></tr>' for x in source_registry)
    events=''.join(f'<div class="event {x["kind"]}"><div class="event-date">{x["date"]}</div><div>{esc(x["label"])}</div></div>' for x in timeline)
    html_doc=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Waje 轻量化游戏：历史盘点与近30天专题分析框架</title>
<style>
:root{{--navy:{NAVY};--blue:{BLUE};--green:{GREEN};--amber:{AMBER};--red:{RED};--muted:{MUTED};--line:{GRID};--canvas:#F3F8FC;--paper:#FFF;--ink:#193852}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--canvas);color:var(--ink);font:16px/1.72 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif}}.hero{{padding:58px max(24px,calc((100% - 1240px)/2));background:linear-gradient(125deg,#10385C,#1D6FAD 62%,#4EB28A);color:#fff}}.eyebrow{{font-size:12px;letter-spacing:.18em;opacity:.8}}h1{{font-size:clamp(34px,5vw,58px);line-height:1.12;letter-spacing:-.04em;margin:14px 0}}.lead{{max-width:900px;font-size:18px;margin:0;opacity:.96}}.meta{{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}}.meta span{{border:1px solid rgba(255,255,255,.36);border-radius:99px;padding:4px 10px;font-size:12px}}.layout{{display:grid;grid-template-columns:215px minmax(0,1fr);gap:28px;max-width:1240px;margin:0 auto;padding:30px 20px 80px}}.toc{{position:sticky;top:18px;height:max-content;padding:10px}}.toc b{{font-size:12px;letter-spacing:.12em;color:var(--muted)}}.toc a{{display:block;color:var(--muted);text-decoration:none;font-size:13px;padding:7px 10px;border-left:2px solid transparent}}.toc a:hover{{border-left-color:var(--blue);background:#EAF5FE;color:var(--blue)}}main{{background:var(--paper);border:1px solid var(--line);border-radius:24px;padding:clamp(24px,5vw,62px);box-shadow:0 18px 48px rgba(19,58,94,.09)}}section{{margin-top:54px;scroll-margin-top:24px}}section:first-child{{margin-top:0}}h2{{font-size:28px;line-height:1.22;letter-spacing:-.03em;margin:0 0 12px}}h3{{font-size:19px;margin:22px 0 8px}}p{{margin:0 0 13px}}.muted{{color:var(--muted)}}.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0}}.kpi{{padding:16px;border:1px solid var(--line);border-radius:16px;background:#FBFDFF}}.kpi small{{display:block;color:var(--muted)}}.kpi b{{display:block;font-size:30px;line-height:1.2;margin:5px 0;color:var(--navy)}}.kpi.warning b{{color:#A66B03}}.kpi.red b{{color:var(--red)}}.callout{{margin:18px 0;padding:16px 18px;border-left:5px solid var(--blue);border-radius:0 14px 14px 0;background:#EEF7FE}}.callout.warn{{background:#FFF8E8;border-color:var(--amber)}}.callout.risk{{background:#FFF0F2;border-color:var(--red)}}.callout.ok{{background:#EFFAF4;border-color:var(--green)}}.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.chart{{border:1px solid var(--line);border-radius:16px;padding:14px;margin:18px 0;background:linear-gradient(150deg,#FCFEFF,#F5FAFE)}}.chart figcaption{{display:flex;justify-content:space-between;gap:18px;margin:0 2px 6px}}.chart figcaption b{{font-size:16px}}.chart figcaption span{{font-size:12px;color:var(--muted);text-align:right}}svg{{width:100%;height:auto;display:block}}.gridline{{stroke:#DDEAF4;stroke-width:1}}.axis{{font:12px "PingFang SC",sans-serif;fill:#58718A}}.event-label{{font:12px "PingFang SC",sans-serif;fill:#A66B03;font-weight:700}}.summary-label{{font:13px "PingFang SC",sans-serif;fill:#3D5C76}}.summary-number{{font-weight:700;fill:#173A5E}}.warning{{fill:#A66B03}}.line-blue{{fill:none;stroke:{BLUE};stroke-width:4}}.chart-title{{font:15px "PingFang SC",sans-serif;fill:#173A5E;font-weight:700}}.bar-label{{font:13px "PingFang SC",sans-serif;fill:#173A5E}}.bar-value{{font:12px "PingFang SC",sans-serif;fill:#173A5E;font-weight:700}}.timeline-text{{font:13px "PingFang SC",sans-serif;fill:#294B67}}.event-list{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:14px}}.event{{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--line);border-left:4px solid var(--blue);border-radius:10px;padding:9px 10px;font-size:13px}}.event.instrument{{border-left-color:var(--amber)}}.event.confounder{{border-left-color:var(--red)}}.event-date{{min-width:44px;color:var(--muted);font-weight:700}}table{{width:100%;border-collapse:collapse;font-size:13px;margin:16px 0}}.scroll{{overflow:auto;border:1px solid var(--line);border-radius:14px}}th{{text-align:left;background:#EDF6FC;padding:10px;color:#1A587F;white-space:nowrap}}td{{padding:10px;border-top:1px solid var(--line);vertical-align:top}}tr:nth-child(even) td{{background:#FBFDFF}}.status{{display:inline-block;font-size:11px;padding:2px 7px;border-radius:20px;background:#EAF4FB;color:#2C6A91}}.flow{{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin:18px 0}}.node{{padding:10px 12px;border-radius:12px;background:#EEF7FE;border:1px solid #C7E0F3;font-size:13px;font-weight:700}}.arrow{{color:#7C9BB1;font-size:20px}}.pill{{display:inline-block;padding:3px 9px;border-radius:30px;font-size:12px;font-weight:700}}.pill.p0{{background:#FFE5E8;color:#B63A49}}.pill.p1{{background:#FFF1D5;color:#9B6500}}.pill.p2{{background:#E5F5EB;color:#24704D}}.priority td:first-child{{width:72px}}.footer{{max-width:1240px;margin:0 auto 30px;color:var(--muted);font-size:12px;padding:0 20px}}@media(max-width:900px){{.layout{{display:block;padding:16px 12px 50px}}.toc{{position:relative;top:auto;margin-bottom:14px;border:1px solid var(--line);border-radius:13px;background:#fff}}.toc a{{display:inline-block;border-left:0}}main{{padding:22px 16px;border-radius:17px}}.kpis{{grid-template-columns:repeat(2,1fr)}}.grid2,.event-list{{grid-template-columns:1fr}}.hero{{padding:42px 20px}}}}@media print{{body{{background:#fff}}.hero{{padding:30px}}.layout{{display:block;padding:0}}.toc{{display:none}}main{{box-shadow:none;border:0;border-radius:0}}section{{break-inside:avoid}}}}
</style></head><body>
<header class="hero"><div class="eyebrow">WAJE · LIGHTWEIGHT GAMES · DATA INVENTORY</div><h1>轻量化游戏：历史数据盘点<br>与近30天专题分析框架</h1><p class="lead">以更新记录为变更时间轴、以历史点击/0局/非0局数据为基线。结论先说明数据能证明什么，也明确说明当前无法证明什么。</p><div class="meta"><span>近30天变更：2026-07-14—08-12</span><span>历史行为基线：2026-05-01—05-17</span><span>数据来源：飞书 API</span><span>生成：2026-08-18</span></div></header>
<div class="layout"><aside class="toc"><b>报告导航</b><a href="#summary">核心结论</a><a href="#current">近30天变更</a><a href="#history">历史复算与矛盾</a><a href="#framework">专题分析框架</a><a href="#dashboard">看板与埋点</a><a href="#actions">P0/P1/P2行动</a><a href="#sources">来源与边界</a></aside><main>
<section id="summary"><h2>1. 核心结论：先区分事实、问题和下一步</h2><p class="muted">本报告不是“轻量化成功/失败”的单一结论。近30天已有连续上线与版本变更，但尚无可归因的近30天游戏表现事实表。</p><div class="kpis"><article class="kpi"><small>近30天更新记录</small><b>14</b><span>条变更，覆盖游戏、版本、埋点、风控与运营</span></article><article class="kpi"><small>游戏/可用性节点</small><b>8</b><span>Limbo、Aviator、Keno、Color Dice 与页面调整</span></article><article class="kpi warning"><small>5月历史点击率</small><b>{pct(pre_rate)} → {pct(post_rate)}</b><span>上线后加权口径 {pp(post_rate-pre_rate)}</span></article><article class="kpi red"><small>当前关键缺口</small><b>0</b><span>张近30天 game_id×版本×端×渠道表现事实表</span></article></div><div class="callout risk"><b>当前最重要的问题不是“缺一个游戏指标”，而是变更和结果没有同表关联。</b> 7月14日至8月12日期间至少发生 Limbo 上/下线、Keno/Color Dice 上线、H5/App版本更新、Opera埋点接入、风控和KYC配置变化。没有 <code>game_id + version + config_version + channel + event_time</code> 的事实数据，任何“某次上线带来提升/下滑”的判断都不成立。</div><div class="grid2"><div class="callout"><b>历史事实</b><br>直接复算的 H5 入口点击率从 <b>{pct(pre_rate)}</b> 下降到 <b>{pct(post_rate)}</b>；标准H5的0局率由81.29%升至81.77%。历史改造没有解决标准H5的首局门槛。</div><div class="callout warn"><b>待验证假设</b><br>Keno、Color Dice、Limbo 等新小游戏可能改善“首局后持续玩”，但当前数据尚不能区分入口吸引力、加载问题、流量质量、游戏规则和版本变化的影响。</div></div></section>
<section id="current"><h2>2. 近30天：变更密度高，先建立可比较的事件时间轴</h2><p>更新时间窗按最新记录 8月12日回溯30天。以下事件不是效果结论，而是所有后续数据对比的切点与干扰项。</p><figure class="chart"><figcaption><b>更新记录时间轴</b><span>蓝：直接游戏/可用性；黄：版本或埋点；红：故障、风控或运营干扰</span></figcaption>{svg_timeline(timeline)}</figure><div class="event-list">{events}</div><div class="callout warn"><b>分析规则：</b>每个切点至少比较“切点前7天 / 后7天”，并同时保留端、包体、渠道、游戏和用户分层；7月23日版本、7月27日KYC门槛、8月6日Opera埋点、8月11日App 2.17 都必须作为协变量或分层条件，不得混入游戏上线效果。</div></section>
<section id="history"><h2>3. 历史复算：方向明确，但历史报告之间存在口径冲突</h2><p>直接读取并复算《H5新注册用户点击行为统计》A1:N18。正式历史基线使用“点击用户数 ÷ 新增人数”的新增人数加权口径，5月11日当天不进入前后比较。</p><figure class="chart"><figcaption><b>H5新注册用户游戏入口点击率</b><span>样本：上线前10日 vs 上线后6日；分母为每日新增人数</span></figcaption>{svg_click(rows,pre_rate,post_rate)}</figure><div class="grid2"><div><h3>直接复算结论</h3><ul><li>上线前：77,199 点击用户 / 155,034 新增，<b>{pct(pre_rate)}</b>。</li><li>上线后：45,418 点击用户 / 115,404 新增，<b>{pct(post_rate)}</b>。</li><li>差异：<b>{pp(post_rate-pre_rate)}</b>；事件次数/点击用户基本稳定在约4.7次，主要问题不在重复点击频次。</li></ul></div><div><h3>为什么与历史文字不完全一致</h3><ul><li>历史结论页写的是 52%—58% 与45%—49%，与当前源表复算值不同。</li><li>另有 CoinFlip 效果复盘声称新增、留存和生态扩散改善，但大量关键数值嵌在独立表格中，未与点击/0局的同一 cohort 对齐。</li><li>结论方向可作为假设保留，数值必须以本次重算和未来统一事实表为准。</li></ul></div></div><figure class="chart"><figcaption><b>0局与非0局历史快照</b><span>来源页面的不同窗口；用于识别首局门槛，不作为严格互补漏斗</span></figcaption>{svg_history_bars()}</figure><div class="callout risk"><b>可确认的历史问题：</b>标准H5 0局率长期在80%+，轻量化上线后并未下降；PWW出现上线当天短期改善但随后回升；WajeBet H5用户意图高、整体稳定。后续专题应把“入口点击、加载成功、首局开始、首局完成”连成同一用户漏斗，而不是分别查看三个比例。</div></section>
<section id="framework"><h2>4. 近30天专题分析框架：以变更为入口，以用户级漏斗为结果</h2><div class="flow"><span class="node">注册 cohort</span><span class="arrow">→</span><span class="node">游戏入口曝光</span><span class="arrow">→</span><span class="node">点击</span><span class="arrow">→</span><span class="node">加载/可下注</span><span class="arrow">→</span><span class="node">首局开始</span><span class="arrow">→</span><span class="node">首局完成</span><span class="arrow">→</span><span class="node">2–3局 / 11局+</span><span class="arrow">→</span><span class="node">留存 / 首付 / 复充</span></div><table><thead><tr><th>分析域</th><th>关键问题</th><th>最小指标</th><th>必须切片</th></tr></thead><tbody><tr><td>入口与首局</td><td>用户在哪里放弃？</td><td>曝光率、点击率、加载成功率、可下注率、首局开始/完成率</td><td>游戏、端、包体、渠道、设备档位、网络、版本</td></tr><tr><td>参与深度</td><td>轻量化是否带来持续玩？</td><td>2–3局率、11局+率、会话时长、跨游戏率</td><td>游戏、cohort、首局结果、免费/付费状态</td></tr><tr><td>商业化与资产</td><td>免费引导是否转为价值？</td><td>首付率、复充率、有效投注、RTP、退款/异常结算</td><td>游戏、规则/配置、用户分层、资产状态</td></tr><tr><td>性能与可靠性</td><td>低端机/弱网是否导致流失？</td><td>game_ready、bet_ready P75/P90、白屏、错误、重试、首局失败</td><td>设备、网络、浏览器、H5 build、CDN/地区</td></tr><tr><td>版本与配置</td><td>改动是否有效、有没有副作用？</td><td>切点前后变化、样本量、置信区间、数据可用率</td><td>game_id、app/h5版本、config_version、渠道、事件日期</td></tr></tbody></table><div class="callout ok"><b>统一主键：</b><code>user_id</code>、<code>session_id</code>、<code>game_id</code>、<code>round_id</code>、<code>event_uid</code>、<code>event_version</code>、<code>server_ts</code>、<code>app_version</code>、<code>h5_build</code>、<code>config_version</code>、<code>channel</code>。其中 <code>game_id + build + config_version</code> 是将更新记录与效果数据挂钩的最低条件。</div></section>
<section id="dashboard"><h2>5. 看板与埋点：先让每次上线都可验证</h2><div class="grid2"><div><h3>产品健康首页（≤10个指标）</h3><ol><li>新增游戏用户</li><li>入口点击率</li><li>加载成功率</li><li>可下注率</li><li>首局完成率</li><li>2–3局率</li><li>11局+率</li><li>成熟D1/D7留存</li><li>首付率</li><li>数据可用率</li></ol></div><div><h3>更新记录自动纳入方式</h3><ol><li>每次专题分析先读取“更新记录”近30天窗口。</li><li>每条变更登记生效时间、端/包体、游戏、版本、配置、预期指标与干扰项。</li><li>看板的日期切片自动标注上线、下线、故障和埋点口径变更。</li><li>若没有完整7天成熟窗口，只展示趋势，不发布效果结论。</li></ol></div></div><table><thead><tr><th>事件/事实表</th><th>新增字段</th><th>解决的问题</th></tr></thead><tbody><tr><td>入口与加载</td><td><code>game_entry_view/click</code>、<code>game_load_start/success/fail</code>、<code>load_ms</code>、<code>error_code</code></td><td>区分入口不吸引、加载失败与主动退出</td></tr><tr><td>对局</td><td><code>game_ready</code>、<code>bet_ready</code>、<code>round_start/end</code>、<code>round_id</code>、<code>result</code></td><td>证明首局和深度参与，而不是只看0局</td></tr><tr><td>性能</td><td><code>device_tier</code>、<code>network</code>、<code>browser</code>、<code>h5_build</code>、P75/P90</td><td>定位低端机、弱网、白屏和长加载</td></tr><tr><td>配置与商业化</td><td><code>config_version</code>、<code>rule_version</code>、<code>payment_status</code>、<code>bet_id</code>、<code>settlement_status</code></td><td>重建上线效果、RTP/资产与首充引导闭环</td></tr></tbody></table></section>
<section id="actions"><h2>6. 可执行行动：按数据闭环排优先级</h2><div class="scroll"><table class="priority"><thead><tr><th>级别</th><th>问题</th><th>立即动作</th><th>验证指标</th><th>护栏与周期</th></tr></thead><tbody><tr><td><span class="pill p0">P0</span></td><td>近30天多个游戏/版本切点没有效果事实表</td><td>建立“更新记录—游戏/版本/配置—数据窗口”事件登记；Keno、Color Dice、Limbo、Aviator逐项绑定 game_id/build。</td><td>每条变更均有前后7天样本量、首局完成、深度参与、数据可用率。</td><td>未成熟窗口只标趋势；上线后D7再复盘。</td></tr><tr><td><span class="pill p0">P0</span></td><td>标准H5前链路历史流失严重</td><td>补齐曝光→点击→加载→可下注→首局的用户级事件，首批覆盖Color Dice、Keno、Limbo。</td><td>加载成功率、可下注率、首局开始/完成率；按低端机与弱网拆分。</td><td>不以点击人数替代点击率；两周内完成事件验收。</td></tr><tr><td><span class="pill p1">P1</span></td><td>新小游戏上线密集，可能互相稀释流量</td><td>建立游戏×入口×渠道贡献矩阵，追踪跨游戏率和新游戏首局用户来源。</td><td>游戏间迁移率、2–3局率、11局+率、CoinFlip/轻量游戏生态扩散率。</td><td>按用户去重；避免同一用户多游戏重复计入新增。</td></tr><tr><td><span class="pill p1">P1</span></td><td>资源标准已发布但性能效果未联动</td><td>把asset-budget.json、performance-report.json与 game_id、commit_id、H5 build 入库关联。</td><td>bet_ready P75/P90、核心资源bytes、白屏/错误、首局完成率。</td><td>资源合格不等于体验合格；每个必测环境10次冷启动。</td></tr><tr><td><span class="pill p2">P2</span></td><td>免费用户限制与首充引导可能改变玩法行为</td><td>记录未付费限制命中、Toast/弹窗曝光、点击、提现/充值结果及资产状态。</td><td>引导曝光→充值转化、异常结算、RTP偏差、客服/投诉率。</td><td>不降低风控/幂等/审计能力；规则版本独立复盘。</td></tr></tbody></table></div></section>
<section id="sources"><h2>7. 来源、数据边界与使用说明</h2><div class="callout warn"><b>数据边界：</b>更新记录可说明“发生了什么”，不能说明“用户表现如何”；5月历史表可说明历史基线，不能代替7月/8月的当前效果。当前正式结论是“近30天变更多、且缺少统一效果数据”，不是“近30天效果差”。</div><div class="scroll"><table><thead><tr><th>来源</th><th>类型</th><th>统计窗口</th><th>用途</th><th>状态</th></tr></thead><tbody>{sources}</tbody></table></div><p class="muted">数据快照已保存：<code>data/raw/lark/2026-08-18/lightgame_h5_newuser_click_stats.json</code> 与 <code>data/raw/lark/2026-08-18/waje_update_log_new_package.json</code>。报告只使用聚合数据，不含用户、订单、设备或资产明细。</p></section>
</main></div><footer class="footer">Waje 数据产品分析 · 飞书 API 来源拉取 · 2026-08-18</footer></body></html>'''
    OUT_HTML.parent.mkdir(parents=True,exist_ok=True)
    OUT_HTML.write_text(html_doc)
    markdown=f'''# Waje 轻量化游戏：历史数据盘点与近30天专题分析框架

生成日期：2026-08-18。数据源通过飞书 API 拉取。

## 核心判断

- 近30天（2026-07-14—08-12）更新记录中有14条相关变更；直接游戏/可用性事件包括 Limbo 9008、Aviator、Keno、Color Dice 9003 及页面调整。
- 变更日志不能替代效果数据。当前没有可按 `game_id × version × 端 × 渠道` 下钻的近30天行为、性能、结算或付费事实表，不能把某次上线与数据变化直接归因。
- 5月历史点击源表复算：上线前 77,199/155,034 = {pct(pre_rate)}；上线后 45,418/115,404 = {pct(post_rate)}，变化 {pp(post_rate-pre_rate)}。
- 历史0局数据：标准H5由81.29%升至81.77%；PWW由61.71%升至61.88%；WajeBet H5由63.63%升至63.73%。轻量化当时未稳定降低首局门槛。

## 近30天事件与分析规则

{chr(10).join(f'- {x["date"]}：{x["label"]}' for x in timeline)}

所有变更按前7天/后7天比较，并分端、包体、渠道、游戏、版本、配置和用户分层。若未获得完整成熟窗口，仅记录趋势，不发布上线效果结论。

## 专题框架

`注册 → 曝光 → 点击 → 加载/可下注 → 首局开始 → 首局完成 → 2–3局/11局+ → D1/D7 → 首付/复充`

必备关联键：`user_id`、`session_id`、`game_id`、`round_id`、`event_uid`、`server_ts`、`app_version`、`h5_build`、`config_version`、`channel`。

## P0

1. 将更新记录中的游戏上线、版本、配置与故障登记为标准事件表，并和各事实表通过 `game_id + build + config_version` 关联。
2. 覆盖 Color Dice、Keno、Limbo 的入口→加载→可下注→首局事件；按低端机、弱网、包体、渠道观察。
3. 统一历史点击、0局、非0局的 cohort、分母、窗口与端/包体映射，停止并列引用相互矛盾的历史结论。

## 来源登记

| 来源 | 用途 | 状态 |
|---|---|---|
{chr(10).join(f'| [{x["source"]}]({x["url"]}) | {x["use"]} | {x["status"]} |' for x in source_registry)}
'''
    OUT_MD.parent.mkdir(parents=True,exist_ok=True)
    OUT_MD.write_text(markdown)
    print(json.dumps({'html':str(OUT_HTML),'markdown':str(OUT_MD),'analysis':str(OUT_DATA),'assets':[str(click_png),str(channel_png),str(timeline_png)]},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
