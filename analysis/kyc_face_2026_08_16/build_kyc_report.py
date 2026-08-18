from __future__ import annotations

import csv
import hashlib
import html
import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/robin/Documents/wajetan_analyst")
DATA_DIR = Path("/Users/robin/Desktop/waje data")
WORK_DIR = ROOT / "analysis/kyc_face_2026_08_16"
HTML_OUT = ROOT / "output/html/Waje-KYC人脸识别与提现认证深度分析-2026-08-16.html"
MD_OUT = ROOT / "knowledge/02-数据/Waje-KYC人脸识别与提现认证分析-2026-08-16.md"
ACTIVE_PATH = DATA_DIR / "主动填写人脸认证统计_2026-08-17T06_32_37.316401Z.csv"
WITHDRAW_PATH = DATA_DIR / "提现触发人脸认证统计_2026-08-17T06_33_07.000788Z.csv"
CONFIG_PATH = Path("/Users/robin/Downloads/线上数值新包.xlsx")
START = pd.Timestamp("2026-07-23")
END = pd.Timestamp("2026-08-16")

EVENT_PHASES = [
    {
        "key": "before_h5_threshold",
        "name": "H5首充门槛调整前",
        "short": "7/23—7/26 调整前",
        "start": pd.Timestamp("2026-07-23"),
        "end": pd.Timestamp("2026-07-26"),
        "event": "H5 config_11 的 firstRechargeBalance 仍为900；作为调整前基线",
    },
    {
        "key": "after_h5_threshold",
        "name": "H5首充门槛900→500后",
        "short": "7/27—8/16 调整后",
        "start": pd.Timestamp("2026-07-27"),
        "end": pd.Timestamp("2026-08-16"),
        "event": "7月27日23:20，H5 config_11 的 firstRechargeBalance 从900调整为500；沟通记录确认之后未再调整",
    },
]

PACKAGE_MAP = {
    "com.hfhy.waje.special": "App",
    "com.wajegame.web": "H5",
}

SOURCE_URLS = {
    "历史报告1": "https://ksg964l11fam.sg.larksuite.com/wiki/M1dswwA1NiZ8L3kO2vSlZMNKgxd",
    "历史报告2": "https://ksg964l11fam.sg.larksuite.com/wiki/UZaww1fGpibKcJkEisil3VSRgHf",
    "旧版风险认证机制": "https://ksg964l11fam.sg.larksuite.com/wiki/FYWzwM6X1iTC62kL3e8l0WQvgRh",
    "手机号校验银行账户方案": "https://ksg964l11fam.sg.larksuite.com/wiki/XGUPwYoMui9ieEk8OktlwW8Egkc",
    "风险判断优化": "https://ksg964l11fam.sg.larksuite.com/wiki/I1Eow13XhiYVsyklqDflcHXGgVY",
    "暂时搁置方案": "https://ksg964l11fam.sg.larksuite.com/wiki/UZ7Jwz7ptiwa0KkQGlClZatqg7c",
    "线上KYC配置": "https://ksg964l11fam.sg.larksuite.com/sheets/WWBBsLNl4hTFnbtI9arlmGsqgoc?sheet=Pf4y9V",
    "线上人脸识别配置": "https://ksg964l11fam.sg.larksuite.com/sheets/WWBBsLNl4hTFnbtI9arlmGsqgoc?sheet=3KVm1s",
    "KYC人脸识别机制": "https://ksg964l11fam.sg.larksuite.com/wiki/V3oPwswUni1A7BkKur9ld0QmgQg",
}

CONFIG_SNAPSHOT = {
    "verified_at": "2026-08-17",
    "change_event": {
        "effective_at": "2026-07-27 23:20",
        "scope": "H5 config_11",
        "field": "firstRechargeBalance",
        "before": 900,
        "after": 500,
        "later_change": "沟通记录确认后续未再调整",
    },
    "trigger_matrix": [
        {"segment": "App自然新增", "config": "config_4", "first_recharge_balance": 900, "total_recharge_times": 3, "total_recharge_amount": 3000, "register_days": 180, "otp": "开", "kyc_v2": "开"},
        {"segment": "App非自然新增", "config": "config_2", "first_recharge_balance": 900, "total_recharge_times": 1, "total_recharge_amount": 2000, "register_days": 180, "otp": "关", "kyc_v2": "关"},
        {"segment": "H5", "config": "config_11", "first_recharge_balance": 500, "total_recharge_times": 3, "total_recharge_amount": 3000, "register_days": 180, "otp": "开", "kyc_v2": "开"},
        {"segment": "iOS", "config": "config_3", "first_recharge_balance": 1000, "total_recharge_times": 3, "total_recharge_amount": 3000, "register_days": 3, "otp": "开", "kyc_v2": "开"},
    ],
    "face": {
        "withdraw_face_open": True,
        "face_reg_time": None,
        "kyc_verify_daily_count": 10,
        "bvn_verification_interval_seconds": 60,
        "face_verify_daily_count": 5,
        "idv_minors_limit": True,
        "face_match_percent": 60,
        "idv_match_percent": 90,
        "bank_phone_same_skip": True,
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pct(value: float | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.{digits}f}%"


def pp(value: float | None, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.{digits}f}pp"


def num(value: float | int | None, digits: int = 0) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    if digits == 0:
        return f"{int(round(value)):,}"
    return f"{value:,.{digits}f}"


def read_source(path: Path, flow: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["日期"] = pd.to_datetime(df["日期"], format="%Y年%m月%d日")
    df["流程"] = flow
    df["端"] = df["包名"].map(PACKAGE_MAP).fillna("未知")
    return df


def in_window(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["日期"].between(START, END)].copy()


def summarize(group: pd.DataFrame, flow: str) -> dict:
    s = group.sum(numeric_only=True)
    actual = float(s["实际调用BVN/NIN人数"])
    not_called = float(s["未调用BVN/NIN人数"])
    trigger = float(s["每日触发人数"]) if flow == "提现触发" else actual + not_called
    face_req = float(s["请求人脸识别人数"])
    face_success = float(s["最终人脸识别成功人数"])
    face_fail = float(s["最终人脸识别失败人数"])
    face_completed = face_success + face_fail
    unresolved = face_req - face_completed
    bvn_call = float(s["BVN调用人数"])
    nin_call = float(s["NIN调用人数"])
    retained = float(s["当前保留失败原因次数"])
    return {
        "flow": flow,
        "trigger": trigger,
        "actual": actual,
        "not_called": not_called,
        "face_request": face_req,
        "face_attempts": float(s["请求人脸识别次数"]),
        "face_success": face_success,
        "face_fail": face_fail,
        "face_completed": face_completed,
        "face_unresolved": unresolved,
        "action_rate": actual / trigger if trigger else None,
        "face_reach_rate": face_req / actual if actual else None,
        "face_success_request_rate": face_success / face_req if face_req else None,
        "face_success_completed_rate": face_success / face_completed if face_completed else None,
        "face_fail_request_rate": face_fail / face_req if face_req else None,
        "face_unresolved_rate": unresolved / face_req if face_req else None,
        "e2e_rate": face_success / trigger if trigger else None,
        "caller_to_success": face_success / actual if actual else None,
        "bvn_calls": bvn_call,
        "bvn_pass": float(s["BVN通过人数"]),
        "bvn_fail": float(s["BVN失败人数"]),
        "bvn_pass_rate": float(s["BVN通过人数"]) / bvn_call if bvn_call else None,
        "nin_calls": nin_call,
        "nin_pass": float(s["NIN通过人数"]),
        "nin_fail": float(s["NIN失败人数"]),
        "nin_pass_rate": float(s["NIN通过人数"]) / nin_call if nin_call else None,
        "bvn_only": float(s["仅调用BVN人数"]),
        "nin_only": float(s["仅调用NIN人数"]),
        "both_methods": float(s["同时调用BVN和NIN人数"]),
        "attempts_per_user": float(s["请求人脸识别次数"]) / face_req if face_req else None,
        "history_fail_attempts": float(s["人脸识别历史失败总次数"]),
        "mismatch_attempts": float(s["当前保留-人像不匹配次数"]),
        "request_error_attempts": float(s["当前保留-请求接口失败次数"]),
        "third_error_attempts": float(s["当前保留-三方接口错误次数"]),
        "retained_fail_reasons": retained,
        "cleared_fail_reasons": float(s["成功后被清除的失败原因次数"]),
        "mismatch_share_retained": float(s["当前保留-人像不匹配次数"]) / retained if retained else None,
        "mismatch_share_history_fail": float(s["当前保留-人像不匹配次数"]) / float(s["人脸识别历史失败总次数"]) if float(s["人脸识别历史失败总次数"]) else None,
        "mismatch_share_all_face_attempts": float(s["当前保留-人像不匹配次数"]) / float(s["请求人脸识别次数"]) if float(s["请求人脸识别次数"]) else None,
        "request_error_share_retained": float(s["当前保留-请求接口失败次数"]) / retained if retained else None,
        "third_error_share_retained": float(s["当前保留-三方接口错误次数"]) / retained if retained else None,
    }


def weekly_summary(df: pd.DataFrame, flow: str) -> list[dict]:
    bins = [pd.Timestamp("2026-07-26"), pd.Timestamp("2026-08-02"), pd.Timestamp("2026-08-09"), pd.Timestamp("2026-08-16")]
    labels = ["07-27至08-02", "08-03至08-09", "08-10至08-16"]
    data = df.copy()
    data["周期"] = pd.cut(data["日期"], bins=bins, labels=labels)
    rows: list[dict] = []
    for period in labels:
        for platform in ["全部", "App", "H5"]:
            part = data[data["周期"].astype(str) == period]
            if platform != "全部":
                part = part[part["端"] == platform]
            item = summarize(part, flow)
            item.update({"period": period, "platform": platform})
            rows.append(item)
    return rows


def phase_summary(df: pd.DataFrame, flow: str) -> list[dict]:
    """按已知发布/配置事件划分日历窗口；源CSV无真实版本字段，不能视为版本cohort。"""
    rows: list[dict] = []
    for phase in EVENT_PHASES:
        phase_df = df.loc[df["日期"].between(phase["start"], phase["end"])]
        for platform in ["全部", "App", "H5"]:
            part = phase_df if platform == "全部" else phase_df.loc[phase_df["端"] == platform]
            item = summarize(part, flow)
            item.update({
                "phase_key": phase["key"],
                "phase": phase["name"],
                "phase_short": phase["short"],
                "phase_start": phase["start"].strftime("%Y-%m-%d"),
                "phase_end": phase["end"].strftime("%Y-%m-%d"),
                "days": int((phase["end"] - phase["start"]).days + 1),
                "event": phase["event"],
                "platform": platform,
            })
            rows.append(item)
    return rows


def normalize_rows(active: pd.DataFrame, withdraw: pd.DataFrame) -> list[dict]:
    rows = []
    for df in [active, withdraw]:
        for _, row in df.sort_values(["日期", "流程", "端"]).iterrows():
            record = {"日期": row["日期"].strftime("%Y-%m-%d"), "流程": row["流程"], "端": row["端"], "包名": row["包名"]}
            for col in df.columns:
                if col in {"日期", "流程", "端", "包名"}:
                    continue
                value = row[col]
                record[col] = int(value) if isinstance(value, (int, float)) and not pd.isna(value) else value
            rows.append(record)
    return rows


def svg_funnel(stages: list[tuple[str, float]], width: int = 900, height: int = 320) -> str:
    max_v = max(v for _, v in stages) or 1
    top = 28
    gap = 12
    bar_h = (height - top - gap * (len(stages) - 1)) / len(stages)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="认证漏斗">']
    colors = ["#2F80C9", "#45A779", "#76C7A3", "#F1C64B", "#EF7B78"]
    for i, (label, value) in enumerate(stages):
        w = max(150, (width - 250) * value / max_v)
        x = 210
        y = top + i * (bar_h + gap)
        parts.append(f'<text x="0" y="{y + bar_h * .65:.1f}" class="svg-label">{html.escape(label)}</text>')
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="{w:.1f}" height="{bar_h:.1f}" rx="9" fill="{colors[i % len(colors)]}"/>')
        parts.append(f'<text x="{x + 14}" y="{y + bar_h * .65:.1f}" class="svg-value">{num(value)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_grouped_bars(categories: list[str], series: list[tuple[str, list[float], str]], width: int = 940, height: int = 390, percent: bool = True) -> str:
    left, right, top, bottom = 78, 18, 30, 68
    plot_w, plot_h = width - left - right, height - top - bottom
    max_v = max([v for _, vals, _ in series for v in vals] + [1])
    max_v = min(1.0, math.ceil(max_v * 10) / 10) if percent else max_v * 1.12
    group_w = plot_w / max(1, len(categories))
    bar_w = min(28, group_w / (len(series) + 1.2))
    out = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for i in range(6):
        value = max_v * i / 5
        y = top + plot_h - plot_h * i / 5
        label = f"{value*100:.0f}%" if percent else f"{value:,.0f}"
        out.append(f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        out.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="tick">{label}</text>')
    for ci, category in enumerate(categories):
        center = left + group_w * (ci + .5)
        out.append(f'<text x="{center:.1f}" y="{height-32}" text-anchor="middle" class="tick">{html.escape(category)}</text>')
        for si, (name, vals, color) in enumerate(series):
            v = vals[ci]
            x = center + (si - (len(series)-1)/2) * (bar_w + 5) - bar_w/2
            h = 0 if max_v == 0 else plot_h * v / max_v
            y = top + plot_h - h
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="5" fill="{color}"/>')
            lab = pct(v) if percent else num(v)
            out.append(f'<text x="{x+bar_w/2:.1f}" y="{max(top+11,y-7):.1f}" text-anchor="middle" class="bar-label">{lab}</text>')
    lx = left
    for name, _, color in series:
        out.append(f'<rect x="{lx}" y="{height-15}" width="12" height="12" rx="3" fill="{color}"/><text x="{lx+18}" y="{height-5}" class="legend">{html.escape(name)}</text>')
        lx += 125
    out.append("</svg>")
    return "".join(out)


def svg_lines(categories: list[str], series: list[tuple[str, list[float], str]], width: int = 940, height: int = 390, percent: bool = True) -> str:
    left, right, top, bottom = 70, 22, 30, 72
    plot_w, plot_h = width - left - right, height - top - bottom
    all_v = [v for _, vals, _ in series for v in vals]
    min_v = max(0, min(all_v) - .05) if percent else 0
    max_v = min(1, max(all_v) + .05) if percent else max(all_v) * 1.15
    out = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for i in range(6):
        v = min_v + (max_v-min_v) * i/5
        y = top + plot_h - plot_h*i/5
        label = f"{v*100:.0f}%" if percent else f"{v:,.0f}"
        out.append(f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        out.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="tick">{label}</text>')
    xs=[]
    for i, cat in enumerate(categories):
        x = left + (plot_w * i / max(1,len(categories)-1))
        xs.append(x)
        out.append(f'<text x="{x:.1f}" y="{height-38}" text-anchor="middle" class="tick">{html.escape(cat)}</text>')
    for name, vals, color in series:
        points=[]
        for x,v in zip(xs,vals):
            y = top + plot_h - (v-min_v)/(max_v-min_v)*plot_h if max_v>min_v else top+plot_h/2
            points.append((x,y,v))
        out.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y,_ in points)}" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        for x,y,v in points:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"/><text x="{x:.1f}" y="{y-12:.1f}" text-anchor="middle" class="bar-label">{pct(v) if percent else num(v)}</text>')
    lx=left
    for name,_,color in series:
        out.append(f'<line x1="{lx}" x2="{lx+24}" y1="{height-12}" y2="{height-12}" stroke="{color}" stroke-width="4"/><text x="{lx+31}" y="{height-7}" class="legend">{html.escape(name)}</text>')
        lx += 165
    out.append("</svg>")
    return "".join(out)


def svg_daily_kyc_trend(df: pd.DataFrame, width: int = 1040, height: int = 470) -> str:
    """Draw a readable 25-day trend with the verified config cut and error spikes."""
    data = df.copy()
    grouped = data.groupby(["日期", "端"], as_index=False).sum(numeric_only=True)
    dates = sorted(grouped["日期"].unique())

    def values(platform: str, metric: str) -> list[float]:
        part = grouped[grouped["端"] == platform].set_index("日期").reindex(dates).fillna(0)
        if metric == "success_request":
            den = part["请求人脸识别人数"].replace(0, pd.NA)
            return (part["最终人脸识别成功人数"] / den).fillna(0).tolist()
        if metric == "unresolved":
            den = part["请求人脸识别人数"].replace(0, pd.NA)
            nume = part["请求人脸识别人数"] - part["最终人脸识别成功人数"] - part["最终人脸识别失败人数"]
            return (nume / den).fillna(0).tolist()
        raise ValueError(metric)

    totals = grouped.groupby("日期")["每日触发人数"].sum().reindex(dates).fillna(0)
    h5_trigger = grouped[grouped["端"] == "H5"].set_index("日期")["每日触发人数"].reindex(dates).fillna(0)
    trigger_share = (h5_trigger / totals.replace(0, pd.NA)).fillna(0).tolist()
    series = [
        ("App 成功/请求", values("App", "success_request"), "#2F80C9"),
        ("H5 成功/请求", values("H5", "success_request"), "#45A779"),
        ("H5 无最终结果", values("H5", "unresolved"), "#EF7B78"),
        ("H5 触发占比", trigger_share, "#E5A900"),
    ]
    left, right, top, bottom = 70, 28, 74, 78
    plot_w, plot_h = width - left - right, height - top - bottom
    all_v = [v for _, vals, _ in series for v in vals]
    min_v = max(0, min(all_v) - .06)
    max_v = min(1, max(all_v) + .06)
    xs = [left + plot_w * i / max(1, len(dates) - 1) for i in range(len(dates))]
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="7月23日至8月16日App与H5认证质量连续趋势">']
    for i in range(6):
        v = min_v + (max_v - min_v) * i / 5
        y = top + plot_h - plot_h * i / 5
        out.append(f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>')
        out.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="tick">{v*100:.0f}%</text>')

    date_labels = [pd.Timestamp(d).strftime("%m-%d") for d in dates]
    label_indexes = {0, 4, 8, 12, 16, 20, len(dates) - 1}
    for i, (x, label) in enumerate(zip(xs, date_labels)):
        if i in label_indexes:
            out.append(f'<text x="{x:.1f}" y="{height-40}" text-anchor="middle" class="tick">{label}</text>')

    change_date = pd.Timestamp("2026-07-27")
    change_idx = next(i for i, d in enumerate(dates) if pd.Timestamp(d) == change_date)
    change_x = xs[change_idx]
    out.append(f'<line x1="{change_x:.1f}" x2="{change_x:.1f}" y1="{top-14}" y2="{top+plot_h}" stroke="#0F699F" stroke-width="2" stroke-dasharray="6 5"/>')
    out.append(f'<rect x="{max(left, change_x-82):.1f}" y="8" width="190" height="35" rx="9" fill="#EAF5FF" stroke="#2F80C9"/>')
    out.append(f'<text x="{max(left, change_x-72):.1f}" y="30" class="event-label">7/27 23:20 · H5门槛900→500</text>')

    spike_labels = {
        "08-01": "请求失败75次",
        "08-05": "请求失败51次",
        "08-13": "请求失败53次",
    }
    for i, (x, label) in enumerate(zip(xs, date_labels)):
        if label not in spike_labels:
            continue
        y0 = top + 10 + (18 if label == "08-05" else 0)
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y0+8}" y2="{top+plot_h}" stroke="#DF6865" stroke-width="1.4" stroke-dasharray="4 5" opacity=".7"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y0:.1f}" r="4" fill="#DF6865"/>')
        out.append(f'<text x="{x+6:.1f}" y="{y0+4:.1f}" class="event-label danger">{label} {spike_labels[label]}</text>')

    for name, vals, color in series:
        points = []
        for x, v in zip(xs, vals):
            y = top + plot_h - (v - min_v) / (max_v - min_v) * plot_h if max_v > min_v else top + plot_h / 2
            points.append((x, y, v))
        out.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y,_ in points)}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
        for x, y, _ in points:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.8" fill="{color}"/>')
        x, y, v = points[-1]
        out.append(f'<text x="{x-4:.1f}" y="{y-9:.1f}" text-anchor="end" class="bar-label">{pct(v)}</text>')

    lx = left
    for name, _, color in series:
        out.append(f'<line x1="{lx}" x2="{lx+22}" y1="{height-13}" y2="{height-13}" stroke="{color}" stroke-width="4"/><text x="{lx+29}" y="{height-8}" class="legend">{html.escape(name)}</text>')
        lx += 205
    out.append("</svg>")
    return "".join(out)


def svg_daily_errors(df: pd.DataFrame, width: int = 940, height: int = 360) -> str:
    pivot = df.pivot_table(index="日期", columns="端", values="当前保留-请求接口失败次数", aggfunc="sum").fillna(0)
    dates = [d.strftime("%m-%d") for d in pivot.index]
    series = [("App", pivot.get("App", pd.Series(0,index=pivot.index)).tolist(), "#2F80C9"), ("H5", pivot.get("H5", pd.Series(0,index=pivot.index)).tolist(), "#EF7B78")]
    return svg_lines(dates, series, width, height, percent=False)


def table(headers: list[str], rows: list[list[str]], classes: str = "") -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    trs = []
    for row in rows:
        trs.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return f'<div class="table-wrap"><table class="{classes}"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'


def build_analysis() -> tuple[dict, pd.DataFrame]:
    active_all = read_source(ACTIVE_PATH, "主动填写")
    withdraw_all = read_source(WITHDRAW_PATH, "提现触发")
    active = in_window(active_all)
    withdraw = in_window(withdraw_all)

    summary = {}
    for flow, df in [("主动填写", active), ("提现触发", withdraw)]:
        summary[flow] = {platform: summarize(df if platform == "全部" else df[df["端"] == platform], flow) for platform in ["全部", "App", "H5"]}

    weekly = weekly_summary(active, "主动填写") + weekly_summary(withdraw, "提现触发")
    phases = phase_summary(active, "主动填写") + phase_summary(withdraw, "提现触发")
    w = summary["提现触发"]["全部"]
    app = summary["提现触发"]["App"]
    h5 = summary["提现触发"]["H5"]
    total_loss = w["trigger"] - w["face_success"]
    losses = [
        {"stage": "触发后未调用BVN/NIN", "count": w["not_called"], "share": w["not_called"] / total_loss},
        {"stage": "已调用但未请求人脸", "count": w["actual"] - w["face_request"], "share": (w["actual"] - w["face_request"]) / total_loss},
        {"stage": "请求人脸但无最终结果", "count": w["face_unresolved"], "share": w["face_unresolved"] / total_loss},
        {"stage": "最终人脸失败", "count": w["face_fail"], "share": w["face_fail"] / total_loss},
    ]

    app_action_gap = max(0, h5["action_rate"] - app["action_rate"])
    app_extra_callers = app_action_gap * app["trigger"]
    h5_face_gap = max(0, app["face_success_request_rate"] - h5["face_success_request_rate"])
    h5_extra_face_success = h5_face_gap * h5["face_request"]
    h5_unresolved_gap = max(0, h5["face_unresolved_rate"] - app["face_unresolved_rate"])
    h5_extra_resolved = h5_unresolved_gap * h5["face_request"]
    bvn_gap = w["nin_pass_rate"] - w["bvn_pass_rate"]
    bvn_only_pass_opportunity = bvn_gap * w["bvn_only"]
    opportunity = {
        "app_action_gap_pp": app_action_gap,
        "app_extra_callers": app_extra_callers,
        "app_extra_success_at_current_downstream": app_extra_callers * app["caller_to_success"],
        "h5_face_gap_pp": h5_face_gap,
        "h5_extra_face_success": h5_extra_face_success,
        "h5_unresolved_gap_pp": h5_unresolved_gap,
        "h5_extra_resolved": h5_extra_resolved,
        "bvn_to_nin_gap_pp": bvn_gap,
        "bvn_only_pass_opportunity": bvn_only_pass_opportunity,
    }

    daily = withdraw.copy()
    daily["行动率"] = daily["实际调用BVN/NIN人数"] / daily["每日触发人数"]
    daily["到达人脸率"] = daily["请求人脸识别人数"] / daily["实际调用BVN/NIN人数"]
    daily["人脸成功率_请求"] = daily["最终人脸识别成功人数"] / daily["请求人脸识别人数"]
    daily["人脸成功率_完成"] = daily["最终人脸识别成功人数"] / (daily["最终人脸识别成功人数"] + daily["最终人脸识别失败人数"])
    daily["无最终结果率"] = (daily["请求人脸识别人数"] - daily["最终人脸识别成功人数"] - daily["最终人脸识别失败人数"]) / daily["请求人脸识别人数"]
    daily["端到端率"] = daily["最终人脸识别成功人数"] / daily["每日触发人数"]
    daily["BVN通过率"] = daily["BVN通过人数"] / daily["BVN调用人数"]
    daily["NIN通过率"] = daily["NIN通过人数"] / daily["NIN调用人数"]
    daily["人均请求次数"] = daily["请求人脸识别次数"] / daily["请求人脸识别人数"]
    top_request_errors = daily.nlargest(8, "当前保留-请求接口失败次数")[["日期", "端", "当前保留-请求接口失败次数", "当前保留失败原因次数"]]

    normalized = pd.concat([active, withdraw], ignore_index=True).sort_values(["日期", "流程", "端"])
    normalized["日期"] = normalized["日期"].dt.strftime("%Y-%m-%d")
    normalized = normalized[["日期", "流程", "端", "包名"] + [c for c in normalized.columns if c not in {"日期", "流程", "端", "包名"}]]

    quality = {
        "source_rows": {"主动填写": len(active_all), "提现触发": len(withdraw_all)},
        "source_min_date": min(active_all["日期"].min(), withdraw_all["日期"].min()).strftime("%Y-%m-%d"),
        "source_max_date": max(active_all["日期"].max(), withdraw_all["日期"].max()).strftime("%Y-%m-%d"),
        "window_rows": {"主动填写": len(active), "提现触发": len(withdraw)},
        "window_days": {"主动填写": active["日期"].nunique(), "提现触发": withdraw["日期"].nunique()},
        "duplicates": {"主动填写": int(active.duplicated(["日期", "包名"]).sum()), "提现触发": int(withdraw.duplicated(["日期", "包名"]).sum())},
        "nulls": {"主动填写": int(active.isna().sum().sum()), "提现触发": int(withdraw.isna().sum().sum())},
        "excluded_partial_date": "2026-08-17",
        "grain": "日期×包名的日汇总；每天先按用户去重，再跨日累计，同一用户跨日可能重复",
        "unsupported_dimensions": ["渠道", "真实客户端版本/流量归属", "风险配置版本", "手机号绑定/手机号查BVN", "银行校验结果", "最终提现结果"],
        "comment_handling": "采用分层漏斗：先拆无最终结果，再看已有结果者成功/失败，最后分析失败尝试原因",
    }

    return ({
        "meta": {
            "title": "Waje KYC人脸识别与提现认证深度分析",
            "period": "2026-07-23至2026-08-16",
            "generated_for": "Waje产品、数据、风控与研发",
            "unit": "累计人次（每天按用户去重后相加；同一用户跨日可能重复）",
            "package_mapping": PACKAGE_MAP,
        },
        "files": {
            "主动填写": {"path": str(ACTIVE_PATH), "sha256": sha256(ACTIVE_PATH)},
            "提现触发": {"path": str(WITHDRAW_PATH), "sha256": sha256(WITHDRAW_PATH)},
            "线上配置快照": {"path": str(CONFIG_PATH), "sha256": sha256(CONFIG_PATH)},
        },
        "summary": summary,
        "weekly": weekly,
        "phases": phases,
        "losses": losses,
        "opportunity": opportunity,
        "quality": quality,
        "top_request_errors": [
            {"date": r["日期"].strftime("%Y-%m-%d"), "platform": r["端"], "count": int(r["当前保留-请求接口失败次数"]), "all_current_reasons": int(r["当前保留失败原因次数"])}
            for _, r in top_request_errors.iterrows()
        ],
        "historical": {
            "2026-07-24": {"entered": 1052, "id_pass": 884, "id_pass_rate": 0.8403, "face_success": 639, "id_to_face": 0.7228, "e2e": 0.6074},
            "2026-07-23至07-26": {"id_pass_range": "82%—86%", "face_completed_success": ">85%", "e2e_range": "46%—50%", "face_abandon_range": "16%—19%", "mismatch_share": ">96%"},
        },
        "config_snapshot": CONFIG_SNAPSHOT,
        "sources": SOURCE_URLS,
    }, normalized)


def build_markdown(data: dict) -> str:
    w = data["summary"]["提现触发"]["全部"]
    app = data["summary"]["提现触发"]["App"]
    h5 = data["summary"]["提现触发"]["H5"]
    active = data["summary"]["主动填写"]["全部"]
    opp = data["opportunity"]
    losses = data["losses"]
    phase_all = [x for x in data["phases"] if x["flow"] == "提现触发" and x["platform"] == "全部"]
    phase_app = [x for x in data["phases"] if x["flow"] == "提现触发" and x["platform"] == "App"]
    phase_h5 = [x for x in data["phases"] if x["flow"] == "提现触发" and x["platform"] == "H5"]
    pre_all, post_all = phase_all
    pre_app, post_app = phase_app
    pre_h5, post_h5 = phase_h5
    h5_daily_before = pre_h5["trigger"] / pre_h5["days"]
    h5_daily_after = post_h5["trigger"] / post_h5["days"]
    app_daily_before = pre_app["trigger"] / pre_app["days"]
    app_daily_after = post_app["trigger"] / post_app["days"]
    phase_md = "\n".join(
        f"| {a['phase_short']} | {num(h['trigger']/h['days'])} | {pct(h['trigger']/a['trigger'])} | {pct(h['face_success_request_rate'])} | {pct(h['face_unresolved_rate'])} | {pct(h['e2e_rate'])} | {pct(ap['face_success_request_rate'])} | {pct(ap['e2e_rate'])} |"
        for a, ap, h in zip(phase_all, phase_app, phase_h5)
    )
    md = f"""# Waje KYC人脸识别与提现认证深度分析（2026-07-23—2026-08-16）

## 报告导读

25天提现触发数据共记录 **{num(w['trigger'])} 累计人次**，最终人脸成功 {num(w['face_success'])}，按全部触发计算为 **{pct(w['e2e_rate'])}**。这里的“累计人次”是每天分别按用户去重后再相加，同一用户跨日出现会重复计算，不等于25天独立用户数。线上配置确认：**7月27日23:20，H5 config_11 的首充带币触发门槛由900降至500，之后未再调整**。调整后H5日均触发约从 {num(h5_daily_before)} 增至 {num(h5_daily_after)} 人次/日（{pct(h5_daily_after/h5_daily_before-1)}），但请求后成功率由 {pct(pre_h5['face_success_request_rate'])} 降至 {pct(post_h5['face_success_request_rate'])}，无最终结果率由 {pct(pre_h5['face_unresolved_rate'])} 升至 {pct(post_h5['face_unresolved_rate'])}；同期App人脸成功/请求基本稳定。门槛下调扩大了H5覆盖人群，但新增覆盖没有同步转化为更好的认证质量，并叠加H5请求链路异常。“人像不匹配”仅表示失败尝试构成，不是用户失败率。

## 一、范围与口径

- 数据窗口：2026-07-23至2026-08-16，共25个完整自然日；排除8月17日未完整数据。
- 两份CSV均为`日期×包名`日汇总，窗口内各50行、无重复日期包名。
- `com.hfhy.waje.special`归类App，`com.wajegame.web`归类H5。
- 区间人数为“累计人次”：每天先按用户去重，再将每日人数相加；同一用户跨日会重复计算，因此不是25天独立用户数。
- `请求人脸但无最终结果`＝请求人数－最终成功人数－最终失败人数，包含主动退出、黑屏/摄像头未拉起、未完成或在途，不能全部认定为用户主动放弃。
- 失败原因是失败尝试次数，不是失败用户数。

## 二、人脸阶段结果拆解

| 层级 | 累计人次 | 分母与解释 |
|---|---:|---|
| 请求人脸识别 | {num(w['face_request'])} | 当前CSV可直接观测到的人脸阶段入口 |
| 无最终结果 | {num(w['face_unresolved'])} | 请求－成功－失败；占请求 {pct(w['face_unresolved_rate'])} |
| 已形成结果 | {num(w['face_completed'])} | 成功＋明确失败 |
| 其中成功 | {num(w['face_success'])} | 占已形成结果 {pct(w['face_success_completed_rate'])} |
| 其中明确失败 | {num(w['face_fail'])} | 占请求 {pct(w['face_fail_request_rate'])} |

当前CSV还缺“至少一种BVN/NIN已通过人数”和页面退出原因，因此只能用“请求人脸”作为进入人脸阶段的代理。后续应补充身份通过、Face SDK拉起、相机权限、开始采集、主动退出和黑屏错误等状态。

## 三、提现触发认证漏斗

| 阶段 | 累计人次 | 阶段转化 |
|---|---:|---:|
| 风险提现触发 | {num(w['trigger'])} | 100.0% |
| 实际调用BVN/NIN | {num(w['actual'])} | {pct(w['action_rate'])} |
| 请求人脸识别 | {num(w['face_request'])} | {pct(w['face_reach_rate'])} |
| 形成最终人脸结果 | {num(w['face_completed'])} | {pct(w['face_completed']/w['face_request'])} |
| 最终人脸成功 | {num(w['face_success'])} | {pct(w['e2e_rate'])}（触发口径） |

关键口径：人脸成功率按请求人数为 {pct(w['face_success_request_rate'])}，按已有最终结果为 {pct(w['face_success_completed_rate'])}。若忽略 {num(w['face_unresolved'])} 累计人次的无最终结果人群，会明显高估整体认证体验。

### 流失贡献

| 流失阶段 | 累计人次 | 占总流失 |
|---|---:|---:|
""" + "\n".join(f"| {x['stage']} | {num(x['count'])} | {pct(x['share'])} |" for x in losses) + f"""

## 四、7月27日H5触发门槛调整前后

| 配置窗口 | H5日均触发 | H5触发占比 | H5成功/请求 | H5无结果率 | H5端到端 | App成功/请求 | App端到端 |
|---|---:|---:|---:|---:|---:|---:|---:|
{phase_md}

- 配置证据：7月27日23:20，H5 `config_11.firstRechargeBalance` 从900改为500；App自然/非自然仍为900，iOS为1000。沟通记录确认该项后续未再调整。
- 调整后H5日均触发增长 {pct(h5_daily_after/h5_daily_before-1)}，明显高于App的 {pct(app_daily_after/app_daily_before-1)}；H5在全部触发中的占比从 {pct(pre_h5['trigger']/pre_all['trigger'])} 升至 {pct(post_h5['trigger']/post_all['trigger'])}。
- H5请求后成功率下降 {pp(post_h5['face_success_request_rate']-pre_h5['face_success_request_rate'])}，无最终结果率上升 {pp(post_h5['face_unresolved_rate']-pre_h5['face_unresolved_rate'])}，端到端下降 {pp(post_h5['e2e_rate']-pre_h5['e2e_rate'])}；同期App成功/请求变化 {pp(post_app['face_success_request_rate']-pre_app['face_success_request_rate'])}、端到端变化 {pp(post_app['e2e_rate']-pre_app['e2e_rate'])}。
- 这是“配置时间前后＋App横向参照”的相关性证据，不是随机实验。CSV没有`config_version`、客户端版本、渠道和首充金额，不能把全部差异都归因于门槛调整。

### 当前线上配置快照（2026-08-17核对）

| 配置 | App自然新增 | App非自然新增 | H5 | iOS |
|---|---:|---:|---:|---:|
| 首充带币触发门槛 | 900 | 900 | **500** | 1000 |
| 累计充值次数上限 | 3 | 1 | 3 | 3 |
| 累计充值金额上限 | 3000 | 2000 | 3000 | 3000 |
| 注册时间范围（天） | 180 | 180 | 180 | 3 |
| OTP / KYC V2 | 开 / 开 | 关 / 关 | 开 / 开 | 开 / 开 |

人脸正式配置为：总开关开启，高级BVN/NIN每日10次、间隔60秒，人脸每日5次，未成年人限制开启，FaceMatch阈值60。`kyc认证`表中的`matchPercent=90`是身份/KYC匹配阈值，不能与人脸`faceMatchPercent=60`混为一项。`face_reg_time`正式配置为空，需由研发确认空值语义及线上最终值。

## 五、App与H5差异

| 指标 | App | H5 | 差异解读 |
|---|---:|---:|---|
| 行动率 | {pct(app['action_rate'])} | {pct(h5['action_rate'])} | H5高{pp(h5['action_rate']-app['action_rate'])} |
| 调用后到达人脸 | {pct(app['face_reach_rate'])} | {pct(h5['face_reach_rate'])} | H5高{pp(h5['face_reach_rate']-app['face_reach_rate'])} |
| 人脸成功/请求 | {pct(app['face_success_request_rate'])} | {pct(h5['face_success_request_rate'])} | H5低{pp(h5['face_success_request_rate']-app['face_success_request_rate'])} |
| 无最终结果率 | {pct(app['face_unresolved_rate'])} | {pct(h5['face_unresolved_rate'])} | H5高{pp(h5['face_unresolved_rate']-app['face_unresolved_rate'])} |
| 端到端成功率 | {pct(app['e2e_rate'])} | {pct(h5['e2e_rate'])} | H5高{pp(h5['e2e_rate']-app['e2e_rate'])} |
| 人均人脸请求次数 | {num(app['attempts_per_user'],2)} | {num(h5['attempts_per_user'],2)} | H5多{num(h5['attempts_per_user']-app['attempts_per_user'],2)}次 |

H5前段转化更好，掩盖了人脸环节较差的问题。H5请求接口失败 {num(h5['request_error_attempts'])} 次，占H5当前失败原因 {pct(h5['request_error_share_retained'])}；App仅 {num(app['request_error_attempts'])} 次、占 {pct(app['request_error_share_retained'])}。H5异常集中在8月1日75次、8月13日53次、8月5日51次。

## 六、BVN与NIN

- 提现触发：NIN调用 {num(w['nin_calls'])} 次，通过率 **{pct(w['nin_pass_rate'])}**；BVN调用 {num(w['bvn_calls'])} 次，通过率 **{pct(w['bvn_pass_rate'])}**，相差 {pp(w['nin_pass_rate']-w['bvn_pass_rate'])}。
- App的BVN通过率 {pct(app['bvn_pass_rate'])}，H5仅 {pct(h5['bvn_pass_rate'])}，H5 BVN链路需单独排查姓名填写、输入校验、错误码和服务端响应。
- NIN（National Identification Number）为尼日利亚国家身份识别号码；BVN（Bank Verification Number）为银行验证号码。
- NIN优先展示有数据依据，但BVN用户是否都具备NIN不能由本表判断。若把BVN-only用户全部按NIN差值测算，理论身份通过机会约 {num(opp['bvn_only_pass_opportunity'])} 累计人次，只能视为上限，不是预测。

## 七、人脸失败与重试

- 25天共请求人脸 {num(w['face_request'])} 累计人次、{num(w['face_attempts'])} 次，人均 {num(w['attempts_per_user'],2)} 次。
- 明确失败 {num(w['face_fail'])} 累计人次，占请求人脸 {pct(w['face_fail_request_rate'])}。这是按每天去重后累计的用户层指标。
- 当前保留失败原因 {num(w['retained_fail_reasons'])} 次，其中人像不匹配 {num(w['mismatch_attempts'])} 次，占 {pct(w['mismatch_share_retained'])}。公式为“当前保留的人像不匹配次数÷当前保留失败原因次数”；它是重复尝试构成，不是用户不匹配率。
- 作为辅助诊断，人像不匹配次数占历史失败尝试 {pct(w['mismatch_share_history_fail'])}、占全部人脸请求次数 {pct(w['mismatch_share_all_face_attempts'])}；两者也都不是用户失败率。
- 成功用户历史失败原因会被清除，本表记录被清除 {num(w['cleared_fail_reasons'])} 次。因此当前失败原因分布不能代表所有历史尝试，建议保留不可变失败事件表。

## 八、主动认证

主动填写表可观测人群按“实际调用＋未调用”推算为 {num(active['trigger'])} 累计人次，身份调用率 {pct(active['action_rate'])}，最终人脸成功 {num(active['face_success'])}，推算端到端仅 {pct(active['e2e_rate'])}。但源表没有明确的页面曝光字段，因此该端到端率只能作为内部观察值，不应直接进入正式经营KPI。

## 九、两阶段对比结论

- 7月23日至26日为配置调整前基线，7月27日至8月16日为调整后阶段，均依据最新导出数据重新核算。
- 整体端到端由 {pct(pre_all['e2e_rate'])} 变为 {pct(post_all['e2e_rate'])}；App成功/请求变化 {pp(post_app['face_success_request_rate']-pre_app['face_success_request_rate'])}，整体稳定。
- H5成功/请求由 {pct(pre_h5['face_success_request_rate'])} 降至 {pct(post_h5['face_success_request_rate'])}，无最终结果由 {pct(pre_h5['face_unresolved_rate'])} 升至 {pct(post_h5['face_unresolved_rate'])}，应优先排查扩量后的H5认证承接和技术链路。
- 人像不匹配仍是当前保留失败尝试的第一原因，但不能把 {pct(w['mismatch_share_retained'])} 解读为用户失败率。用户层面的明确失败/请求为 {pct(w['face_fail_request_rate'])}。

## 十、问题定位与优化方案

### P0：统一漏斗分母与状态

将“触发、实际调用、请求人脸、已有最终结果、最终成功”同时展示，禁止只写“人脸成功率”。看板固定并列显示触发口径、请求口径和完成口径。

### P0：把H5 500门槛做成可追踪灰度

H5门槛900→500后，日均触发增长 {pct(h5_daily_after/h5_daily_before-1)}，但成功/请求下降 {pp(post_h5['face_success_request_rate']-pre_h5['face_success_request_rate'])}、无结果上升 {pp(post_h5['face_unresolved_rate']-pre_h5['face_unresolved_rate'])}。后续配置调整必须携带`config_version`、命中规则和首充金额段，按同日同渠道比较500/900人群；目标是成功/请求恢复至不低于 {pct(pre_h5['face_success_request_rate'])}，护栏为风险拦截率、提现损失和三方调用成本。

### P0：专项排查H5请求接口失败

H5贡献 {pct(h5['request_error_attempts']/w['request_error_attempts'])} 的请求接口失败，却只占 {pct(h5['face_request']/w['face_request'])} 的人脸请求。增加request_id、浏览器、网络、H5 build、接口耗时、HTTP/业务错误码；单日超过30次或占当前失败原因超过5%即告警。

### P0：优化人像不匹配后的重试与替代路径

在采集页增加光线、距离、遮挡、镜头权限的实时提示；连续2次不匹配后切换更明确的操作指导，仍失败则进入人工复核或证件替代方案。验证指标为首次成功率、重试挽回率和人均请求次数；护栏是欺诈通过率、人工审核量和三方费用。

### P1：NIN优先，BVN提供明确错误修复

NIN通过率比BVN高 {pp(w['nin_pass_rate']-w['bvn_pass_rate'])}。默认突出NIN；BVN失败按不存在、姓名不一致、冻结、系统错误分别提示，不再统一返回模糊失败。

### P1：减少无操作和无最终结果

触发后未调用 {num(w['not_called'])} 累计人次，占总流失 {pct(losses[0]['share'])}；人脸请求后无最终结果 {num(w['face_unresolved'])} 累计人次，占请求 {pct(w['face_unresolved_rate'])}。增加认证目的和隐私说明、保存进度、返回后续接、退出挽留，并单独埋点关闭、超时、权限拒绝和网络中断。

### P2：补齐新手机号—银行卡流程与提现结果

当前CSV没有手机号绑定、手机号查BVN、银行卡匹配或最终提现结果，无法评价新流程。上线前必须补齐完整状态机并记录流程版本、配置版本和生效时间；旧流程与新流程不能在报表中混算。

## 十一、当前数据缺口

- 无渠道、客户端版本、风险配置版本，不能进行渠道和版本因果分析。
- 无银行校验通过、提现提交和提现成功字段，当前“最终成功”仅代表人脸成功。
- 无手机号新流程字段，无法判断新版机制是否已上线或有效。
- 失败原因按次数而非用户统计；成功后原因被清除，历史分布不完整。
- 源表无“身份通过人数”“Face SDK拉起成功”“相机权限”“主动退出/黑屏”等拆分字段，暂时无法完整定位身份通过后至人脸结果之间的流失环节。

## 核心数据来源

- 提现触发人脸认证统计（2026-08-17导出）
- 主动填写人脸认证统计（2026-08-17导出）
- [线上KYC配置表（kyc认证）]({SOURCE_URLS['线上KYC配置']})
- [线上人脸识别配置表]({SOURCE_URLS['线上人脸识别配置']})
- KYC人脸识别核心设计逻辑与机制拆解（2026-08-17）
"""
    return md


def build_html(data: dict, normalized: pd.DataFrame) -> str:
    w = data["summary"]["提现触发"]["全部"]
    app = data["summary"]["提现触发"]["App"]
    h5 = data["summary"]["提现触发"]["H5"]
    active = data["summary"]["主动填写"]["全部"]
    losses = data["losses"]
    opp = data["opportunity"]
    weekly = [r for r in data["weekly"] if r["flow"] == "提现触发" and r["platform"] == "全部"]
    weekly_app = [r for r in data["weekly"] if r["flow"] == "提现触发" and r["platform"] == "App"]
    weekly_h5 = [r for r in data["weekly"] if r["flow"] == "提现触发" and r["platform"] == "H5"]
    phase_all = [x for x in data["phases"] if x["flow"] == "提现触发" and x["platform"] == "全部"]
    phase_app = [x for x in data["phases"] if x["flow"] == "提现触发" and x["platform"] == "App"]
    phase_h5 = [x for x in data["phases"] if x["flow"] == "提现触发" and x["platform"] == "H5"]
    pre_all, post_all = phase_all
    pre_app, post_app = phase_app
    pre_h5, post_h5 = phase_h5
    h5_daily_before = pre_h5["trigger"] / pre_h5["days"]
    h5_daily_after = post_h5["trigger"] / post_h5["days"]
    app_daily_before = pre_app["trigger"] / pre_app["days"]
    app_daily_after = post_app["trigger"] / post_app["days"]
    trend_labels = ["07-23至07-26"] + [x["period"] for x in weekly]
    trend_all = [pre_all] + weekly
    trend_app = [pre_app] + weekly_app
    trend_h5 = [pre_h5] + weekly_h5

    funnel_svg = svg_funnel([
        ("风险提现触发", w["trigger"]),
        ("实际调用BVN/NIN", w["actual"]),
        ("请求人脸识别", w["face_request"]),
        ("形成最终人脸结果", w["face_completed"]),
        ("最终人脸成功", w["face_success"]),
    ])
    platform_svg = svg_grouped_bars(
        ["行动率", "到达人脸", "人脸成功/请求", "有结果成功率", "无最终结果", "端到端"],
        [
            ("App", [app["action_rate"], app["face_reach_rate"], app["face_success_request_rate"], app["face_success_completed_rate"], app["face_unresolved_rate"], app["e2e_rate"]], "#2F80C9"),
            ("H5", [h5["action_rate"], h5["face_reach_rate"], h5["face_success_request_rate"], h5["face_success_completed_rate"], h5["face_unresolved_rate"], h5["e2e_rate"]], "#45A779"),
        ],
    )
    method_svg = svg_grouped_bars(
        ["App BVN", "App NIN", "H5 BVN", "H5 NIN"],
        [("通过率", [app["bvn_pass_rate"], app["nin_pass_rate"], h5["bvn_pass_rate"], h5["nin_pass_rate"]], "#2F80C9")],
    )
    weekly_svg = svg_lines(
        trend_labels,
        [
            ("行动率", [x["action_rate"] for x in trend_all], "#2F80C9"),
            ("人脸成功/请求", [x["face_success_request_rate"] for x in trend_all], "#45A779"),
            ("端到端", [x["e2e_rate"] for x in trend_all], "#F1B735"),
            ("无最终结果", [x["face_unresolved_rate"] for x in trend_all], "#EF7B78"),
        ],
    )
    daily_withdraw = normalized[normalized["流程"] == "提现触发"].copy()
    daily_withdraw["日期"] = pd.to_datetime(daily_withdraw["日期"])
    phase_svg = svg_daily_kyc_trend(daily_withdraw)
    error_svg = svg_daily_errors(daily_withdraw)

    loss_rows = [[x["stage"], f'<b>{num(x["count"])}</b>', pct(x["share"])] for x in losses]
    platform_rows = [
        ["行动率", pct(app["action_rate"]), pct(h5["action_rate"]), pp(h5["action_rate"]-app["action_rate"])],
        ["实际调用→请求人脸", pct(app["face_reach_rate"]), pct(h5["face_reach_rate"]), pp(h5["face_reach_rate"]-app["face_reach_rate"])],
        ["人脸成功/请求", pct(app["face_success_request_rate"]), pct(h5["face_success_request_rate"]), pp(h5["face_success_request_rate"]-app["face_success_request_rate"])],
        ["已有结果中的成功率", pct(app["face_success_completed_rate"]), pct(h5["face_success_completed_rate"]), pp(h5["face_success_completed_rate"]-app["face_success_completed_rate"])],
        ["无最终结果率", pct(app["face_unresolved_rate"]), pct(h5["face_unresolved_rate"]), pp(h5["face_unresolved_rate"]-app["face_unresolved_rate"])],
        ["端到端成功率", pct(app["e2e_rate"]), pct(h5["e2e_rate"]), pp(h5["e2e_rate"]-app["e2e_rate"])],
        ["人均人脸请求次数", num(app["attempts_per_user"],2), num(h5["attempts_per_user"],2), f"{h5['attempts_per_user']-app['attempts_per_user']:+.2f}"],
    ]
    weekly_rows=[]
    for label, a, h in zip(trend_labels, trend_app, trend_h5):
        weekly_rows.append([label, pct(a["action_rate"]), pct(h["action_rate"]), pct(a["e2e_rate"]), pct(h["e2e_rate"]), pct(a["face_unresolved_rate"]), pct(h["face_unresolved_rate"])])
    phase_rows = []
    for a, ap, h in zip(phase_all, phase_app, phase_h5):
        phase_rows.append([
            a["phase_short"],
            num(h["trigger"]/h["days"]),
            pct(h["trigger"]/a["trigger"]),
            pct(h["face_success_request_rate"]),
            pct(h["face_unresolved_rate"]),
            pct(h["e2e_rate"]),
            pct(ap["face_success_request_rate"]),
            pct(ap["e2e_rate"]),
        ])
    comparison_rows = []
    for platform, before, after in [("全部", pre_all, post_all), ("App", pre_app, post_app), ("H5", pre_h5, post_h5)]:
        comparison_rows.append([
            platform,
            f"{num(before['trigger']/before['days'])} → {num(after['trigger']/after['days'])}",
            f"{pct(before['action_rate'])} → {pct(after['action_rate'])}",
            f"{pct(before['face_success_request_rate'])} → {pct(after['face_success_request_rate'])}（{pp(after['face_success_request_rate']-before['face_success_request_rate'])}）",
            f"{pct(before['face_unresolved_rate'])} → {pct(after['face_unresolved_rate'])}（{pp(after['face_unresolved_rate']-before['face_unresolved_rate'])}）",
            f"{pct(before['e2e_rate'])} → {pct(after['e2e_rate'])}（{pp(after['e2e_rate']-before['e2e_rate'])}）",
        ])
    errors = data["top_request_errors"][:6]
    error_rows=[[x["date"],x["platform"],num(x["count"]),pct(x["count"]/x["all_current_reasons"] if x["all_current_reasons"] else None)] for x in errors]
    sources_html = "".join([
        f'<li><a href="{SOURCE_URLS["线上KYC配置"]}">线上KYC配置表（kyc认证）</a></li>',
        f'<li><a href="{SOURCE_URLS["线上人脸识别配置"]}">线上人脸识别配置表</a></li>',
        '<li>提现触发人脸认证统计（2026-08-17导出）</li>',
        '<li>主动填写人脸认证统计（2026-08-17导出）</li>',
        '<li>KYC人脸识别核心设计逻辑与机制拆解（2026-08-17）</li>',
    ])

    css = """
    :root{--ink:#15324f;--muted:#607b95;--blue:#2f80c9;--blue2:#eaf5ff;--green:#45a779;--green2:#eaf8f1;--yellow:#f1c64b;--yellow2:#fff8df;--red:#df6865;--red2:#fff0ef;--line:#cfe1ee;--paper:#fff;--bg:#f3f9fc}
    *{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#eef8fd,#f8fbf4 48%,#f5fbff);color:var(--ink);font:16px/1.68 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}.page{width:min(1220px,calc(100% - 34px));margin:24px auto 64px}.hero{padding:42px;border-radius:28px;background:linear-gradient(135deg,#12395f,#286f9c 54%,#3c9a81);color:#fff;box-shadow:0 20px 45px #1b57731c}.eyebrow{font-size:13px;letter-spacing:.12em;text-transform:uppercase;opacity:.8}.hero h1{font-size:38px;line-height:1.2;margin:10px 0}.meta{display:flex;gap:12px;flex-wrap:wrap;margin-top:22px}.pill{display:inline-flex;padding:7px 12px;border-radius:999px;background:#ffffff20;border:1px solid #ffffff38;font-size:13px}.hero-summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:22px}.hero-point{position:relative;padding:17px 18px 16px 52px;border-radius:17px;background:#ffffff14;border:1px solid #ffffff2e;min-height:126px}.hero-point .index{position:absolute;left:16px;top:17px;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;background:#fff;color:#1f628d;font-weight:850}.hero-point strong{display:block;font-size:17px;margin-bottom:5px}.hero-point p{margin:0;color:#eef8ff;line-height:1.62}.notice{margin-top:18px;padding:13px 16px;border-radius:14px;background:#fff1b8;color:#614b00}.section{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:24px;padding:28px;margin-top:22px;box-shadow:0 12px 34px #2b6d8c10}.section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px}.section h2{font-size:27px;margin:0 0 6px}.section h3{font-size:20px;margin:24px 0 8px}.muted{color:var(--muted);margin:0}.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-top:18px}.kpi{padding:17px;border-radius:17px;background:var(--blue2);border:1px solid #d3e9f8}.kpi.green{background:var(--green2)}.kpi.yellow{background:var(--yellow2)}.kpi.red{background:var(--red2)}.kpi .label{font-size:13px;color:var(--muted)}.kpi strong{display:block;font-size:26px;line-height:1.15;margin:7px 0}.kpi small{color:var(--muted)}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}.callout{padding:18px;border-radius:16px;border-left:5px solid var(--blue);background:#f0f7fc}.callout.green{border-color:var(--green);background:#f1fbf6}.callout.yellow{border-color:#e8ad20;background:#fff9e9}.callout.red{border-color:var(--red);background:#fff4f3}.callout strong{font-size:18px}.metric{display:inline-block;padding:1px 7px;border-radius:7px;background:#dff1ff;color:#0c659d;font-weight:850}.metric.green{background:#daf3e6;color:#247452}.metric.yellow{background:#fff0b8;color:#8a6500}.metric.red{background:#ffe0de;color:#b83f3b}.hero-point .metric,.hero-point .metric.green,.hero-point .metric.yellow,.hero-point .metric.red{display:inline;padding:0;border-radius:0;background:transparent;color:inherit;font-weight:850}.chart{margin:18px 0 4px;padding:14px;border-radius:18px;background:#fbfdff;border:1px solid #dcebf4;overflow:auto}.chart svg{display:block;width:100%;height:auto;min-width:780px}.svg-label{font-size:15px;fill:#375875}.svg-value{font-size:17px;font-weight:700;fill:#fff}.grid{stroke:#dce8ef;stroke-width:1}.tick,.legend{font-size:12px;fill:#5f7890}.bar-label{font-size:12px;font-weight:700;fill:#24445f}.event-label{font-size:12px;font-weight:750;fill:#17658f}.event-label.danger{fill:#b94a46}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:16px;margin:14px 0}table{width:100%;border-collapse:collapse;min-width:700px}th{background:#edf6fb;color:#46677e;font-size:13px;text-align:left;padding:12px}td{padding:12px;border-top:1px solid #e1edf4;vertical-align:top}td:not(:first-child){text-align:right}tr:hover td{background:#f9fcfe}.flow{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:16px 0}.node{padding:10px 13px;border-radius:12px;background:var(--blue2);border:1px solid #cbe6f7;font-weight:650}.arrow{color:#7d96a9;font-size:20px}.priority{display:grid;grid-template-columns:70px 1.15fr 1fr 1fr;gap:0;border:1px solid var(--line);border-radius:16px;overflow:hidden;margin-top:14px}.priority>div{padding:13px;border-bottom:1px solid var(--line)}.priority>div:nth-child(-n+4){background:#edf6fb;font-weight:700}.priority .p0{color:#be423d;font-weight:800}.priority .p1{color:#b57600;font-weight:800}.priority .p2{color:#317a5d;font-weight:800}.tag{padding:5px 9px;border-radius:999px;background:var(--blue2);color:#2b6691;font-size:12px;white-space:nowrap}.appendix{background:#fbfdff}.foot{color:#678096;font-size:13px;padding:18px 4px}.source-list{columns:1}.source-list a{color:#236da2}.highlight-number{color:#0f699f;font-weight:800}.print-only{display:none}@media(max-width:900px){.hero-summary{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}.priority{grid-template-columns:55px 1fr}.priority>div:nth-child(4n+3),.priority>div:nth-child(4n+4){display:none}.hero{padding:28px}.hero h1{font-size:30px}.section{padding:20px}}@media(max-width:620px){body{font-size:15px}.page{width:min(100% - 18px,1220px);margin-top:10px}.hero{padding:23px 18px;border-radius:20px}.hero h1{font-size:27px}.hero-point{padding:15px 14px 15px 48px;min-height:0}.section{padding:18px 15px;border-radius:18px}.section h2{font-size:23px}.kpis{grid-template-columns:1fr 1fr}.kpi strong{font-size:22px}.chart{padding:8px}.table-wrap{margin-left:-2px;margin-right:-2px}}@media print{body{background:#fff}.page{width:100%;margin:0}.hero,.section{box-shadow:none;break-inside:avoid}.section{margin-top:12px}.chart{break-inside:avoid}.print-only{display:block}a{color:inherit;text-decoration:none}}
    """

    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Waje KYC人脸识别与提现认证深度分析</title><style>{css}</style></head><body><main class="page">
    <header class="hero"><div class="eyebrow">Waje · KYC / Face Verification</div><h1>Waje KYC人脸识别与提现认证深度分析</h1><div class="hero-summary"><article class="hero-point"><span class="index">1</span><strong>综述</strong><p>报告覆盖2026年7月23日至8月16日共25个完整自然日，分析<span class="metric">{num(w['trigger'])}次提现触发</span>（每天按用户去重后累计），并横向比较App与H5认证表现。</p></article><article class="hero-point"><span class="index">2</span><strong>核心数据与判断</strong><p>最终人脸成功占全部触发<span class="metric yellow">{pct(w['e2e_rate'])}</span>；按人脸请求计算成功率为<span class="metric green">{pct(w['face_success_request_rate'])}</span>，另有<span class="metric red">{num(w['face_unresolved'])}累计人次</span>未形成最终结果。</p></article><article class="hero-point"><span class="index">3</span><strong>发现的问题</strong><p><span class="metric">7月27日23:20</span>，H5首充带币触发门槛由<span class="metric yellow">900降至500</span>。调整后<span class="metric green">H5覆盖扩大</span>，但<span class="metric red">成功/请求下降、无结果率上升</span>；同期<span class="metric green">App整体稳定</span>。</p></article><article class="hero-point"><span class="index">4</span><strong>游戏侧需解决的问题</strong><p>优先治理H5相机与Face SDK拉起、请求接口稳定性和断点续接；补齐退出、黑屏、权限拒绝、弱网及配置版本字段，并将门槛调整纳入可追踪灰度。</p></article></div><div class="meta"><span class="pill">数据：2026-07-23—2026-08-16</span><span class="pill">50行/表 · 25天 · App/H5</span><span class="pill">配置切点：2026-07-27 23:20</span><span class="pill">8月17日未完整，已排除</span></div></header>

    <section class="section"><div class="section-head"><div><h2>1. 核心经营与体验判断</h2><p class="muted">各项指标按对应阶段定义分母，避免将触发、请求和已有结果三种口径混用。</p></div><span class="tag">提现触发主漏斗</span></div><div class="callout yellow"><strong>统计单位说明</strong><p>报告中的“累计人次”是每天先按用户去重，再将每天人数相加；同一用户在不同日期出现会被重复计算。因此<span class="metric yellow">{num(w['trigger'])}累计人次</span>不代表25天内有{num(w['trigger'])}名独立用户。</p></div><div class="kpis">
      <div class="kpi"><span class="label">风险提现触发</span><strong>{num(w['trigger'])}</strong><small>累计人次</small></div>
      <div class="kpi green"><span class="label">实际调用BVN/NIN</span><strong>{pct(w['action_rate'])}</strong><small>{num(w['actual'])} 累计人次</small></div>
      <div class="kpi yellow"><span class="label">最终人脸成功/触发</span><strong>{pct(w['e2e_rate'])}</strong><small>{num(w['face_success'])} 累计人次</small></div>
      <div class="kpi"><span class="label">最终成功/请求人脸</span><strong>{pct(w['face_success_request_rate'])}</strong><small>{num(w['face_success'])}/{num(w['face_request'])}</small></div>
      <div class="kpi green"><span class="label">有结果用户中的成功率</span><strong>{pct(w['face_success_completed_rate'])}</strong><small>{num(w['face_success'])}/{num(w['face_completed'])}</small></div>
      <div class="kpi red"><span class="label">请求后无最终结果</span><strong>{pct(w['face_unresolved_rate'])}</strong><small>{num(w['face_unresolved'])} 累计人次</small></div>
    </div><div class="grid2" style="margin-top:18px"><article class="callout"><strong>7月27日H5降门槛后，覆盖扩大</strong><p>H5日均触发约由<span class="metric">{num(h5_daily_before)}</span>增至<span class="metric">{num(h5_daily_after)}</span>人次/日，增长<span class="metric green">{pct(h5_daily_after/h5_daily_before-1)}</span>；H5触发占比由<span class="metric">{pct(pre_h5['trigger']/pre_all['trigger'])}</span>升至<span class="metric">{pct(post_h5['trigger']/post_all['trigger'])}</span>。同期App日均触发增长{pct(app_daily_after/app_daily_before-1)}。</p></article><article class="callout red"><strong>扩量没有同步转成认证质量</strong><p>H5成功/请求由<span class="metric yellow">{pct(pre_h5['face_success_request_rate'])}</span>降至<span class="metric red">{pct(post_h5['face_success_request_rate'])}</span>，无最终结果由<span class="metric yellow">{pct(pre_h5['face_unresolved_rate'])}</span>升至<span class="metric red">{pct(post_h5['face_unresolved_rate'])}</span>；同期App成功/请求变化仅{pp(post_app['face_success_request_rate']-pre_app['face_success_request_rate'])}。</p></article></div></section>

    <section class="section"><div class="section-head"><div><h2>2. 提现触发认证漏斗</h2><p class="muted">从风险触发到人脸成功；当前CSV没有银行校验和最终提现结果，因此漏斗止于人脸成功。</p></div><span class="tag">{num(w['trigger'])} 累计人次</span></div><div class="chart">{funnel_svg}</div><h3>总流失由四段构成</h3>{table(["流失阶段","累计人次","占全部流失"],loss_rows)}<div class="callout yellow"><strong>人脸阶段核心指标须按分母分别呈现</strong><p>已有最终结果用户中的成功率为<span class="metric green">{pct(w['face_success_completed_rate'])}</span>；按全部人脸请求计算，成功率为<span class="metric yellow">{pct(w['face_success_request_rate'])}</span>；另有<span class="metric red">{num(w['face_unresolved'])}累计人次</span>未形成最终成功或失败，占人脸请求<span class="metric red">{pct(w['face_unresolved_rate'])}</span>。三项指标反映不同问题，必须并列解读。</p></div></section>

    <section class="section"><div class="section-head"><div><h2>3. 人脸阶段结果拆解：先识别无结果，再分析成败</h2><p class="muted">先区分未形成结果的人群，再在已有最终结果者中拆分成功和失败，最后分析失败尝试原因。</p></div><span class="tag">分层漏斗口径</span></div>{table(["人脸阶段层级","累计人次","正确分母","说明"],[["请求人脸识别",num(w['face_request']),"—","当前CSV可直接观测的人脸阶段入口"],["无最终结果",num(w['face_unresolved']),pct(w['face_unresolved_rate'])+" / 请求","含主动退出、黑屏/摄像头未拉起、未完成或在途"],["已有最终结果",num(w['face_completed']),pct(w['face_completed']/w['face_request'])+" / 请求","最终成功＋明确失败"],["其中成功",num(w['face_success']),pct(w['face_success_completed_rate'])+" / 已有结果","不可与触发口径混用"],["其中明确失败",num(w['face_fail']),pct(w['face_fail_request_rate'])+" / 请求","用户层面的失败指标"]])}<div class="callout red"><strong>当前仍缺一个关键阶段</strong><p>CSV没有“至少一种BVN/NIN认证通过人数”，所以无法准确计算“身份通过后未请求人脸”的人数；只能用请求人脸人数作为下一阶段代理。后续必须补身份通过、Face SDK拉起、相机权限、开始采集、主动退出和黑屏错误。</p></div></section>

    <section class="section"><div class="section-head"><div><h2>4. 7月27日H5触发门槛调整前后</h2><p class="muted">配置表确认：H5 config_11 的 firstRechargeBalance 于7月27日23:20由900降至500，之后未再调整。</p></div><span class="tag">配置切点分析</span></div><h3>7月23日至8月16日连续趋势</h3><p class="muted">曲线展示每日App/H5人脸成功率、H5无最终结果率及H5触发占比；竖线标注配置变更与请求接口异常日期。</p><div class="chart">{phase_svg}</div>{table(["配置窗口","H5日均触发（人次/日）","H5触发占比","H5成功/请求","H5无结果率","H5端到端","App成功/请求","App端到端"],phase_rows)}<div class="grid2"><article class="callout green"><strong>门槛下调扩大了H5覆盖</strong><p>H5日均触发增长{pct(h5_daily_after/h5_daily_before-1)}，H5在全部触发中的占比提高{pp(post_h5['trigger']/post_all['trigger']-pre_h5['trigger']/pre_all['trigger'])}；同期App日均触发仅增长{pct(app_daily_after/app_daily_before-1)}。</p></article><article class="callout red"><strong>新增覆盖没有同步转化</strong><p>调整后H5请求后成功下降{pp(post_h5['face_success_request_rate']-pre_h5['face_success_request_rate'])}、无最终结果上升{pp(post_h5['face_unresolved_rate']-pre_h5['face_unresolved_rate'])}、端到端下降{pp(post_h5['e2e_rate']-pre_h5['e2e_rate'])}；同期App端到端变化{pp(post_app['e2e_rate']-pre_app['e2e_rate'])}。</p></article></div><div class="callout yellow"><strong>备注</strong><p>本节为具有明确配置切点、并以App作为横向参照的前后观察。由于导出数据未包含config_version、首充金额、渠道和真实客户端版本，结果用于判断变化方向与排查优先级，不作为单一配置变更的因果证明。</p></div><h3>当前触发配置矩阵</h3>{table(["人群/端","配置","首充带币门槛","累计充值次数上限","累计充值金额上限","注册时间范围","OTP / KYC V2"],[["App自然新增","config_4","900","3","3000","180天","开 / 开"],["App非自然新增","config_2","900","1","2000","180天","关 / 关"],["H5","config_11","<b>500</b>","3","3000","180天","开 / 开"],["iOS","config_3","1000","3","3000","3天","开 / 开"]])}<h3>人脸正式配置</h3><div class="kpis" style="grid-template-columns:repeat(5,1fr)"><div class="kpi green"><span class="label">人脸总开关</span><strong>开启</strong><small>withdraw_face_open</small></div><div class="kpi"><span class="label">高级IDV每日次数</span><strong>10</strong><small>间隔60秒</small></div><div class="kpi"><span class="label">人脸每日次数</span><strong>5</strong><small>三方调用计费边界</small></div><div class="kpi yellow"><span class="label">FaceMatch阈值</span><strong>60</strong><small>人脸相似度</small></div><div class="kpi red"><span class="label">face_reg_time</span><strong>空</strong><small>需确认空值语义</small></div></div><div class="callout"><strong>身份匹配与人脸相似度采用不同阈值</strong><p><code>kyc认证.matchPercent=90</code>用于身份/KYC匹配；<code>人脸识别配置.faceMatchPercent=60</code>用于人像相似度。报表、告警和实验必须分别记录，避免混用。</p></div></section>

    <section class="section"><div class="section-head"><div><h2>5. App与H5：前段与人脸阶段方向相反</h2><p class="muted">H5前段更愿意继续，但人脸阶段成功更低、未决更多、请求次数更高。</p></div><span class="tag">包名映射口径</span></div><div class="chart">{platform_svg}</div>{table(["指标","App","H5","H5-App"],platform_rows)}<div class="grid2"><article class="callout green"><strong>H5端到端较高来自前段优势</strong><p>H5端到端<span class="metric green">{pct(h5['e2e_rate'])}</span>，高于App <span class="metric">{pct(app['e2e_rate'])}</span>，原因是H5行动率和到达人脸率更高；不能据此判断H5人脸体验更优。</p></article><article class="callout red"><strong>H5人脸体验有技术故障信号</strong><p>H5仅占<span class="metric">{pct(h5['face_request']/w['face_request'])}</span>的人脸请求，却贡献<span class="metric red">{pct(h5['request_error_attempts']/w['request_error_attempts'])}</span>的请求接口失败。<span class="metric red">8月1日、8月5日、8月13日</span>有明显尖峰。</p></article></div></section>

    <section class="section"><div class="section-head"><div><h2>6. 分阶段趋势：整体稳定，端侧结构在变化</h2><p class="muted">增加7月23日至26日调整前基线，随后按三个完整自然周观察行动率、请求后成功、无最终结果和端到端表现。</p></div><span class="tag">基线4天＋3个完整周</span></div><div class="chart">{weekly_svg}</div>{table(["周期","App行动率","H5行动率","App端到端","H5端到端","App无结果","H5无结果"],weekly_rows)}<p class="muted">7月23日至26日为配置调整前基线；后续三个周期均为完整7天。H5行动率保持较高，但人脸请求后的成功表现弱于App，无最终结果率也更高，问题主要集中在人脸链路而非是否开始认证。</p></section>

    <section class="section"><div class="section-head"><div><h2>7. NIN稳定领先，H5 BVN是短板</h2><p class="muted">通过率按各自调用人数计算；同时调用两种方式的用户会分别进入两种方法统计。</p></div><span class="tag">方法比较</span></div><div class="callout"><strong>名词说明</strong><p><b>NIN</b>（National Identification Number）是尼日利亚国家身份识别号码；<b>BVN</b>（Bank Verification Number）是银行验证号码，用于关联和验证银行账户实名身份。</p></div><div class="chart">{method_svg}</div><div class="grid2"><article class="callout green"><strong>NIN：{pct(w['nin_pass_rate'])}</strong><p>{num(w['nin_calls'])}次调用，显著高于BVN的{pct(w['bvn_pass_rate'])}，差{pp(w['nin_pass_rate']-w['bvn_pass_rate'])}。继续以NIN为默认入口有数据依据。</p></article><article class="callout red"><strong>H5 BVN：{pct(h5['bvn_pass_rate'])}</strong><p>比App BVN低{pp(h5['bvn_pass_rate']-app['bvn_pass_rate'])}。应从姓名输入规则、BVN不存在/冻结、接口错误和H5输入体验逐项拆原因。</p></article></div><div class="callout yellow"><strong>机会空间，不是预测</strong><p>若全部BVN-only用户都能使用NIN，按当前方法差值测算，理论可多通过约 <span class="highlight-number">{num(opp['bvn_only_pass_opportunity'])}</span> 累计人次；现实中并非所有BVN用户都有可用NIN，因此只能作为上限。</p></div></section>

    <section class="section"><div class="section-head"><div><h2>8. 人脸失败：用户结果与尝试原因分层分析</h2><p class="muted">明确失败率按每天去重后累计人数计算；人像不匹配占比按当前保留的失败原因次数计算，二者不能混用。</p></div><span class="tag">{num(w['history_fail_attempts'])} 历史失败尝试</span></div><div class="kpis" style="grid-template-columns:repeat(4,1fr)"><div class="kpi red"><span class="label">明确失败/请求人脸</span><strong>{pct(w['face_fail_request_rate'])}</strong><small>{num(w['face_fail'])} 累计人次</small></div><div class="kpi yellow"><span class="label">不匹配/当前原因</span><strong>{pct(w['mismatch_share_retained'])}</strong><small>{num(w['mismatch_attempts'])}/{num(w['retained_fail_reasons'])} 次</small></div><div class="kpi"><span class="label">不匹配/历史失败尝试</span><strong>{pct(w['mismatch_share_history_fail'])}</strong><small>辅助诊断，非用户率</small></div><div class="kpi green"><span class="label">不匹配/全部人脸尝试</span><strong>{pct(w['mismatch_share_all_face_attempts'])}</strong><small>辅助诊断，非用户率</small></div></div><div class="callout yellow"><strong>人像不匹配占比的正确解释</strong><p>计算公式为“当前保留人像不匹配次数÷当前保留失败原因次数”。同一用户可多次失败；成功用户此前的{num(w['cleared_fail_reasons'])}条失败原因还会被清除。因此该指标只能描述当前失败尝试构成，不能表示用户不匹配率。用户层面的明确失败/请求为{pct(w['face_fail_request_rate'])}。</p></div><h3>请求接口失败的每日尖峰</h3><div class="chart">{error_svg}</div>{table(["日期","端","请求接口失败次数","占当日当前失败原因"],error_rows)}<div class="callout red"><strong>定位优先级：H5请求链路</strong><p>优先补request_id、浏览器、网络类型、H5 build、SDK版本、HTTP码、业务码和接口耗时。单日失败超过30次或占当前失败原因超过5%时告警，并关联发布和第三方服务状态。</p></div></section>

    <section class="section"><div class="section-head"><div><h2>9. 主动认证：起始与持续完成均存在阻力</h2><p class="muted">源表没有页面曝光字段，以下“可观测人群”由实际调用＋未调用推算，仅作为辅助分析。</p></div><span class="tag">辅助观察指标</span></div><div class="kpis" style="grid-template-columns:repeat(5,1fr)"><div class="kpi"><span class="label">推算可观测人群</span><strong>{num(active['trigger'])}</strong><small>累计人次</small></div><div class="kpi yellow"><span class="label">身份调用率</span><strong>{pct(active['action_rate'])}</strong><small>{num(active['actual'])}</small></div><div class="kpi"><span class="label">调用后请求人脸</span><strong>{pct(active['face_reach_rate'])}</strong><small>{num(active['face_request'])}</small></div><div class="kpi red"><span class="label">请求后无最终结果</span><strong>{pct(active['face_unresolved_rate'])}</strong><small>{num(active['face_unresolved'])}</small></div><div class="kpi green"><span class="label">推算端到端</span><strong>{pct(active['e2e_rate'])}</strong><small>{num(active['face_success'])}</small></div></div><p>主动流程和提现强制流程不能混算。主动流程的开始率和完成率明显更低，优化重点应放在认证价值与隐私说明、进度保存及退出后的可恢复能力，而不是单纯提高识别阈值。</p></section>

    <section class="section"><div class="section-head"><div><h2>10. 两阶段对比：调整前基线与调整后表现</h2><p class="muted">全部指标均依据最新导出数据重新核算：7月23日至26日为调整前，7月27日至8月16日为调整后。</p></div><span class="tag">同口径复算</span></div>{table(["端","日均触发（前→后）","行动率（前→后）","成功/请求（前→后）","无结果率（前→后）","端到端（前→后）"],comparison_rows)}<div class="callout"><strong>两阶段对比结论</strong><p>整体端到端由<span class="metric yellow">{pct(pre_all['e2e_rate'])}</span>变为<span class="metric yellow">{pct(post_all['e2e_rate'])}</span>，变化不大；App成功/请求保持稳定，而H5下降<span class="metric red">{pp(post_h5['face_success_request_rate']-pre_h5['face_success_request_rate'])}</span>、无最终结果上升<span class="metric red">{pp(post_h5['face_unresolved_rate']-pre_h5['face_unresolved_rate'])}</span>。因此排查应优先聚焦H5扩量后的认证承接和技术链路。</p></div></section>

    <section class="section"><div class="section-head"><div><h2>11. 最新机制与线上配置的对应关系</h2></div><span class="tag">流程与配置核对</span></div><div class="flow"><span class="node">风险提现触发</span><span class="arrow">→</span><span class="node">OTP/手机号</span><span class="arrow">→</span><span class="node">BVN/NIN</span><span class="arrow">→</span><span class="node">官方人像/活体</span><span class="arrow">→</span><span class="node">FaceMatch</span><span class="arrow">→</span><span class="node">返回提现</span></div>{table(["机制/配置","当前状态","数据验证范围"],[["人脸总开关开启","withdraw_face_open=true","可验证进入和结果，缺实际开关版本"],["H5首充带币门槛500","7月27日更新，当前config_11快照为500","可做配置切点前后观察"],["高级IDV 10次/日、间隔60秒","线上配置已启用","缺限额和冷却命中事件"],["人脸5次/日、FaceMatch阈值60","线上配置已启用","可看尝试次数，缺相似度分数与限额事件"],["未成年人限制开启","线上配置已启用","当前导出无年龄与拦截结果"],["手机号→查询BVN→银行卡匹配","方案流程已定义","当前导出无法验证最终提现结果"],["face_reg_time为空","当前配置快照为空","需确认默认语义及线上实际生效值"]])}</section>

    <section class="section"><div class="section-head"><div><h2>12. 可执行优化</h2><p class="muted">每项包含证据、动作、验证指标与护栏。</p></div><span class="tag">P0→P2</span></div><div class="priority"><div>优先级</div><div>证据与问题</div><div>执行动作</div><div>验证与护栏</div><div class="p0">P0</div><div>无结果、成功、失败和失败原因曾被混成一个“人脸成功率”。</div><div>看板固定并列：身份通过、请求人脸、无结果、有结果成功/失败；失败原因另起一层。</div><div>同条件跨报表差异=0；无结果原因覆盖率&gt;95%。</div><div class="p0">P0</div><div>H5贡献{pct(h5['request_error_attempts']/w['request_error_attempts'])}请求接口失败，8/1、8/5、8/13尖峰。</div><div>补齐请求链路日志、H5 build和相机权限，建立日告警并关联发布。</div><div>接口失败占比&lt;5%；护栏为SDK成本和请求时延。</div><div class="p0">P0</div><div>明确失败/请求为{pct(w['face_fail_request_rate'])}；不匹配占当前失败尝试{pct(w['mismatch_share_retained'])}。</div><div>采集实时指导；连续2次失败切换增强提示，继续失败进入替代/人工复核。</div><div>首次成功率、重试挽回率；护栏为欺诈放行率。</div><div class="p1">P1</div><div>NIN通过率比BVN高{pp(w['nin_pass_rate']-w['bvn_pass_rate'])}，H5 BVN仅{pct(h5['bvn_pass_rate'])}。</div><div>NIN优先；BVN按不存在、姓名、冻结、系统错误给具体修复指引。</div><div>BVN通过率、方法切换成功率、客服咨询率。</div><div class="p1">P1</div><div>请求后无最终结果{num(w['face_unresolved'])}，H5高于App。</div><div>拆分主动退出、黑屏、摄像头未拉起、权限拒绝、弱网与在途；支持返回续接。</div><div>无结果率、恢复完成率；护栏为投诉与平均完成时长。</div><div class="p2">P2</div><div>无真实版本、配置版本、手机号、银行校验和最终提现数据。</div><div>按flow_version/config_version补齐状态机和配置生效时间。</div><div>可按真实版本对账；旧新开关不可同时开启。</div></div></section>

    <section class="section appendix"><div class="section-head"><div><h2>附录A：数据口径、质量与分析边界</h2><p class="muted">用于说明数据范围、指标解释和当前尚不能回答的问题。</p></div></div>{table(["检查项","结果","影响"],[["日期与完整性","7/23—8/16连续25天；8/17排除","通过"],["记录粒度","日期×包名；每表50行，无重复","区间人数按每天去重后累计，同一用户跨日可能重复"],["App/H5","仅两个包名，可比较端","不能下钻渠道"],["版本/配置","无真实app_version、web_build、config_version","仅能按事件日期切窗，不能做版本因果"],["身份阶段","无“至少一种身份认证通过人数”字段","请求人脸仅作下一阶段代理"],["人脸无结果","由请求－成功－失败推导","包含退出、黑屏/相机未拉起、未完成或在途"],["失败原因","按失败尝试次数；成功后原因被清除","不能当失败用户分布"],["提现后续","无银行校验与最终提现","报告漏斗止于人脸成功"]])}</section>

    <section class="section appendix"><h2>附录B：核心数据来源</h2><ul class="source-list">{sources_html}</ul><p class="muted">核心分析直接使用两份最新认证统计导出、线上KYC与人脸识别配置，以及KYC核心机制文档。报告仅展示聚合结果。</p></section>
    <footer class="foot">Waje 数据产品分析 · 生成日期 2026-08-17 · 报告仅使用聚合数据，不包含姓名、手机号、BVN/NIN号码、银行卡号、人脸图片或特征值。</footer>
    </main></body></html>"""


def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    MD_OUT.parent.mkdir(parents=True, exist_ok=True)
    data, normalized = build_analysis()
    (WORK_DIR / "analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    normalized.to_csv(WORK_DIR / "normalized.csv", index=False, encoding="utf-8-sig")
    HTML_OUT.write_text(build_html(data, normalized), encoding="utf-8")
    MD_OUT.write_text(build_markdown(data), encoding="utf-8")
    print(json.dumps({"html": str(HTML_OUT), "markdown": str(MD_OUT), "analysis": str(WORK_DIR / "analysis.json"), "normalized": str(WORK_DIR / "normalized.csv")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
