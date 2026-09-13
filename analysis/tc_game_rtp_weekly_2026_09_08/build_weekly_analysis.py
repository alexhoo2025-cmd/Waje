#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
MASTER = PROJECT / "data/outputs/lifecycle_joint/2026-09-07/lark-after/values"
RAW = PROJECT / "data/raw/lifecycle_joint/2026-09-08-report"
OLD_PATH = PROJECT / "analysis/tc_game_rtp_tracking_2026_09_02/build_tracking_report.py"
TC_PATH = ROOT / "sources/metabase_tc_daily_2026-08-25_2026-09-07.csv"
CHANNEL_PATH = ROOT / "sources/metabase_tc_channels_top7_2026-08-25_2026-09-07.csv"
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
COLORS = {"blue": "#2F6FBE", "gold": "#BD8538", "green": "#25846E", "purple": "#7B6DB2", "red": "#B4534B", "ink": "#17324D", "muted": "#60748A", "grid": "#DCE8F0"}
PREV = (date(2026, 8, 25), date(2026, 8, 31))
CURR = (date(2026, 9, 1), date(2026, 9, 7))
TREND = (date(2026, 8, 26), date(2026, 9, 7))
NEW_GAMES = {"Hilo": {"launch": date(2026, 8, 21), "game_id": "9011"}, "Plinko": {"launch": date(2026, 8, 21), "game_id": "9016"}, "Tower": {"launch": date(2026, 8, 25), "game_id": "9013"}}

spec = importlib.util.spec_from_file_location("old_tracking", OLD_PATH)
old = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(old)


def compact(v: object) -> str:
    return str(v).replace("\n", "").replace(" ", "")


def source_records(path: Path, kind: str, day: date) -> list[dict]:
    frame = pd.read_excel(path)
    frame.columns = [compact(c) for c in frame.columns]
    output = []
    for raw in frame.to_dict("records"):
        raw["日期"] = day
        if kind in {"game", "detail"}:
            raw["游戏"] = old.canonical_game(raw.get("游戏") or raw.get("游戏类型"))
        output.append(raw)
    return output


def read_game_rows() -> list[dict]:
    records = old.annotated_rows(MASTER / "aIE757.json")
    by_key = {(r["日期"], old.canonical_game(r.get("游戏"))): old.game_row(r) for r in records}
    for day, folder in [(date(2026, 9, 3), "2026-09-03"), (date(2026, 9, 7), "2026-09-07-independent")]:
        for r in source_records(RAW / folder / "game.xlsx", "game", day):
            by_key[(day, r["游戏"])] = old.game_row(r)
    return sorted(by_key.values(), key=lambda r: (r["date"], r["game"]))


def detail_row(r: dict) -> dict | None:
    life = str(r.get("生命周期") or "").strip()
    if life not in {"1", "2", "3", "4"}:
        return None
    return {
        "date": r["日期"], "game": old.canonical_game(r.get("游戏") or r.get("游戏类型")), "lifecycle": int(life),
        "base_bet": old.number(r.get("基础下注额")) or 0.0,
        "base_actual_profit": old.number(r.get("基础实际盈利")),
        "complete_bet": old.number(r.get("完全下注额")) or 0.0,
        "complete_expected_profit": old.number(r.get("完全预期盈利")),
        "complete_actual_profit": old.number(r.get("完全实际盈利")),
        "complete_expected_return": old.number(r.get("预期回报比")),
        "bankruptcy": old.number(r.get("总破产保护金额")) or 0.0,
        "personal_control": old.number(r.get("总个人盈利控制金额")) or 0.0,
    }


def read_detail_rows() -> list[dict]:
    records = old.annotated_rows(MASTER / "wjhify.json")
    converted = [detail_row(r) for r in records]
    by_key = {(r["date"], r["lifecycle"], r["game"]): r for r in converted if r}
    for day, folder in [(date(2026, 9, 3), "2026-09-03"), (date(2026, 9, 7), "2026-09-07-independent")]:
        for raw in source_records(RAW / folder / "detail.xlsx", "detail", day):
            r = detail_row(raw)
            if r:
                by_key[(r["date"], r["lifecycle"], r["game"])] = r
    return sorted(by_key.values(), key=lambda r: (r["date"], r["lifecycle"], r["game"]))


def aggregate_by_game(rows: list[dict], start: date, end: date) -> tuple[list[dict], dict]:
    selected = [r for r in rows if start <= r["date"] <= end and r["complete_bet"] > 0]
    groups = defaultdict(list)
    for r in selected:
        groups[r["game"]].append(r)
    result = [{"game": g, **old.aggregate(v)} for g, v in groups.items()]
    result.sort(key=lambda r: r["complete_bet"], reverse=True)
    return result, old.aggregate(selected)


def index_by_game(rows: list[dict]) -> dict[str, dict]:
    return {r["game"]: {**r, "rank": i + 1} for i, r in enumerate(rows)}


def pct(v: float | None, d=2) -> str:
    return "N/A" if v is None else f"{v*100:.{d}f}%"


def pp(v: float | None, d=2) -> str:
    return "N/A" if v is None else f"{v:+.{d}f}pp"


def amount(v: float | None) -> str:
    return old.amount(v)


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_PATH, size=size, index=1 if bold else 0)


def canvas(title: str, subtitle: str, width=1600, height=900):
    image = Image.new("RGB", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    draw.text((60, 40), title, fill=COLORS["ink"], font=font(34, True))
    draw.text((60, 95), subtitle, fill=COLORS["muted"], font=font(18))
    return image, draw


def save_image(image: Image.Image, name: str) -> str:
    path = ASSETS / name
    image.save(path, "PNG", optimize=True)
    return str(path.relative_to(PROJECT))


def line_points(draw, rows, key, box, low, high, color, dashed=False):
    left, top, right, bottom = box
    pts=[]
    for i,r in enumerate(rows):
        val=r.get(key)
        if val is None: continue
        x=left+(right-left)*i/max(1,len(rows)-1); y=bottom-(bottom-top)*(val-low)/(high-low)
        pts.append((i,r,x,y))
    for a,b in zip(pts,pts[1:]):
        if dashed:
            for k in range(0,20,2):
                t1=k/20;t2=min(1,(k+1)/20);draw.line((a[2]+(b[2]-a[2])*t1,a[3]+(b[3]-a[3])*t1,a[2]+(b[2]-a[2])*t2,a[3]+(b[3]-a[3])*t2),fill=color,width=3)
        else: draw.line((a[2],a[3],b[2],b[3]),fill=color,width=4)
    if not dashed:
        for _,_,x,y in pts: draw.ellipse((x-5,y-5,x+5,y+5),fill=color)
    return pts


def chart_tc(tc_rows):
    rows=[r for r in tc_rows if TREND[0]<=r["date"]<=TREND[1]]; image,draw=canvas("全产品TC日趋势","8月26日—9月7日完整自然日；TC=成功提现÷成功现金充值。")
    left,top,right,bottom=130,180,1520,700;vals=[r["tc"] for r in rows];low=min(vals)-.012;high=max(vals)+.012
    for i in range(5):
        v=low+(high-low)*i/4;y=bottom-(bottom-top)*i/4;draw.line((left,y,right,y),fill=COLORS["grid"],width=2);draw.text((45,y-12),f"{v:.0%}",fill=COLORS["muted"],font=font(17))
    line_points(draw,rows,"tc",(left,top,right,bottom),low,high,COLORS["blue"])
    for i,r in enumerate(rows):
        x=left+(right-left)*i/(len(rows)-1);y=bottom-(bottom-top)*(r["tc"]-low)/(high-low);draw.text((x-26,y-34),f"{r['tc']:.1%}",fill=COLORS["ink"],font=font(14,True));draw.text((x-22,bottom+24),r["date"].strftime("%m/%d"),fill=COLORS["muted"],font=font(14))
    return save_image(image,"01_全产品TC日趋势_0826_0907.png")


def horizontal_delta(title, subtitle, rows, label_key, value_key, name):
    image,draw=canvas(title,subtitle,1600,920);left,top,right,bottom=430,170,1450,830;maxabs=max(abs(r[value_key]) for r in rows)*1.25;zero=(left+right)/2
    draw.line((zero,top,zero,bottom),fill=COLORS["ink"],width=2)
    step=(bottom-top)/len(rows)
    for i,r in enumerate(rows):
        y=top+i*step+step*.18;v=r[value_key];x=zero+(right-left)/2*v/maxabs;color=COLORS["green"] if v>=0 else COLORS["red"]
        draw.text((40,y+6),str(r[label_key]),fill=COLORS["ink"],font=font(18));draw.rectangle((min(zero,x),y,max(zero,x),y+step*.48),fill=color);draw.text((x+10 if v>=0 else x-105,y+5),f"{v:+.2f}pp",fill=COLORS["ink"],font=font(17,True))
    return save_image(image,name)


def chart_channels(channels): return horizontal_delta("Top 7渠道TC周变化","9月1日—7日减8月25日—31日；正值表示TC上升。",sorted(channels,key=lambda r:r["tc_change_pp"]),"channel","tc_change_pp","02_Top7渠道TC周变化.png")


def chart_scatter(current):
    rows=[r for r in current if r["rtp_gap_pp"] is not None];image,draw=canvas("本周游戏RTP偏离与下注规模","横轴=实际RTP - 预期RTP；纵轴=完全下注额（对数刻度）。",1700,950);left,top,right,bottom=180,180,1550,760
    xs=[r["rtp_gap_pp"] for r in rows];ys=[math.log10(r["complete_bet"]) for r in rows];xmin,xmax=min(xs)-1,max(xs)+1;ymin,ymax=min(ys)-.2,max(ys)+.2
    zero=left+(right-left)*(0-xmin)/(xmax-xmin);draw.line((zero,top,zero,bottom),fill=COLORS["ink"],width=2)
    for i in range(5): y=bottom-(bottom-top)*i/4;draw.line((left,y,right,y),fill=COLORS["grid"],width=2);draw.text((45,y-10),amount(10**(ymin+(ymax-ymin)*i/4)),fill=COLORS["muted"],font=font(15))
    by_gap=sorted(rows,key=lambda r:r["rtp_gap_pp"])
    labels=set(r["game"] for r in sorted(rows,key=lambda r:r["complete_bet"],reverse=True)[:10])
    labels.update(r["game"] for r in by_gap[:3]+by_gap[-3:] if abs(r["rtp_gap_pp"])>=3)
    for r,yv in zip(rows,ys):
        x=left+(right-left)*(r["rtp_gap_pp"]-xmin)/(xmax-xmin);y=bottom-(bottom-top)*(yv-ymin)/(ymax-ymin)
        point_color=COLORS["green"] if r["rtp_gap_pp"]>=0 else COLORS["red"]
        draw.ellipse((x-8,y-8,x+8,y+8),fill=point_color,outline="#FFFFFF")
        if r["game"] in labels:
            label=f'{r["game"]} {r["rtp_gap_pp"]:+.2f}pp'
            bbox=draw.textbbox((0,0),label,font=font(14,True));tw=bbox[2]-bbox[0];th=bbox[3]-bbox[1]
            tx=x+11 if x<right-250 else x-tw-11
            ty=y+10 if y<top+45 else y-th-12
            draw.rounded_rectangle((tx-4,ty-2,tx+tw+4,ty+th+2),radius=5,fill="#FFFFFF",outline=COLORS["grid"])
            draw.text((tx,ty),label,fill=COLORS["ink"],font=font(14,True))
    draw.text((650,850),"实际RTP - 预期RTP（百分点）",fill=COLORS["ink"],font=font(18,True))
    return save_image(image,"03_本周游戏RTP偏离与下注规模.png")


def chart_share_delta(compare):
    rows=sorted(compare,key=lambda r:max(r["bet_share_prev"],r["bet_share_curr"]),reverse=True)[:12];rows.sort(key=lambda r:r["bet_share_change_pp"])
    return horizontal_delta("头部游戏下注占比周变化","占全部游戏完全下注额的比例；正值表示份额增加。",rows,"game","bet_share_change_pp","04_头部游戏下注占比周变化.png")


def panel_line(draw, title, rows, box, color):
    left,top,right,bottom=box;values=[r["actual_rtp"] for r in rows if r["actual_rtp"] is not None]+[r["expected_rtp"] for r in rows if r["expected_rtp"] is not None];low=max(0,min(values)-.03);high=max(values)+.03
    draw.text((left,top-42),title,fill=color,font=font(22,True))
    for i in range(4): y=bottom-(bottom-top)*i/3;draw.line((left,y,right,y),fill=COLORS["grid"],width=1);draw.text((left-64,y-9),f"{low+(high-low)*i/3:.0%}",fill=COLORS["muted"],font=font(13))
    actual_pts=line_points(draw,rows,"actual_rtp",box,low,high,color);line_points(draw,rows,"expected_rtp",box,low,high,COLORS["gold"],True)
    if actual_pts:
        selected={min(actual_pts,key=lambda p:p[1]["actual_rtp"])[0],max(actual_pts,key=lambda p:p[1]["actual_rtp"])[0],actual_pts[-1][0]}
        for idx,r,x,y in actual_pts:
            if idx not in selected: continue
            label=f'{r["actual_rtp"]:.1%}'
            bbox=draw.textbbox((0,0),label,font=font(13,True));tw=bbox[2]-bbox[0];th=bbox[3]-bbox[1]
            tx=min(right-tw-3,max(left+3,x-tw/2));ty=y+10 if y<top+30 else y-th-12
            draw.rounded_rectangle((tx-3,ty-2,tx+tw+3,ty+th+2),radius=4,fill="#FFFFFF",outline=COLORS["grid"])
            draw.text((tx,ty),label,fill=color,font=font(13,True))


def chart_new_games(new_daily):
    image,draw=canvas("新游戏逐日实际与预期RTP","实线=实际RTP，虚线=预期RTP；上线日至9月7日。",1600,1120);palette=[COLORS["blue"],COLORS["green"],COLORS["purple"]]
    for i,(game,rows) in enumerate(new_daily.items()): panel_line(draw,game,rows,(170,210+i*285,1500,400+i*285),palette[i])
    return save_image(image,"05_新游戏逐日实际与预期RTP.png")


def chart_lifecycle(lifecycle):
    image,draw=canvas("新游戏生命周期RTP偏离","数值为实际RTP减预期RTP；空白表示无可比数据。",1450,650);games=list(NEW_GAMES);cellw,cellh=270,110;left,top=240,180
    for j in range(4): draw.text((left+j*cellw+48,130),f"生命周期{j+1}",fill=COLORS["ink"],font=font(18,True))
    for i,g in enumerate(games):
        draw.text((60,top+i*cellh+38),g,fill=COLORS["ink"],font=font(20,True))
        for j in range(4):
            r=next(x for x in lifecycle if x["game"]==g and x["lifecycle"]==j+1);v=r["rtp_gap_pp"]
            if v is None: bg="#F3F5F7"
            elif v>=3: bg="#D8F3E8"
            elif v>=0: bg="#E7F2FF"
            elif v<=-3: bg="#FDE3E0"
            else: bg="#FFF0E1"
            draw.rectangle((left+j*cellw,top+i*cellh,left+(j+1)*cellw-8,top+(i+1)*cellh-8),fill=bg,outline=COLORS["grid"]);draw.text((left+j*cellw+75,top+i*cellh+35),"N/A" if v is None else f"{v:+.2f}pp",fill=COLORS["ink"],font=font(19,True))
    return save_image(image,"06_新游戏生命周期RTP偏离.png")


def chart_focus_daily(game_rows):
    image,draw=canvas("重点游戏逐日RTP观察","8月26日—9月7日；实线=实际RTP，虚线=预期RTP。",1600,1050);names=["EasyWin","Blackjack","Tower","Plinko"]
    for idx,g in enumerate(names):
        rows=[]
        for d in sorted({r["date"] for r in game_rows if TREND[0]<=r["date"]<=TREND[1]}):
            s=[r for r in game_rows if r["game"]==g and r["date"]==d and r["complete_bet"]>0]
            if s: rows.append({"date":d,**old.aggregate(s)})
        x=100+(idx%2)*760;y=210+(idx//2)*400;panel_line(draw,g,rows,(x+100,y,x+700,y+260),COLORS["blue"])
    return save_image(image,"07_重点游戏逐日RTP观察.png")


def main():
    games, detail = read_game_rows(), read_detail_rows()
    prev_games, prev_all = aggregate_by_game(games, *PREV)
    curr_games, curr_all = aggregate_by_game(games, *CURR)
    prev_idx, curr_idx = index_by_game(prev_games), index_by_game(curr_games)
    names = sorted(set(prev_idx) | set(curr_idx))
    comparison=[]
    total_bet_delta=curr_all["complete_bet"]-prev_all["complete_bet"]
    for game in names:
        p,c=prev_idx.get(game),curr_idx.get(game)
        if not p or not c: continue
        bet_delta=c["complete_bet"]-p["complete_bet"]
        comparison.append({
            "game":game,"complete_bet_prev":p["complete_bet"],"complete_bet_curr":c["complete_bet"],"bet_change_pct":c["complete_bet"]/p["complete_bet"]-1 if p["complete_bet"] else None,
            "bet_delta":bet_delta,"bet_delta_contribution_pct":bet_delta/total_bet_delta if total_bet_delta else None,
            "actual_rtp_prev":p["actual_rtp"],"actual_rtp_curr":c["actual_rtp"],"rtp_change_pp":(c["actual_rtp"]-p["actual_rtp"])*100,
            "expected_rtp_curr":c["expected_rtp"],"rtp_gap_curr_pp":c["rtp_gap_pp"],"expected_coverage_curr":c["expected_coverage"],
            "bet_share_prev":p["complete_bet"]/prev_all["complete_bet"],"bet_share_curr":c["complete_bet"]/curr_all["complete_bet"],
            "bet_share_change_pp":(c["complete_bet"]/curr_all["complete_bet"]-p["complete_bet"]/prev_all["complete_bet"])*100,
            "rank_prev":p["rank"],"rank_curr":c["rank"],"rank_change":p["rank"]-c["rank"],"profit_vs_expected_curr":c["profit_vs_expected"]})
    comparison.sort(key=lambda r:r["complete_bet_curr"],reverse=True)

    new_daily={};new_summary={};lifecycle=[]
    for game,meta in NEW_GAMES.items():
        rows=[r for r in games if r["game"]==game and meta["launch"]<=r["date"]<=CURR[1] and r["complete_bet"]>0]
        daily=[]
        for d in sorted({r["date"] for r in rows}): daily.append({"date":d,**old.aggregate([r for r in rows if r["date"]==d])})
        new_daily[game]=daily;new_summary[game]={"game_id":meta["game_id"],"launch":meta["launch"].isoformat(),**old.aggregate(rows)}
        for life in range(1,5):
            selected=[r for r in detail if r["game"]==game and r["lifecycle"]==life and meta["launch"]<=r["date"]<=CURR[1] and r["complete_bet"]>0]
            lifecycle.append({"game":game,"lifecycle":life,**old.aggregate(selected)})

    anomalies=[r for r in curr_games if r["rtp_gap_pp"] is not None and abs(r["rtp_gap_pp"])>=3]
    anomalies.sort(key=lambda r:abs(r.get("profit_vs_expected") or 0),reverse=True)
    focus_names=list(dict.fromkeys(["EasyWin","Blackjack","Tower","Plinko"]+[r["game"] for r in anomalies[:4]]))
    focus=[]
    for name in focus_names:
        if name in curr_idx: focus.append(curr_idx[name])

    tc_raw=list(csv.DictReader(TC_PATH.open()));tc_rows=[{"date":date.fromisoformat(r["business_date"]),"recharge":float(r["success_recharge_amount"]),"withdraw":float(r["success_withdraw_amount"]),"tc":float(r["success_withdraw_amount"])/float(r["success_recharge_amount"])} for r in tc_raw]
    channels=[]
    for r in csv.DictReader(CHANNEL_PATH.open()):
        rp,wp,rc,wc=[float(r[k]) for k in ("recharge_prev","withdraw_prev","recharge_curr","withdraw_curr")]
        channels.append({"channel":r["channel"],"recharge_prev":rp,"withdraw_prev":wp,"recharge_curr":rc,"withdraw_curr":wc,"tc_prev":wp/rp,"tc_curr":wc/rc,"tc_change_pp":(wc/rc-wp/rp)*100})
    def week_tc(start,end):
        rs=[r for r in tc_rows if start<=r["date"]<=end];re=sum(r["recharge"] for r in rs);wd=sum(r["withdraw"] for r in rs);return {"days":len(rs),"recharge":re,"withdraw":wd,"tc":wd/re}
    tc_prev,tc_curr=week_tc(*PREV),week_tc(*CURR)
    for r in channels:
        r["recharge_change_pct"]=r["recharge_curr"]/r["recharge_prev"]-1 if r["recharge_prev"] else None
        r["recharge_share_curr"]=r["recharge_curr"]/tc_curr["recharge"] if tc_curr["recharge"] else None

    positive_drivers=sorted((r for r in comparison if r["bet_delta"]>0),key=lambda r:r["bet_delta"],reverse=True)
    negative_drivers=sorted((r for r in comparison if r["bet_delta"]<0),key=lambda r:r["bet_delta"])

    raw7=RAW/"2026-09-07-independent"
    shapes={name:pd.read_excel(raw7/f"{name}.xlsx").shape[0] for name in ("summary","detail","game","active")}
    assert shapes=={"summary":1,"detail":372,"game":31,"active":11}
    assert len([r for r in games if PREV[0]<=r["date"]<=CURR[1]])==14*31
    assert not [k for k,v in Counter((r["date"],r["game"]) for r in games if PREV[0]<=r["date"]<=CURR[1]).items() if v>1]
    assert tc_prev["days"]==tc_curr["days"]==7
    assert curr_all["days"]==7 and prev_all["days"]==7

    charts={"tc_trend":chart_tc(tc_rows),"channel_delta":chart_channels(channels),"game_scatter":chart_scatter(curr_games),"share_delta":chart_share_delta(comparison),"new_game_daily":chart_new_games(new_daily),"lifecycle":chart_lifecycle(lifecycle),"focus_daily":chart_focus_daily(games)}
    result={
        "generated_at":datetime.now(timezone.utc).isoformat(),"status":"ready_to_publish","windows":{"trend":[x.isoformat() for x in TREND],"previous_week":[x.isoformat() for x in PREV],"current_week":[x.isoformat() for x in CURR]},
        "tc":{"previous":tc_prev,"current":tc_curr,"change_pp":(tc_curr["tc"]-tc_prev["tc"])*100,"recharge_change_pct":tc_curr["recharge"]/tc_prev["recharge"]-1,"withdraw_change_pct":tc_curr["withdraw"]/tc_prev["withdraw"]-1,"daily":[{**r,"date":r["date"].isoformat()} for r in tc_rows],"channels":channels},
        "game_overall":{"previous":prev_all,"current":curr_all,"bet_change_pct":curr_all["complete_bet"]/prev_all["complete_bet"]-1,"actual_rtp_change_pp":(curr_all["actual_rtp"]-prev_all["actual_rtp"])*100},
        "game_comparison":comparison,"bet_drivers":{"total_delta":total_bet_delta,"positive":positive_drivers[:7],"negative":negative_drivers[:5],"channel_package_attribution_status":"not_available_no_shared_game_channel_package_key"},"current_games":curr_games,"new_games":new_summary,"new_game_daily":{g:[{**r,"date":r["date"].isoformat()} for r in rs] for g,rs in new_daily.items()},"new_game_lifecycle":lifecycle,"focus_games":focus,"anomalies":anomalies,"charts":charts,
        "quality":{"game_rows":14*31,"distinct_games":31,"duplicate_date_game_keys":[],"lifecycle_0903":"complete_requery","lifecycle_0907":"complete_independent_requery","lifecycle_0907_stable_seconds":45,"quarantined_candidate":"data/raw/lifecycle_joint/2026-09-08-report/2026-09-07","accepted_source":"data/raw/lifecycle_joint/2026-09-08-report/2026-09-07-independent","source_shapes":shapes,"blocked_fields":["有效局数","最终结算状态","取消/退款","免费注/Bonus","配置版本","用户级大奖分布"]}}
    (ROOT/"analysis-results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    (ROOT/"quality-checks.json").write_text(json.dumps({"status":"passed","publication_allowed":True,**result["quality"]},ensure_ascii=False,indent=2))
    receipt=json.loads((ROOT/"source-receipt.json").read_text())
    receipt.update({"status":"sources_complete","new_lark_document_created":False,"reason":None,"lifecycle_0907_resolution":"initial low-volume candidate quarantined; independent requery returned 2,507,108,274.37 full bet and 75,106 users with stable four-block fingerprints","next_action":"Build, validate and publish the V3 Lark report.","original_report_revision":119,"original_report_unchanged":True})
    (ROOT/"source-receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print(json.dumps({"status":result["status"],"tc":result["tc"],"game_overall":result["game_overall"],"new_games":result["new_games"],"anomalies":[{"game":r["game"],"bet":r["complete_bet"],"rtp":r["actual_rtp"],"gap_pp":r["rtp_gap_pp"]} for r in anomalies],"charts":charts},ensure_ascii=False,default=str))

if __name__=="__main__": main()
