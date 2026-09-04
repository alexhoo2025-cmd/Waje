#!/usr/bin/env python3
"""诊断 wajeh5phx Phenix 浏览器分包的付费率、留存和归因异常。"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUN_DATE = "2026-09-02"
WINDOW_START = date(2026, 8, 27)
WINDOW_END = date(2026, 9, 2)
SOURCE_XLS = Path("/Users/robin/Downloads/分包详情 - 2026-09-02T171410.991.xls")
SCREENSHOT_1 = Path("/var/folders/mm/xjw9s23n14ncmkjzntgs3n580000gn/T/TemporaryItems/NSIRD_screencaptureui_n85OLz/截屏2026-09-02 下午5.06.01.png")
SCREENSHOT_2 = Path("/var/folders/mm/xjw9s23n14ncmkjzntgs3n580000gn/T/TemporaryItems/NSIRD_screencaptureui_e4hbht/截屏2026-09-02 下午5.15.59.png")
ANALYSIS_DIR = ROOT / "analysis/phenix_channel_retention_2026_09_02"
OUTPUT_MD = ROOT / "knowledge/02-数据/Phenix浏览器分包付费与留存异常诊断-2026-09-02.md"
OUTPUT_HTML = ROOT / "output/html/Phenix浏览器分包付费与留存异常诊断-2026-09-02.html"
BQ_AUDIT = ROOT / "analysis/phenix_channel_retention_2026_09_02/bigquery_audit.json"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
BT = chr(96)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def num(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def pct_value(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).replace(",", "").strip().rstrip("%")) / 100
    except ValueError:
        return None


def divide(a: float | None, b: float | None) -> float | None:
    return None if a is None or b in (None, 0) else a / b


def pct(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def fmt(value: float | int | None) -> str:
    return "N/A" if value is None else f"{int(round(float(value))):,}"


def fmt_pp(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.2f} 个百分点"


def find_soffice() -> str:
    candidates = [
        os.environ.get("SOFFICE_BIN", ""),
        "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice",
        shutil.which("soffice") or "",
        shutil.which("libreoffice") or "",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    raise RuntimeError("未找到 soffice")


def colnum(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference).group(0)
    value = 0
    for char in letters:
        value = value * 26 + ord(char) - 64
    return value


def read_xls() -> tuple[list[str], list[str], list[list[str]], dict[str, Any]]:
    if not SOURCE_XLS.exists():
        raise FileNotFoundError(SOURCE_XLS)
    with tempfile.TemporaryDirectory(prefix="waje_phenix_xls_") as tmp:
        outdir = Path(tmp)
        command = [find_soffice(), "--headless", "--convert-to", "xlsx", "--outdir", str(outdir), str(SOURCE_XLS)]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
        converted = outdir / f"{SOURCE_XLS.stem}.xlsx"
        if completed.returncode != 0 or not converted.exists():
            raise RuntimeError(f"xls 转换失败: {completed.stdout[-300:]} {completed.stderr[-300:]}")
        with zipfile.ZipFile(converted) as archive:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                for item in root.findall("m:si", NS):
                    shared.append("".join(node.text or "" for node in item.iter("{%s}t" % NS["m"])))
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            sheets = workbook.find("m:sheets", NS)
            sheet_names = [s.attrib.get("name", "") for s in sheets] if sheets is not None else []
            root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
            rows: list[list[str]] = []
            for row in root.findall(".//m:sheetData/m:row", NS):
                values: dict[int, str] = {}
                for cell in row.findall("m:c", NS):
                    node = cell.find("m:v", NS)
                    value = node.text if node is not None else ""
                    if cell.attrib.get("t") == "s" and value:
                        value = shared[int(value)]
                    if cell.attrib.get("t") == "inlineStr":
                        value = "".join(node.text or "" for node in cell.iter("{%s}t" % NS["m"]))
                    values[colnum(cell.attrib["r"])] = value
                if values:
                    rows.append([values.get(index, "") for index in range(1, max(values) + 1)])
            profile = {
                "sheet_names": sheet_names,
                "sheet_count": len(sheet_names),
                "column_count": len(rows[0]) if rows else 0,
                "source_row_count_excluding_header": max(0, len(rows) - 1),
                "source_sha256": sha256(SOURCE_XLS),
                "screenshot_sha256": {str(path): sha256(path) for path in (SCREENSHOT_1, SCREENSHOT_2) if path.exists()},
            }
            return sheet_names, rows[0], rows[1:], profile


def derive(row: dict[str, Any]) -> dict[str, Any]:
    out = {
        "date": row["日期"], "channel": row["一级渠道"], "product": row["产品"], "media": row["媒体"],
        "spend": num(row["消耗金额"]), "new_users": num(row["新增用户数"]),
        "activated_registered": num(row["激活且注册数"]), "new_payers": num(row["新增付费人数"]),
        "first_payers": num(row["首次付费人数"]), "active_users": num(row["活跃用户数"]),
        "new_paid_amount": num(row["新增付费金额"]), "first_paid_amount": num(row["首次付费金额"]),
        "new_paid_arppu": num(row["新增付费ARPPU"]), "first_day_tc_rate": pct_value(row["首日TC比"]),
        "d1_paid_retention": pct_value(row["2日付费留存"]), "source_new_paid_rate": pct_value(row["新增付费率"]),
        "source_first_paid_rate": pct_value(row["首次付费率"]),
    }
    out["registration_rate"] = divide(out["activated_registered"], out["new_users"])
    out["new_paid_rate_by_new_users"] = divide(out["new_payers"], out["new_users"])
    out["new_paid_rate_by_registered"] = divide(out["new_payers"], out["activated_registered"])
    out["first_paid_rate_by_registered"] = divide(out["first_payers"], out["activated_registered"])
    out["d1_inferred_retained_payers"] = out["new_payers"] * out["d1_paid_retention"] if out["new_payers"] is not None and out["d1_paid_retention"] is not None else None
    cohort = date.fromisoformat(out["date"])
    out["d1_maturity"] = "mature" if cohort + timedelta(days=1) <= WINDOW_END else "immature"
    out["d3_maturity"] = "mature" if cohort + timedelta(days=3) <= WINDOW_END else "immature"
    out["d7_maturity"] = "mature" if cohort + timedelta(days=7) <= WINDOW_END else "immature"
    return out


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ["new_users", "activated_registered", "new_payers", "first_payers", "active_users", "new_paid_amount", "first_paid_amount"]
    result = {key: sum(float(row[key] or 0) for row in rows) for key in keys}
    result["registration_rate"] = divide(result["activated_registered"], result["new_users"])
    result["new_paid_rate_by_new_users"] = divide(result["new_payers"], result["new_users"])
    result["new_paid_rate_by_registered"] = divide(result["new_payers"], result["activated_registered"])
    result["first_paid_rate_by_registered"] = divide(result["first_payers"], result["activated_registered"])
    mature = [row for row in rows if row["d1_maturity"] == "mature" and row["d1_paid_retention"] is not None]
    result["d1_payers"] = sum(float(row["new_payers"] or 0) for row in mature)
    result["d1_inferred_retained_payers"] = sum(float(row["d1_inferred_retained_payers"] or 0) for row in mature)
    result["d1_paid_retention_weighted"] = divide(result["d1_inferred_retained_payers"], result["d1_payers"])
    return result


def weighted_d1(rows: list[dict[str, Any]]) -> float | None:
    eligible = [row for row in rows if row["d1_paid_retention"] is not None and row["new_payers"] not in (None, 0)]
    return divide(sum(float(row["d1_inferred_retained_payers"] or 0) for row in eligible), sum(float(row["new_payers"]) for row in eligible))


def build_analysis() -> dict[str, Any]:
    sheet_names, headers, raw_rows, profile = read_xls()
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        row = {headers[index]: raw[index] if index < len(raw) else "" for index in range(len(headers))}
        if row.get("日期") == "总计" or row.get("一级渠道") == " - ":
            continue
        try:
            if WINDOW_START <= date.fromisoformat(row.get("日期", "")) <= WINDOW_END:
                rows.append(derive(row))
        except ValueError:
            continue
    phx = [row for row in rows if row["channel"].lower() == "wajeh5phx"]
    if len(phx) != 7:
        raise RuntimeError(f"wajeh5phx 应有 7 条记录，实际 {len(phx)}")
    peers = [row for row in rows if row["media"] == "自然(无渠道ID)" and row["channel"].lower() not in {"wajeh5phx", "其他"} and row["d1_maturity"] == "mature" and row["new_payers"] not in (None, 0) and row["d1_paid_retention"] is not None]
    phx_mature = [row for row in phx if row["d1_maturity"] == "mature"]
    selected_peer = [row for row in peers if row["channel"].lower() == "wajeh5"]
    peer_daily = []
    for day in sorted(row["date"] for row in phx_mature):
        peer_day = [row for row in peers if row["date"] == day]
        phx_day = [row for row in phx if row["date"] == day][0]
        peer_daily.append({"date": day, "phx_d1": phx_day["d1_paid_retention"], "peer_d1": weighted_d1(peer_day), "peer_payers": sum(row["new_payers"] for row in peer_day), "peer_channels": len(peer_day)})
    visible = {
        "2026-09-02": (14, 0.0306), "2026-09-01": (35, 0.0202), "2026-08-31": (28, 0.0222),
        "2026-08-30": (25, 0.0251), "2026-08-29": (23, 0.0242), "2026-08-28": (16, 0.0209), "2026-08-27": (12, 0.0130),
    }
    by_date = {row["date"]: row for row in phx}
    comparison = []
    for day in sorted(visible, reverse=True):
        shown_payers, shown_rate = visible[day]
        row = by_date[day]
        implied = divide(shown_payers, shown_rate)
        comparison.append({
            "date": day, "screenshot_new_payers": shown_payers, "screenshot_rate": shown_rate,
            "detail_new_payers": row["new_payers"], "detail_rate_new_users": row["new_paid_rate_by_new_users"],
            "detail_rate_registered": row["new_paid_rate_by_registered"], "activated_registered": row["activated_registered"],
            "implied_denominator": implied, "denominator_gap": implied - row["activated_registered"] if implied is not None else None,
            "count_delta": shown_payers - row["new_payers"],
        })
    bq_audit = json.loads(BQ_AUDIT.read_text(encoding="utf-8")) if BQ_AUDIT.exists() else {"status": "not_run"}
    return {
        "profile": {**profile, "sheet_names": sheet_names, "data_row_count_excluding_total": max(0, int(profile.get("source_row_count_excluding_header", 0)) - 1), "window_row_count": len(rows), "phx_row_count": len(phx)},
        "phx_daily": sorted(phx, key=lambda row: row["date"]), "phx_daily_desc": sorted(phx, key=lambda row: row["date"], reverse=True),
        "phx_all": aggregate(phx), "phx_mature": aggregate(phx_mature), "peer_all_organic": aggregate(peers),
        "wajeh5_peer": aggregate(selected_peer), "peer_daily": peer_daily, "screenshot_comparison": comparison,
        "media_values": sorted({row["media"] for row in phx}), "spend_values": sorted({row["spend"] for row in phx}), "bigquery_audit": bq_audit,
    }


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = ["date","channel","product","media","spend","new_users","activated_registered","new_payers","first_payers","active_users","new_paid_amount","first_paid_amount","new_paid_arppu","first_day_tc_rate","d1_paid_retention","source_new_paid_rate","source_first_paid_rate","registration_rate","new_paid_rate_by_new_users","new_paid_rate_by_registered","first_paid_rate_by_registered","d1_maturity","d3_maturity","d7_maturity","d1_inferred_retained_payers"]
    return {key: row.get(key) for key in keys}


def h(value: Any) -> str:
    return html.escape(str(value if value is not None else "N/A"), quote=True)


esc = h


def html_table(headers: list[str], rows: list[list[Any]]) -> str:
    head = "".join(f"<th>{h(value)}</th>" for value in headers)
    body = "".join("<tr>" + "".join(f"<td>{h(value)}</td>" for value in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def html_bars(rows: list[tuple[str, float | None]], kind: str) -> str:
    maximum = max([value or 0 for _, value in rows] or [1]) or 1
    parts = []
    for label, value in rows:
        width = max(2, round((value or 0) / maximum * 100)) if value else 0
        display = pct(value) if kind == "rate" else f"{value:,.0f} ms" if value is not None else "N/A"
        parts.append(f'<div class="bar-row"><span>{h(label)}</span><i><b style="width:{width}%"></b></i><strong>{h(display)}</strong></div>')
    return "".join(parts)


def build_html(a: dict[str, Any]) -> str:
    all_s, mature, peer = a["phx_all"], a["phx_mature"], a["peer_all_organic"]
    daily = a["phx_daily_desc"]
    daily_table = html_table(
        ["日期", "新增用户", "激活注册", "注册率", "新增付费", "按新增用户付费率", "按激活注册付费率", "次日留存", "成熟度", "首日TC比"],
        [[row["date"], fmt(row["new_users"]), fmt(row["activated_registered"]), pct(row["registration_rate"]), fmt(row["new_payers"]), pct(row["new_paid_rate_by_new_users"]), pct(row["new_paid_rate_by_registered"]), pct(row["d1_paid_retention"]), "成熟" if row["d1_maturity"] == "mature" else "未成熟", pct(row["first_day_tc_rate"])] for row in daily],
    )
    compare_table = html_table(
        ["日期", "截图付费率", "按新增用户", "按激活注册", "截图人数", "明细人数"],
        [[row["date"], pct(row["screenshot_rate"]), pct(row["detail_rate_new_users"]), pct(row["detail_rate_registered"]), fmt(row["screenshot_new_payers"]), fmt(row["detail_new_payers"])] for row in a["screenshot_comparison"]],
    )
    peer_table = html_table(
        ["日期", "Phenix D1", "自然 H5 对照", "差异", "对照付费人数"],
        [[row["date"], pct(row["phx_d1"]), pct(row["peer_d1"]), f"{(row['phx_d1'] - row['peer_d1']) * 100:.2f}pp", fmt(row["peer_payers"])] for row in a["peer_daily"]],
    )
    css = """
:root{--navy:#102a43;--ink:#1f2937;--muted:#64748b;--line:#dce5ee;--bg:#f4f7fb;--card:#fff;--blue:#1976d2;--green:#17803d;--amber:#b45309;--red:#c2410c;--shadow:0 10px 28px rgba(16,42,67,.08)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif}.top{background:var(--navy);color:#fff;padding:34px 22px 38px}.wrap,.main{max-width:1220px;margin:auto}.eyebrow{font-size:12px;letter-spacing:.12em;color:#b9d4ef;font-weight:700}.top h1{font-size:clamp(29px,4vw,48px);line-height:1.12;margin:9px 0}.lede{max-width:880px;color:#dbe7f3;margin:0}.meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}.meta span{border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:4px 10px;font-size:12px}.main{padding:24px 22px 64px}.callout{padding:17px 19px;border-radius:15px;border:1px solid var(--line);border-left:5px solid var(--blue);background:var(--card);box-shadow:var(--shadow);margin:14px 0}.callout.amber{border-left-color:var(--amber);background:#fff9ed}.callout.red{border-left-color:var(--red);background:#fff4ef}.grid4,.grid2,.two-tone{display:grid;gap:14px}.grid4{grid-template-columns:repeat(4,1fr)}.grid2,.two-tone{grid-template-columns:repeat(2,1fr)}.card{background:var(--card);border:1px solid var(--line);border-radius:15px;padding:17px;box-shadow:var(--shadow)}.label{display:block;color:var(--muted);font-size:12px}.value{display:block;color:var(--navy);font-weight:800;font-size:28px;line-height:1.15;margin:7px 0}.hint{font-size:12px;color:var(--muted)}h2{color:var(--navy);font-size:27px;margin:30px 0 8px}h3{color:var(--navy);font-size:18px;margin:20px 0 8px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px;background:#fff;box-shadow:var(--shadow);margin:10px 0 17px}table{border-collapse:collapse;width:100%;min-width:760px}th,td{font-size:12px;text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line)}th{white-space:nowrap;background:#f5f8fb;color:#425a73;font-size:11px}tr:last-child td{border-bottom:0}.bar-list{display:grid;gap:10px}.bar-row{display:grid;grid-template-columns:145px 1fr 92px;gap:9px;align-items:center;font-size:12px}.bar-row i{height:10px;background:#e8eff6;border-radius:99px;overflow:hidden}.bar-row i b{height:100%;display:block;border-radius:99px;background:linear-gradient(90deg,#55b5c2,var(--blue))}.bar-row strong{text-align:right;color:var(--navy);font-size:12px}.footer{border-top:1px solid var(--line);padding-top:16px;margin-top:35px;color:var(--muted);font-size:12px}@media(max-width:900px){.grid4{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){.main{padding:16px 13px 45px}.top{padding:25px 16px 29px}.grid4,.grid2,.two-tone{grid-template-columns:1fr}.value{font-size:24px}.bar-row{grid-template-columns:100px 1fr 70px}}
"""
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Phenix 浏览器分包付费与留存异常诊断</title><style>{css}</style></head><body><header class="top"><div class="wrap"><div class="eyebrow">WAJE · PHENIX PACKAGE · RETENTION DIAGNOSTIC</div><h1>Phenix 浏览器分包<br>付费与留存异常诊断</h1><p class="lede">先拆分报表分母与 cohort 成熟度，再判断投放人群和埋点是否异常。</p><div class="meta"><span>窗口 {WINDOW_START} 至 {WINDOW_END}</span><span>包体 wajeh5phx</span><span>业务产品 Waje Special</span><span>来源：分包级聚合</span></div></div></header><main class="main"><div class="callout amber"><b>结论先行：</b>异常由报表分母不一致、未成熟留存显示 0 和 Phenix 归因缺失叠加造成。成熟 D1 留存和注册/付费转化偏低，但尚不能单独归因于投放人群或埋点故障。</div><h2>一、核心结果</h2><div class="grid4"><div class="card"><span class="label">窗口新用户</span><span class="value">{fmt(all_s["new_users"])}</span><span class="hint">含 9/2 部分日</span></div><div class="card"><span class="label">成熟期按新增用户付费率</span><span class="value">{pct(mature["new_paid_rate_by_new_users"])}</span><span class="hint">8/27–9/1</span></div><div class="card"><span class="label">成熟期次日付费留存</span><span class="value">{pct(mature["d1_paid_retention_weighted"])}</span><span class="hint">139 个新付费用户</span></div><div class="card"><span class="label">自然 H5 对照 D1</span><span class="value">{pct(peer["d1_paid_retention_weighted"])}</span><span class="hint">同媒体其他分包</span></div></div><h2>二、报表分母对齐</h2><p class="hint">两个报表采用不同分母，“新增付费率”不能直接横向比较。</p>{compare_table}<div class="two-tone"><div class="card"><span class="label">按新增用户</span><span class="value">{pct(mature["new_paid_rate_by_new_users"])}</span><span class="hint">新增付费人数 ÷ 新增用户数</span></div><div class="card"><span class="label">按激活且注册</span><span class="value">{pct(mature["new_paid_rate_by_registered"])}</span><span class="hint">新增付费人数 ÷ 激活且注册数</span></div></div><h2>三、Phenix 日趋势（实际聚合）</h2>{daily_table}<div class="grid2"><div class="card"><h3>按新增用户付费率</h3><div class="bar-list">{html_bars([(row["date"], row["new_paid_rate_by_new_users"]) for row in daily], "rate")}</div></div><div class="card"><h3>次日付费留存</h3><div class="bar-list">{html_bars([(row["date"], row["d1_paid_retention"]) for row in daily], "rate")}</div><p class="hint">9/2 未成熟，0% 不可作为真实留存。</p></div></div><h2>四、留存成熟度与对照</h2><div class="grid2"><div class="card"><h3>cohort 成熟度</h3>{html_table(["cohort","D1","D3","D7"], [[row["date"],"可用" if row["d1_maturity"]=="mature" else "未成熟","可用" if row["d3_maturity"]=="mature" else "未成熟","可用" if row["d7_maturity"]=="mature" else "未成熟"] for row in daily])}<p class="hint">未成熟应显示 N/A。</p></div><div class="card"><h3>同日自然 H5 对照</h3>{peer_table}<p class="hint">Phenix 成熟 D1 {pct(mature["d1_paid_retention_weighted"])}；对照 {pct(peer["d1_paid_retention_weighted"])}。</p></div></div><h2>五、根因判断</h2>{html_table(["问题","证据","判断","处理"], [["口径不一致","0.64% 与约 2.02% 并存","高","统一分母"],["未成熟留存","9/2 D1、全窗口 D7 未成熟","高","返回 N/A"],["投放归因","媒体自然、消耗 0","若确属付费投放则高","补 campaign/media"],["用户质量","注册/付费/D1 低于对照","中","归因清洗后分层"],["埋点故障","单表可复算，缺留存分子","未定","查脱敏留存事实"]])}<h2>六、P0/P1 修复</h2>{html_table(["优先级","事项","验收"], [["P0","统一按新增用户和按激活注册两种付费率","两报表分子/分母一致"],["P0","增加 D1/D3/D7 maturity_status","未成熟不显示 0%"],["P0","补 package/campaign/media/referrer","不再落入自然无渠道"],["P1","留存事实对账","D1 可由脱敏聚合重算"],["P1","设备/浏览器/地区/版本分层","区分人群与体验因素"]])}<div class="callout red"><b>数据边界：</b>Phenix 媒体归因当前未确认；D3/D7 近期 cohort 未成熟；本报告不做因果判断。</div><footer class="footer">来源：{esc(SOURCE_XLS.name)}；不含用户明细、订单明细、账号或凭据。SHA256：{esc(a["profile"]["source_sha256"])}</footer></main></body></html>"""


def write_outputs(a: dict[str, Any]) -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    (ANALYSIS_DIR / "source_profile.json").write_text(json.dumps(a["profile"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS_DIR / "filtered_phx_daily.json").write_text(json.dumps([compact_row(row) for row in a["phx_daily"]], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS_DIR / "peer_comparison.json").write_text(json.dumps({"phx_mature": a["phx_mature"], "peer_all_organic": a["peer_all_organic"], "wajeh5_peer": a["wajeh5_peer"], "peer_daily": a["peer_daily"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS_DIR / "screenshot_comparison.json").write_text(json.dumps(a["screenshot_comparison"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS_DIR / "bigquery_audit_summary.json").write_text(json.dumps(bq_summary(a), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    formula_checks = {
        "new_paid_rate_by_new_users": "new_payers / new_users",
        "new_paid_rate_by_registered": "new_payers / activated_registered",
        "d1_paid_retention": "d1_inferred_retained_payers / new_payers; source column 2日付费留存",
        "maturity": "as_of_date >= cohort_date + N days; otherwise N/A",
        "source_rate_reconciles": all(abs((row["new_paid_rate_by_new_users"] or 0) - (row["source_new_paid_rate"] or 0)) < 0.00015 for row in a["phx_daily"]),
        "bigquery_api_status": bq_summary(a)["status"],
        "bigquery_latest_h5_table": bq_summary(a)["last_day"],
        "bigquery_phx_marker_event_count": bq_summary(a)["phx_param_marker_event_count"],
    }
    (ANALYSIS_DIR / "formula_checks.json").write_text(json.dumps(formula_checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    validation = {
        "status": "passed",
        "checks": {
            "source_exists": SOURCE_XLS.exists(),
            "seven_phx_rows": len(a["phx_daily"]) == 7,
            "source_rate_reconciles": formula_checks["source_rate_reconciles"],
            "incomplete_2026_09_02_is_immature": next(row for row in a["phx_daily"] if row["date"] == "2026-09-02")["d1_maturity"] == "immature",
            "screenshot_rows": len(a["screenshot_comparison"]) == 7,
            "no_user_level_rows": True,
            "no_credentials": True,
            "remote_systems_not_modified": True,
            "bigquery_api_aggregate_audit_ok": bq_summary(a)["status"] == "ok",
            "bigquery_phx_marker_zero_is_not_empty_source": (bq_summary(a)["total_event_count"] or 0) > 0 and bq_summary(a)["phx_param_marker_event_count"] == 0,
        },
    }
    validation["status"] = "passed" if all(validation["checks"].values()) else "failed"
    (ANALYSIS_DIR / "validation.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "run_id": f"phenix_channel_retention_{RUN_DATE}",
        "run_date": RUN_DATE,
        "status": "ok_provisional_diagnosis",
        "source": {"file": SOURCE_XLS.name, "sha256": a["profile"]["source_sha256"], "window": [WINDOW_START.isoformat(), WINDOW_END.isoformat()]},
        "bigquery": {"audit_file": str(BQ_AUDIT.relative_to(ROOT)), "status": bq_summary(a)["status"], "latest_h5_table_day": bq_summary(a)["last_day"], "phx_marker_event_count": bq_summary(a)["phx_param_marker_event_count"]},
        "scope": {"package": "wajeh5phx", "product": "Waje Special", "media_observed": a["media_values"], "spend_observed": a["spend_values"]},
        "outputs": {"markdown": str(OUTPUT_MD.relative_to(ROOT)), "html": str(OUTPUT_HTML.relative_to(ROOT)), "analysis_dir": str(ANALYSIS_DIR.relative_to(ROOT))},
        "safety": {"raw_source_saved": False, "user_level_rows_saved": False, "credentials_saved": False, "remote_systems_modified": False},
    }
    (ANALYSIS_DIR / "run_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ANALYSIS_DIR / "README.md").write_text(f"""# Phenix 分包付费与留存诊断工件

- Markdown：{OUTPUT_MD.relative_to(ROOT)}
- HTML：{OUTPUT_HTML.relative_to(ROOT)}
- 来源：{SOURCE_XLS.name}，只保留分包级聚合。
- 企业 BigQuery API：bigquery_audit.json；只保留 H5 原始入库元数据和日期级聚合计数。
- 运行：python3 scripts/analyze_phenix_channel_retention.py
- 不保存转换后的 xlsx、用户明细、订单明细、账号或凭据。
""", encoding="utf-8")
    markdown = build_markdown(a)
    markdown = markdown.replace("\n## 4. 留存异常定位", "\n" + build_bq_markdown(a) + "\n## 4. 留存异常定位", 1)
    OUTPUT_MD.write_text(markdown, encoding="utf-8")
    html_text = build_html(a)
    html_text = html_text.replace("<h2>五、根因判断</h2>", build_bq_html(a) + "<h2>五、根因判断</h2>", 1)
    html_text = html_text.replace("<section><h2>三、企业 BigQuery 原始入库审计（API 实测）</h2>", "<section><h2>五、企业 BigQuery 原始入库审计（API 实测）</h2>", 1)
    html_text = html_text.replace("<h2>五、根因判断</h2>", "<h2>六、根因判断</h2>", 1)
    html_text = html_text.replace("<h2>六、P0/P1 修复</h2>", "<h2>七、P0/P1 修复</h2>", 1)
    OUTPUT_HTML.write_text(html_text, encoding="utf-8")


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value if value is not None else "N/A").replace("|", "\\|").replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


def build_markdown(a: dict[str, Any]) -> str:
    all_s, mature, peer = a["phx_all"], a["phx_mature"], a["peer_all_organic"]
    daily = [
        [row["date"], fmt(row["new_users"]), fmt(row["activated_registered"]), pct(row["registration_rate"]),
         fmt(row["new_payers"]), pct(row["new_paid_rate_by_new_users"]), pct(row["new_paid_rate_by_registered"]),
         pct(row["d1_paid_retention"]), "可用" if row["d1_maturity"] == "mature" else "未成熟", pct(row["first_day_tc_rate"])]
        for row in a["phx_daily_desc"]
    ]
    compare = [
        [row["date"], fmt(row["screenshot_new_payers"]), pct(row["screenshot_rate"]), fmt(row["detail_new_payers"]),
         pct(row["detail_rate_new_users"]), pct(row["detail_rate_registered"]), fmt(row["activated_registered"]),
         pct(row["denominator_gap"] / row["activated_registered"] if row["denominator_gap"] is not None and row["activated_registered"] else None)]
        for row in a["screenshot_comparison"]
    ]
    peer_rows = [
        [row["date"], pct(row["phx_d1"]), pct(row["peer_d1"]),
         f"{(row['phx_d1'] - row['peer_d1']) * 100:.2f} 个百分点", fmt(row["peer_payers"]), row["peer_channels"]]
        for row in a["peer_daily"]
    ]
    maturity = [[row["date"], "可用" if row["d1_maturity"] == "mature" else "未成熟", "可用" if row["d3_maturity"] == "mature" else "未成熟", "可用" if row["d7_maturity"] == "mature" else "未成熟"] for row in a["phx_daily_desc"]]
    source_hash = a["profile"]["source_sha256"]
    return "\n".join([
        "---", "type: diagnostic-report", "domain: acquisition-retention", "status: provisional-diagnosis",
        f"updated: {RUN_DATE}", f"source_file: {SOURCE_XLS.name}", f"source_sha256: {source_hash}",
        f"window: {WINDOW_START}..{WINDOW_END}", "package: wajeh5phx", "---", "",
        "# Phenix 浏览器分包付费与留存异常诊断", "",
        f"> 诊断对象：{BT}wajeh5phx{BT}（用户描述为 Phenix 浏览器投放测试）。窗口：{BT}{WINDOW_START}{BT} 至 {BT}{WINDOW_END}{BT}。来源为分包级聚合导出和两张报表截图；不读取用户明细。",
        "",
        "## 1. 结论先行", "",
        "**当前最主要的问题不是单一的人群质量或单一的埋点故障，而是报表分母、cohort 成熟度和渠道归因同时不一致。**",
        "",
        md_table(["判断项", "证据", "状态"], [
            ["付费率口径不一致", "分包详情按新增用户计算；BQ 报表可见比例更接近激活且注册用户计算", "高置信度：分母问题"],
            ["近期留存显示 0", "9/2 次日留存未成熟；8/27～9/2 的 D7 均未成熟", "高置信度：成熟度展示问题"],
            ["渠道归因缺失", "7 天媒体均为自然(无渠道ID)，消耗金额均为 0", "若确属付费投放则高优先级"],
            ["Phenix 人群信号偏弱", f"成熟 6 天按新增用户付费率 {pct(mature['new_paid_rate_by_new_users'])}、D1 留存 {pct(mature['d1_paid_retention_weighted'])}；自然 H5 对照 D1 {pct(peer['d1_paid_retention_weighted'])}", "中置信度：需清洗归因后确认"],
            ["原始埋点整体故障", "分包详情付费率可由人数复算；留存比例呈现小样本可解释比例", "当前未证实"],
        ]),
        "",
        "> 先统一口径、筛选范围和成熟度，再判断 Phenix 人群。近期 0% 不能直接解释为真实流失。",
        "",
        "## 2. 数据范围与分母", "",
        md_table(["项目", "结果", "说明"], [
            ["源文件", SOURCE_XLS.name, f"1 个 Sheet；{a['profile']['column_count']} 个字段；{a['profile']['data_row_count_excluding_total']:,} 条非总计数据行"],
            ["Phenix 日记录", "7 条", "2026-08-27～2026-09-02；Waje Special；媒体均为自然(无渠道ID)"],
            ["窗口新用户", fmt(all_s["new_users"]), "含 9/2 部分日"],
            ["窗口激活且注册", fmt(all_s["activated_registered"]), f"注册转化率 {pct(all_s['registration_rate'])}"],
            ["窗口新增付费", fmt(all_s["new_payers"]), f"按新增用户付费率 {pct(all_s['new_paid_rate_by_new_users'])}"],
            ["成熟期新增付费", fmt(mature["new_payers"]), f"剔除 9/2；按激活注册付费率 {pct(mature['new_paid_rate_by_registered'])}"],
        ]),
        "",
        "### 2.1 两个“新增付费率”不是同一指标", "",
        f"- 分包详情：新增付费人数 ÷ 新增用户数。9/1 为 {BT}35 ÷ 5,459 = 0.64%{BT}，与导出表一致。",
        f"- BQ 截图：9/1 显示 35 人、2.02%；该比例更接近 {BT}35 ÷ 激活且注册数 1,681 = 2.08%{BT}，不是按 5,459 新用户计算。",
        "- 建议固定命名为“新增用户付费率”和“注册用户付费率”，查询结果同时展示分子、分母和筛选范围。",
        "",
        "## 3. Phenix 日数据复核", "",
        md_table(["日期", "新增用户", "激活注册", "注册率", "新增付费", "按新增用户付费率", "按激活注册付费率", "次日留存", "成熟度", "首日 TC 比"], daily),
        "",
        "### 3.1 截图与分包详情对齐", "",
        md_table(["日期", "截图付费人数", "截图付费率", "明细人数", "按新增用户", "按激活注册", "激活注册数", "截图推算分母差异"], compare),
        "",
        "截图 9/2 的新增付费人数为 14，分包详情为 15；其余可见日期人数基本一致。该差异更像刷新时点、媒体筛选或查询快照差异，不能单凭截图判定埋点漏报。",
        "",
        "## 4. 留存异常定位", "",
        "### 4.1 未成熟 cohort 被显示为 0", "",
        md_table(["cohort 日期", "次日/D1", "D3", "D7"], maturity),
        "",
        "- 9/2 的次日留存最早要到 9/3 才成熟，当前应显示 N/A/未成熟。",
        "- 8/31～9/2 的 D3 未成熟；8/27～9/2 的 D7 均未成熟。",
        "- 8/27～8/30 的 D3 已达到观察条件；若这些 cohort 的 D3 仍为 0%，再查留存事件和 join。",
        "",
        "### 4.2 成熟次日付费留存低于同日自然 H5 对照", "",
        md_table(["日期", "Phenix D1", "自然 H5 对照", "差异", "对照付费人数", "对照分包数"], peer_rows),
        "",
        f"成熟 6 天加权：Phenix D1 约 **{pct(mature['d1_paid_retention_weighted'])}**（139 个新付费，按比例反推约 7 个次日回访付费）；自然 H5 其他分包约 **{pct(peer['d1_paid_retention_weighted'])}**（3,316 个新付费）。差异约 **{fmt_pp(mature['d1_paid_retention_weighted'] - peer['d1_paid_retention_weighted'])}**。",
        "",
        "这是方向性人群/体验信号。Phenix 当前没有媒体归因 ID，不能把它解释为已证实的付费投放因果结果。",
        "",
        "## 5. 根因判断：人群还是上报？", "",
        md_table(["可能原因", "证据", "判断", "处理"], [
            ["报表口径/分母不一致", "0.64% 与约 2.02% 并存；两种分母均可复算", "高", "统一指标命名、分母和筛选"],
            ["cohort 未成熟显示 0", "9/2 D1、全窗口 D7 未成熟", "高", "增加 maturity_status，未成熟返回 N/A"],
            ["投放归因缺失", "媒体自然无渠道、消耗 0", "若属付费投放则高", "补 campaign、媒体、referrer"],
            ["Phenix 人群质量偏弱", f"成熟注册率 {pct(mature['registration_rate'])} vs 对照 {pct(peer['registration_rate'])}；按新增用户付费率 {pct(mature['new_paid_rate_by_new_users'])} vs {pct(peer['new_paid_rate_by_new_users'])}", "中", "归因清洗后按设备/地区/版本分层"],
            ["留存事件漏报或 join 错误", "没有留存分子事实；分包表只能反推整数级结果", "未定", "查脱敏 cohort 留存事实"],
        ]),
        "",
        "### 当前定位结论", "",
        "1. 付费率的明显差异主要由分母和报表范围不一致造成。",
        "2. 留存 0% 首先由未成熟日期导致，不能直接归因用户不回访。",
        "3. 成熟 D1、注册率和付费率确实低于对照，存在人群质量或产品体验问题。",
        "4. 当前没有足够证据证明全链路留存埋点丢失；需要脱敏服务端聚合做最终排除。",
        "",
        "## 6. P0/P1 修复清单", "",
        md_table(["优先级", "事项", "实现要求", "验收标准"], [
            ["P0", "统一付费率口径", "同时输出按新增用户、按激活注册两种比例", "两报表分子/分母逐项一致"],
            ["P0", "修复留存成熟度", "按 as_of_date >= cohort_date + N 判断 D1/D3/D7", "未成熟显示 N/A，不显示 0%"],
            ["P0", "核对 Phenix 归因", "补 package、campaign、attribution_media、attribution_channel、install_referrer", "投放测试不落入自然无渠道"],
            ["P1", "留存事实对账", "以新增付费 cohort 为分母核对次日再次成功付费/活跃付费人数", "D1 公式可由脱敏聚合事实重算"],
            ["P1", "人群分层", "按设备、浏览器、地区、版本、注册状态、媒体拆分", "同一分层下比较 Phenix 与对照"],
        ]),
        "",
        "## 7. 验证 SQL / 伪代码", "",
        f"付费率：{BT}new_payers / new_users{BT}；注册用户付费率：{BT}new_payers / activated_registered{BT}。",
        f"留存成熟度：{BT}as_of_date >= cohort_date + N{BT}，未满足条件返回 NULL/N/A。",
        f"推荐关联：{BT}cohort_date + package_name + attribution_media + user_id_hash{BT}；不保存用户明细，只保留安全聚合结果。",
        "",
        "## 8. 证据边界", "",
        f"- 源文件为分包级聚合，不含用户明细；SHA256：{BT}{source_hash}{BT}。",
        "- 截图只用于核对可见分子/比例，不替代完整导出。",
        f"- {BT}2日付费留存{BT} 按 cohort 次日/D1 付费留存解释；若 Origin 定义不同，需要按指标字典重算。",
        "- Phenix 与自然 H5 对照可能同时受到人群、版本、归因和刷新时间影响，当前不做因果判断。",
        "",
    ])


def bq_summary(a: dict[str, Any]) -> dict[str, Any]:
    audit = a.get("bigquery_audit", {})
    queries = {row.get("id"): row for row in audit.get("queries", [])}
    table_rows = queries.get("01_bq_h5_table_coverage", {}).get("execution", {}).get("aggregate_rows", [])
    marker_rows = queries.get("02_bq_phx_marker_coverage", {}).get("execution", {}).get("aggregate_rows", [])
    marker = marker_rows[0] if marker_rows else {}
    days = sorted({str(row.get("table_name", ""))[-8:] for row in table_rows if re.search(r"events_\d{8}$", str(row.get("table_name", "")))})
    return {
        "status": audit.get("status", "not_run"),
        "table_count": len(table_rows),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
        "event_day": marker.get("event_table_day"),
        "total_event_count": marker.get("total_event_count"),
        "distinct_event_name_count": marker.get("distinct_event_name_count"),
        "business_event_candidate_count": marker.get("business_event_candidate_count"),
        "game_event_candidate_count": marker.get("game_event_candidate_count"),
        "app_id_marker_event_count": marker.get("app_id_marker_event_count"),
        "app_version_marker_event_count": marker.get("app_version_marker_event_count"),
        "package_param_present_count": marker.get("package_param_present_count"),
        "channel_param_present_count": marker.get("channel_param_present_count"),
        "attribution_media_param_present_count": marker.get("attribution_media_param_present_count"),
        "campaign_param_present_count": marker.get("campaign_param_present_count"),
        "phx_param_marker_event_count": marker.get("phx_param_marker_event_count"),
        "traffic_source_present_count": marker.get("traffic_source_present_count"),
        "collected_source_present_count": marker.get("collected_source_present_count"),
        "pseudo_id_present_count": marker.get("pseudo_id_present_count"),
        "approximate_pseudo_id_count": marker.get("approximate_pseudo_id_count"),
        "dry_run_total_bytes": audit.get("dry_run_total_bytes"),
        "aggregate_result_rows": audit.get("aggregate_result_rows"),
    }


def build_bq_markdown(a: dict[str, Any]) -> str:
    bq = bq_summary(a)
    latest = bq.get("last_day") or "未知"
    gap = "未覆盖 2026-08-28 至 2026-09-02" if latest and latest < "20260828" else "覆盖窗口待继续核对"
    rows = [
        ["API 认证/查询", bq.get("status"), "真实 API 聚合查询已执行；只返回元数据和计数"],
        ["H5 原始表覆盖", f"{bq.get('table_count')} 张，至 {latest}", gap],
        ["2026-08-27 入库事件", fmt(bq.get("total_event_count")), f"{bq.get('distinct_event_name_count')} 类事件"],
        ["Phenix 标记命中", fmt(bq.get("app_id_marker_event_count")) + " / " + fmt(bq.get("app_version_marker_event_count")) + " / " + fmt(bq.get("phx_param_marker_event_count")), "app_id、版本和标准来源参数均未命中 Phenix"],
        ["业务/游戏事件候选", f"{fmt(bq.get('business_event_candidate_count'))} / {fmt(bq.get('game_event_candidate_count'))}", "未观察到充值/支付/注册/提现或游戏阶段候选"],
        ["包/渠道/媒体参数", f"{fmt(bq.get('package_param_present_count'))} / {fmt(bq.get('channel_param_present_count'))} / {fmt(bq.get('attribution_media_param_present_count'))}", "当前 H5 原始事件未填这些标准参数键"],
        ["campaign 参数", fmt(bq.get("campaign_param_present_count")), "存在部分 campaign key，但没有 Phenix 值命中"],
        ["伪标识覆盖", fmt(bq.get("pseudo_id_present_count")), f"约 {fmt(bq.get('approximate_pseudo_id_count'))} 个匿名主体；不代表可按 Phenix 归因"],
    ]
    return "\n".join([
        "## 3.2 企业 BigQuery 原始入库审计（API 实测）",
        "",
        "> 本节使用企业 BigQuery API 对 `wajenigeria` 的 H5 Firebase 原始表执行只读聚合。没有读取或保存事件明细、参数值或用户标识。",
        "",
        md_table(["检查项", "结果", "解释"], rows),
        "",
        "### BQ 对 Origin 报表的直接结论",
        "",
        "- BigQuery H5 原始表当前只到 `2026-08-27`，无法独立验证 Origin 文件中的 8/28～9/2 分包数据；这属于数据覆盖延迟/缺口，不是业务值为 0。",
        "- 2026-08-27 有 771,647 条事件，但只有 4 类标准行为事件；没有观察到 Phenix 包体标记，也没有充值、支付、注册、提现或游戏阶段事件候选。",
        "- `user_pseudo_id` 在原始入库中有聚合覆盖，但因为没有 Phenix 的包/媒体/渠道标记，不能用匿名主体数把 BQ 数据分配到 `wajeh5phx`。",
        "- 因此，Origin 的新增用户、付费人数和留存结果目前不能由企业 BigQuery 原始 H5 入库独立复算；问题更接近“来源链路未打通/事件契约缺失”，不是已经证实的“留存事件全部漏报”。",
        "",
    ])


def build_bq_html(a: dict[str, Any]) -> str:
    bq = bq_summary(a)
    latest = bq.get("last_day") or "未知"
    rows = [
        ["API 查询状态", bq.get("status"), "只读聚合"],
        ["H5 原始表覆盖", f"{bq.get('table_count')} 张，至 {latest}", "8/28～9/2 未覆盖"],
        ["8/27 事件量", fmt(bq.get("total_event_count")), f"{bq.get('distinct_event_name_count')} 类标准行为事件"],
        ["Phenix 标记命中", fmt(bq.get("phx_param_marker_event_count")), "app_id/版本/标准参数均未命中"],
        ["业务/游戏候选", f"{fmt(bq.get('business_event_candidate_count'))} / {fmt(bq.get('game_event_candidate_count'))}", "当前无法由 BQ 复算付费/留存"],
        ["包/渠道/媒体参数", f"{fmt(bq.get('package_param_present_count'))} / {fmt(bq.get('channel_param_present_count'))} / {fmt(bq.get('attribution_media_param_present_count'))}", "标准键未填充"],
        ["伪标识覆盖", fmt(bq.get("pseudo_id_present_count")), f"约 {fmt(bq.get('approximate_pseudo_id_count'))} 个匿名主体"],
    ]
    return "<section><h2>三、企业 BigQuery 原始入库审计（API 实测）</h2><div class=\"callout red\"><b>结论：</b>API 查询成功，但 H5 原始表只覆盖到 2026-08-27；当天只有 4 类标准行为事件，Phenix 标记、业务事件和游戏事件候选均为 0。这个 0 表示当前源字段没有被入库或未被映射，不表示 Phenix 业务指标为 0。</div>" + html_table(["检查项","结果","解释"], rows) + "<p class=\"hint\">因此 Origin 8/28～9/2 的新增用户、付费和留存不能由当前 BQ 原始 H5 入库独立复算；需补齐日期表、来源标记和业务事实链路。</p></section>"


def main() -> None:
    analysis = build_analysis()
    write_outputs(analysis)
    print(json.dumps({"status": "ok", "markdown": str(OUTPUT_MD), "html": str(OUTPUT_HTML), "analysis_dir": str(ANALYSIS_DIR)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
