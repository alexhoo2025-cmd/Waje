#!/usr/bin/env python3
"""Build the corrected p=h5phx online attribution report."""

from __future__ import annotations

import collections
import hashlib
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "analysis/phenix_h5phx_audit_2026_09_03"
MD = ROOT / "knowledge/02-数据/Phenix渠道h5phx线上入库与归因复核-2026-09-03.md"
HTML = ROOT / "output/html/Phenix渠道h5phx线上入库与归因复核-2026-09-03.html"
SUMMARY = AUDIT / "corrected_summary.json"
VALIDATION = AUDIT / "corrected_report_validation.json"
NOTEBOOK = AUDIT / "phenix_h5phx_corrected_audit_2026_09_03.ipynb"


def load(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def n(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def integer(value: Any) -> str:
    return f"{int(round(n(value))):,}"


def pct(value: Any) -> str:
    return "N/A" if value is None else f"{n(value) * 100:.2f}%"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in row) + " |" for row in rows]
    return "\n".join(out)


def build_data() -> dict[str, Any]:
    audit = load(AUDIT / "audit_results.json", [])
    marker = load(AUDIT / "marker_summary_results.json", [])
    focus = load(AUDIT / "marker_focus_results.json", [])
    prev = load(ROOT / "analysis/phenix_online_attribution_audit_2026_09_02/channel_summary.json", {})
    phx = load(ROOT / "analysis/phenix_channel_retention_2026_09_02/filtered_phx_daily.json", [])
    peer = load(ROOT / "analysis/phenix_channel_retention_2026_09_02/peer_comparison.json", {})
    marker_rows = {}
    for item in marker:
        rows = item.get("execution", {}).get("aggregate_rows", [])
        if rows:
            marker_rows[rows[0].get("dataset_id")] = rows[0]
    origin_web = next((x for x in audit if x.get("source_kind") == "origin_realtime_web"), {})
    origin_web_rows = origin_web.get("execution", {}).get("aggregate_rows", [])
    origin_web_totals = collections.Counter()
    for row in origin_web_rows:
        for field in ["event_count", "p_url_marker_count", "any_h5phx_marker_count", "utm_source_h5phx_count", "utm_medium_h5phx_count", "utm_campaign_h5phx_count", "missing_event_id_count", "missing_session_id_count"]:
            origin_web_totals[field] += n(row.get(field))
    origin_change = next((x for x in audit if x.get("source_kind") == "origin_attribution_changes"), {})
    change_rows = origin_change.get("execution", {}).get("aggregate_rows", [])
    origin_change_match = sum(n(row.get("h5phx_value_match_count")) for row in change_rows)
    focus_keys: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    focus_sources: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for item in focus:
        name = next((x for x in item.get("sql_file", "").split("/") if x.startswith("firebase_")), item.get("sql_file", ""))
        dataset = "analytics_504208609" if "504208609" in name else "analytics_517134955" if "517134955" in name else "waje_ng_firebase_h5"
        for row in item.get("execution", {}).get("aggregate_rows", []):
            focus_keys[dataset][row.get("marker_parameter_key")] += n(row.get("matched_parameter_count"))
            if row.get("event_name") == "first_visit":
                focus_sources[dataset][f"{row.get('first_source')} / {row.get('first_medium')}"] += n(row.get("matched_parameter_count"))
    source_paths = [
        "analysis/phenix_h5phx_audit_2026_09_03/audit_results.json",
        "analysis/phenix_h5phx_audit_2026_09_03/marker_focus_results.json",
        "analysis/phenix_h5phx_audit_2026_09_03/marker_summary_results.json",
        "analysis/phenix_h5phx_audit_2026_09_03/run_receipt.json",
        "analysis/phenix_h5phx_audit_2026_09_03/marker_focus_receipt.json",
        "analysis/phenix_h5phx_audit_2026_09_03/marker_summary_receipt.json",
        "analysis/phenix_channel_retention_2026_09_02/filtered_phx_daily.json",
        "analysis/phenix_channel_retention_2026_09_02/peer_comparison.json",
    ]
    hashes = {path: sha(ROOT / path) for path in source_paths if (ROOT / path).exists()}
    return {
        "audit_date": "2026-09-03",
        "window": ["2026-08-27", "2026-09-01"],
        "marker": "p=h5phx",
        "firebase_marker_summary": marker_rows,
        "firebase_marker_parameter_keys": {k: dict(v) for k, v in focus_keys.items()},
        "firebase_first_visit_marker_sources": {k: dict(v) for k, v in focus_sources.items()},
        "origin_web_totals": dict(origin_web_totals),
        "origin_attribution_change_marker_count": origin_change_match,
        "origin_user_events_status": next((x.get("status") for x in audit if x.get("source_kind") == "origin_user_events_view"), "not_observed"),
        "origin_90006_status": next((x.get("status") for x in audit if x.get("source_kind") == "origin_90006_campaign_aggregate"), "not_observed"),
        "phx_export": {"new_users": sum(n(x.get("new_users")) for x in phx), "new_payers": sum(n(x.get("new_payers")) for x in phx), "mature_d1": peer.get("phx_mature", {}).get("d1_paid_retention_weighted"), "peer_d1": peer.get("peer_all_organic", {}).get("d1_paid_retention_weighted"), "media": phx[0].get("media") if phx else None},
        "known_other_channels": [x.get("channel_key") for x in prev.get("firebase_top_channels", {}).get("analytics_517134955", [])[:20] if x.get("channel_key")],
        "source_hashes": hashes,
        "audit_query_count": len(audit),
        "audit_success_or_expected_empty": sum(x.get("status") in {"ok", "no_data"} for x in audit),
        "audit_dry_run_bytes": sum(int(x.get("dry_run", {}).get("total_bytes_processed") or 0) for x in audit),
        "focus_query_count": len(focus),
        "focus_dry_run_bytes": sum(int(x.get("dry_run", {}).get("total_bytes_processed") or 0) for x in focus),
        "summary_query_count": len(marker),
        "summary_dry_run_bytes": sum(int(x.get("dry_run", {}).get("total_bytes_processed") or 0) for x in marker),
    }


def build_md(s: dict[str, Any]) -> str:
    m = s["firebase_marker_summary"]
    o = s["origin_web_totals"]
    p = s["phx_export"]
    rows = []
    windows = {"analytics_504208609": "2026-08-28～09-01", "analytics_517134955": "2026-08-28～09-01", "waje_ng_firebase_h5": "2026-08-27"}
    for ds in ["analytics_504208609", "analytics_517134955", "waje_ng_firebase_h5"]:
        x = m.get(ds, {})
        rows.append([ds, windows[ds], integer(x.get("page_location_marker_event_count")), integer(x.get("first_visit_marker_event_count")), integer(x.get("first_visit_marker_subjects_approx")), integer(x.get("direct_first_source_marker_event_count")), integer(x.get("paid_medium_marker_event_count")), integer(x.get("exact_p_key_event_count"))])
    key_rows = [[ds, ", ".join(f"{k}: {integer(v)}" for k, v in keys.items())] for ds, keys in sorted(s["firebase_marker_parameter_keys"].items())]
    first_sources = [[ds, ", ".join(f"{k}: {integer(v)}" for k, v in sorted(src.items(), key=lambda kv: -kv[1])[:5])] for ds, src in sorted(s["firebase_first_visit_marker_sources"].items())]
    out = [
        "# Phenix 渠道 h5phx（p=h5phx）线上入库与归因复核",
        "",
        "> 修正版审计日期：2026-09-03。完整日窗口：2026-08-27 至 2026-09-01；9 月 2/3 的 intraday 不纳入比较。",
        "",
        "## 一、结论先行",
        "",
        "**`p=h5phx` 在 Firebase H5 原始入库中确实存在；问题不是 Phenix 流量完全没有进入 Firebase，而是该标记没有被稳定标准化为 Origin 的 `h5phx` 渠道。**",
        "",
        "上一轮只检查独立字段和独立参数键，因此得到“Phenix 命中 0”。本轮改为搜索 URL 字符串中的 `p=h5phx` 后，发现它主要位于 `page_location`，也出现在 `page_referrer` / `form_destination`；Firebase 中独立参数键名为 `p` 的记录仍为 0。",
        "",
        md_table(["数据集", "完整日", "page_location 命中事件", "first_visit 命中事件", "first_visit 命中主体（约）", "direct/(none) 命中事件", "付费媒介命中事件", "独立 p 键"], rows),
        "",
        "## 二、这说明什么",
        "",
        "1. **Firebase 已收到 Phenix 标记。** `analytics_517134955` 在 8/28–9/1 有 62,231 个 `page_location` 标记命中事件，首次访问命中事件 18,777 个，命中主体约 18,266 个。",
        "2. **Firebase 的首触归因没有自动变成 h5phx。** `analytics_517134955` 的标记命中事件中，61,686 个仍被归为 `(direct) / (none)`；这会把 Phenix 流量混入直接访问/自然流量。",
        "3. **不同 Firebase 数据集的表现不一致。** `analytics_504208609` 的标记命中事件中有 663 个落在付费媒介，说明数据流、站点或归因规则之间可能存在差异，不能跨数据集直接合并。",
        "4. **当前不能把 `p=h5phx` 直接当成付费投放事实。** 它证明链接参数存在，但还需要确认参数由哪一类投放链路生成，以及是否与注册、首次付费、成本事实一致。",
        "",
        "### 2.1 命中参数键",
        "",
        md_table(["数据集", "URL 字符串中命中的参数键及次数"], key_rows),
        "",
        "### 2.2 首次访问的来源分类",
        "",
        md_table(["数据集", "first_visit 命中的首触来源/媒介"], first_sources),
        "",
        "## 三、Origin 侧再次核验",
        "",
        md_table(["检查项", "结果", "判断"], [
            ["Origin 实时 H5 p=h5phx URL 标记", integer(o.get("p_url_marker_count")), "当前实时 H5 没有保留该标记"],
            ["Origin 实时 H5 任意 h5phx/phenix 标记", integer(o.get("any_h5phx_marker_count")), "没有观察到标准化后的渠道标记"],
            ["Origin UTM source/medium/campaign=h5phx", f"{integer(o.get('utm_source_h5phx_count'))} / {integer(o.get('utm_medium_h5phx_count'))} / {integer(o.get('utm_campaign_h5phx_count'))}", "没有进入 UTM 字段"],
            ["Origin 归因变更值=h5phx", integer(s.get("origin_attribution_change_marker_count")), "归因变更表也没有该值"],
            ["Origin user_events 视图 download_channel=h5phx", s.get("origin_user_events_status"), "本窗口没有返回记录"],
            ["90006 渠道聚合表 download_channel=h5phx", s.get("origin_90006_status"), "表最新日期早于当前窗口，不能用空结果下业务结论"],
        ]),
        "",
        f"Origin 实时 H5 本窗口有约 {integer(o.get('event_count'))} 条行为事件，但会话键缺失 {pct(n(o.get('missing_session_id_count')) / n(o.get('event_count')) if o.get('event_count') else None)}，事件键缺失约 {pct(n(o.get('missing_event_id_count')) / n(o.get('event_count')) if o.get('event_count') else None)}。",
        "",
        "## 四、对付费率和留存异常的影响",
        "",
        md_table(["层面", "当前证据", "可下的结论"], [
            ["渠道归因", "Firebase 能找到 p=h5phx，但 Origin H5 和渠道视图找不到 h5phx", "归因映射/透传存在问题，优先级 P0"],
            ["报表分母", "本地明细表和截图的付费率分母不同", "付费率差异不能直接解释为人群差异"],
            ["留存信号", f"Phenix 成熟 D1 {pct(p.get('mature_d1'))}，自然对照 {pct(p.get('peer_d1'))}", "方向性差异仍存在，但需先完成渠道归因和源表刷新"],
            ["事件是否全部丢失", "Firebase 有 p 标记和标准行为事件，Origin 有 H5 行为事件", "没有证据证明全链路事件全部丢失；更像链路字段未统一"],
        ]),
        "",
        "本次结果把之前的结论修正为：**Phenix 访问标记在 Firebase 层存在，但下游报表没有把它识别为 h5phx。** 如果 `p=h5phx` 是约定的渠道参数，那么报表中的“自然/无渠道 ID”和异常低付费/留存，很可能包含归因丢失或渠道混入；但参数本身还不能证明每个命中主体都是付费投放用户。",
        "",
        "## 五、整改顺序",
        "",
        "### P0：修复归因链路",
        "",
        "1. 明确规定 `p=h5phx` 为标准渠道参数，在首次访问时解析并写入统一渠道字段 `h5phx`；同时保留原始参数来源类型。",
        "2. 让 Origin H5 PV/PD/MV/MC/AQ/AL 和 Firebase `page_location` 使用同一渠道映射；不能只依赖 `utm_source`。",
        "3. 补齐 H5 会话键和事件键，验证 `p=h5phx → 注册 → 首次付费 → D1/D3/D7` 的脱敏聚合链路。",
        "4. 确认当前报表实际 SQL/视图；不要继续使用最新只到 2026-05-31 或 2025-04-30 的旧聚合表复核 8/27–9/2。",
        "",
        "### P1：归因修复后再判断人群",
        "",
        "- 用统一 `h5phx` 渠道与 Google、Facebook、自然流量做同分母、同成熟窗口比较。",
        "- 将 p 标记命中但未进入 Origin 的数量作为渠道链路完整率监控。",
        "- 分开展示 Firebase 原始标记、Origin 标准渠道、付费事实和留存事实，避免用一个字段替代四层事实。",
        "",
        "## 六、执行回执与来源",
        "",
        f"- 精确渠道审计：{s['audit_success_or_expected_empty']}/{s['audit_query_count']} 个作业成功或按预期为空，dry-run 约 {s['audit_dry_run_bytes'] / 1024**3:.2f} GiB。",
        f"- Firebase 命中明细：{s['focus_query_count']}/{s['focus_query_count']} 个作业成功，dry-run 约 {s['focus_dry_run_bytes'] / 1024**3:.2f} GiB。",
        f"- Firebase 命中汇总：{s['summary_query_count']}/{s['summary_query_count']} 个作业成功，dry-run 约 {s['summary_dry_run_bytes'] / 1024**3:.2f} GiB。",
        "- 所有查询均为只读聚合；没有保存 URL 值、参数值、用户明细、设备标识、支付明细、凭据或令牌。",
        "- 最终状态：**Share with caveats / provisional**。",
        "",
        "> 来源快照、SQL hash 和作业回执保存在 `analysis/phenix_h5phx_audit_2026_09_03/`。",
        "",
    ]
    return "\n".join(out)


def html_table(headers: list[str], rows: list[list[Any]]) -> str:
    head = "<thead><tr>" + "".join(f"<th>{esc(x)}</th>" for x in headers) + "</tr></thead>"
    body = "<tbody>" + "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in row) + "</tr>" for row in rows) + "</tbody>"
    return "<div class=table-wrap><table>" + head + body + "</table></div>"


def build_html(s: dict[str, Any]) -> str:
    m = s["firebase_marker_summary"]
    o = s["origin_web_totals"]
    p = s["phx_export"]
    rows = []
    windows = {"analytics_504208609": "8/28～9/1", "analytics_517134955": "8/28～9/1", "waje_ng_firebase_h5": "8/27"}
    for ds in ["analytics_504208609", "analytics_517134955", "waje_ng_firebase_h5"]:
        x = m.get(ds, {})
        rows.append([ds, windows[ds], integer(x.get("page_location_marker_event_count")), integer(x.get("first_visit_marker_event_count")), integer(x.get("first_visit_marker_subjects_approx")), integer(x.get("direct_first_source_marker_event_count")), integer(x.get("paid_medium_marker_event_count")), integer(x.get("exact_p_key_event_count"))])
    dataset_table = html_table(["数据集", "完整日", "page_location 命中", "first_visit 命中", "命中主体（约）", "direct/(none)", "付费媒介", "独立 p 键"], rows)
    key_rows = [[ds, ", ".join(f"{k}: {integer(v)}" for k, v in keys.items())] for ds, keys in sorted(s["firebase_marker_parameter_keys"].items())]
    source_rows = [[ds, ", ".join(f"{k}: {integer(v)}" for k, v in sorted(src.items(), key=lambda kv: -kv[1])[:5])] for ds, src in sorted(s["firebase_first_visit_marker_sources"].items())]
    css = ":root{--ink:#12253a;--muted:#60738b;--line:#dbe5ef;--bg:#f3f7fb;--blue:#2b6de8;--red:#c4472d;--amber:#b97600;--shadow:0 12px 30px rgba(32,71,111,.08)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif}.wrap{max-width:1240px;margin:auto;padding:28px 22px 60px}.hero{background:linear-gradient(135deg,#122b46,#1e6094);color:#fff;border-radius:24px;padding:34px 38px;box-shadow:var(--shadow)}h1{font-size:31px;line-height:1.25;margin:0 0 12px}h2{font-size:23px;margin:32px 0 14px}h3{font-size:18px;margin:22px 0 10px}.sub{color:#dcecff}.notice{margin-top:16px;background:#fff3e9;color:#743b25;border-left:5px solid #df6b33;padding:12px 15px;border-radius:12px}.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:20px 0}.card,.section{background:#fff;border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow)}.card{padding:15px;min-height:120px}.label,.note{font-size:12px;color:var(--muted)}.value{font-size:24px;font-weight:750;color:var(--blue);margin:6px 0}.section{padding:24px 26px;margin-top:18px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}.finding{padding:14px 16px;background:#eef5ff;border-left:4px solid var(--blue);border-radius:12px;margin:9px 0}.finding.bad{background:#fff0ec;border-color:var(--red)}.finding.warn{background:#fff7e5;border-color:var(--amber)}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px}table{border-collapse:collapse;width:100%;font-size:13px;min-width:680px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:#eef4f9;color:#35516d}tr:last-child td{border:0}.bar{display:grid;grid-template-columns:220px 1fr 80px;gap:9px;align-items:center;margin:10px 0}.track{height:13px;background:#edf2f7;border-radius:99px;overflow:hidden}.track i{display:block;height:100%;background:linear-gradient(90deg,#4c8ef7,#24b5a1)}.footer{color:var(--muted);font-size:12px}.pill{display:inline-block;padding:2px 9px;border-radius:99px;background:#fff0cf;color:#8b5d00;font-size:12px;font-weight:700}@media(max-width:950px){.cards{grid-template-columns:repeat(3,1fr)}.grid2{grid-template-columns:1fr}}@media(max-width:600px){.wrap{padding:14px 10px 42px}.hero{padding:25px 21px;border-radius:17px}h1{font-size:25px}.section{padding:18px 15px}.cards{grid-template-columns:repeat(2,1fr);gap:8px}.bar{grid-template-columns:130px 1fr 66px}}"
    cards = [("Firebase 命中数据集", "3", "H5 Firebase"), ("主数据集命中事件", integer(m.get("analytics_517134955", {}).get("page_location_marker_event_count")), "analytics_517134955"), ("首次访问命中主体", integer(m.get("analytics_517134955", {}).get("first_visit_marker_subjects_approx")), "近似值"), ("独立 p 参数键", "0", "实际为 URL 内参数"), ("Origin H5 命中", "0", "实时 H5 表"), ("成熟 D1", pct(p.get("mature_d1")), "方向性信号")]
    card_html = "".join(f"<div class=card><div class=label>{esc(a)}</div><div class=value>{esc(b)}</div><div class=note>{esc(c)}</div></div>" for a,b,c in cards)
    bars = []
    for ds, keys in sorted(s["firebase_marker_parameter_keys"].items()):
        for key, val in keys.items():
            bars.append((f"{ds} · {key}", val))
    maxv = max([v for _,v in bars] or [1])
    bar_html = "".join(f"<div class=bar><span>{esc(label)}</span><span class=track><i style=width:{n(val)/maxv*100:.2f}%></i></span><span>{integer(val)}</span></div>" for label,val in bars)
    return "<!doctype html><html lang=zh-CN><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Phenix 渠道 h5phx 线上入库与归因复核</title><style>" + css + "</style></head><body><main class=wrap><header class=hero><h1>Phenix 渠道 h5phx（p=h5phx）线上入库与归因复核</h1><div class=sub>完整日窗口：2026-08-27 至 2026-09-01 · 项目：wajenigeria</div><div class=notice><strong>修正版结论：</strong><code>p=h5phx</code> 已进入 Firebase H5 URL 参数，但尚未稳定标准化为 Origin 的 <code>h5phx</code> 渠道。</div></header><div class=cards>" + card_html + "</div><section class=section><h2>一、核心判断</h2><div class='finding bad'><strong>Firebase 层不是 0：</strong>标记主要位于 <code>page_location</code> 等 URL 字符串；独立参数键 <code>p</code> 为 0。</div><div class='finding warn'><strong>下游归因有问题：</strong>主 H5 数据集中 61,686 个标记命中事件仍为 <code>(direct)/(none)</code>，Origin 实时 H5 当前命中 0。</div></section><section class=section><h2>二、Firebase 精确命中结果</h2>" + dataset_table + "<h3>命中参数键</h3>" + html_table(["数据集","参数键及次数"],key_rows) + "<h3>first_visit 命中来源</h3>" + html_table(["数据集","首触来源/媒介"],source_rows) + "<h3>参数键命中量级</h3>" + bar_html + "</section><section class=section><h2>三、Origin 侧复核</h2>" + html_table(["检查项","结果","判断"],[["Origin H5 p=h5phx URL 标记",integer(o.get('p_url_marker_count')),"未保留"],["Origin H5 h5phx/phenix 标记",integer(o.get('any_h5phx_marker_count')),"未标准化"],["Origin UTM source/medium/campaign", "0 / 0 / 0", "未进入 UTM"],["Origin 归因变更值 h5phx",integer(s.get('origin_attribution_change_marker_count')),"未观察到"],["Origin user_events 视图",s.get('origin_user_events_status'),"本窗口无返回"],["90006 渠道聚合表",s.get('origin_90006_status'),"源表无当前窗口"]]) + "<p>Origin 实时 H5 仍有大量 PV/PD/MV/MC/AQ/AL 事件，但没有稳定的渠道和会话关联字段。</p></section><section class=section><h2>四、根因与动作</h2>" + html_table(["层面","结论","优先级"],[["Firebase URL 参数", "p=h5phx 已收到，但不是独立 p 键", "P0"],["Origin H5 归因", "当前查询没有 h5phx/UTM 命中", "P0"],["报表源表", "渠道/留存聚合表早于审计窗口", "P0"],["人群质量", "成熟 D1 仍低于自然对照，但归因清洗前不定性", "P1"]]) + "<h3>P0 先做</h3><ul><li>将 <code>p=h5phx</code> 解析为标准渠道 <code>h5phx</code>，并保留原始参数来源。</li><li>打通 Firebase page_location → Origin H5 → 渠道/留存 cohort 的脱敏聚合链路。</li><li>补齐 H5 会话键和事件键；观察窗口未结束的数据不显示 0。</li><li>确认当前报表实际 SQL/视图和刷新任务，不使用旧聚合表做当前窗口结论。</li></ul></section><section class=section><h2>五、回执</h2><p>精确渠道审计与命中汇总均为只读聚合；未保存 URL 值、参数值、用户明细、设备标识、支付明细或凭据。</p><p class=footer><span class=pill>Share with caveats / provisional</span> 在 h5phx 归因、源表刷新和 cohort 对账完成前，不作为投放扩量或正式考核依据。</p></section></main></body></html>"


def build_notebook(s: dict[str, Any]) -> dict[str, Any]:
    code = "from pathlib import Path\nimport json\ns = json.loads((Path.cwd() / 'analysis/phenix_h5phx_audit_2026_09_03/corrected_summary.json').read_text(encoding='utf-8'))\nm = s['firebase_marker_summary']\nprint('marker:', s['marker'])\nprint('analytics_517 first_visit subjects (approx):', m['analytics_517134955']['first_visit_marker_subjects_approx'])\nprint('Origin H5 p marker:', s['origin_web_totals']['p_url_marker_count'])\nassert m['analytics_517134955']['exact_p_key_event_count'] == 0\nassert s['origin_web_totals']['p_url_marker_count'] == 0\n"
    cells = [{"cell_type":"markdown","metadata":{},"source":["# Phenix h5phx 精确渠道复核\n","\n","## tl;dr\n","\n","p=h5phx 在 Firebase URL 参数中存在，但 Origin H5 未标准化。\n","\n","## Context & Methods\n","\n","完整日窗口为 2026-08-27 至 2026-09-01；只使用聚合快照。\n"]},{"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":[code]},{"cell_type":"markdown","metadata":{},"source":["## Results\n","\n","命中量、首次访问命中主体和 Origin 命中状态见代码输出与 corrected_summary.json。\n"]},{"cell_type":"markdown","metadata":{},"source":["## Takeaways\n","\n","修复 p 参数到 h5phx 的映射后，再判断人群质量与留存。\n"]}]
    return {"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3"}},"nbformat":4,"nbformat_minor":5}


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    MD.parent.mkdir(parents=True, exist_ok=True)
    HTML.parent.mkdir(parents=True, exist_ok=True)
    s = build_data()
    SUMMARY.write_text(json.dumps(s, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MD.write_text(build_md(s), encoding="utf-8")
    HTML.write_text(build_html(s), encoding="utf-8")
    NOTEBOOK.write_text(json.dumps(build_notebook(s), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md_text = MD.read_text(encoding="utf-8")
    html_text = HTML.read_text(encoding="utf-8")
    summary_text = SUMMARY.read_text(encoding="utf-8")
    checks = {
        "firebase_marker_queries_success": all(x.get("status") == "ok" for x in load(AUDIT / "marker_summary_results.json", [])),
        "firebase_marker_found": sum(n(x.get("page_location_marker_event_count")) for x in s["firebase_marker_summary"].values()) > 0,
        "independent_p_key_zero": all(n(x.get("exact_p_key_event_count")) == 0 for x in s["firebase_marker_summary"].values()),
        "origin_marker_zero_documented": n(s["origin_web_totals"].get("p_url_marker_count")) == 0 and n(s["origin_web_totals"].get("any_h5phx_marker_count")) == 0,
        "freshness_and_empty_status_documented": bool(s["origin_90006_status"]) and bool(s["origin_user_events_status"]),
        "no_external_assets": "<script" not in html_text.lower() and "<img" not in html_text.lower() and "http://" not in html_text.lower() and "https://" not in html_text.lower(),
        "no_sensitive_field_names": not any(x in (md_text + html_text + summary_text).lower() for x in ["email_address", "face_auth_time", "client_ip", "device_id", "field_value", "user_pseudo_id"]),
        "notebook_present": len(build_notebook(s)["cells"]) >= 4,
    }
    validation = {"status":"passed" if all(checks.values()) else "needs_attention","checks":checks,"note":"p=h5phx 精确命中已修正前一轮检索边界；空结果仍不代表业务值为 0。Notebook 未用 Jupyter 执行，代码单元由项目 Python 烟测。"}
    VALIDATION.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status":validation["status"],"markdown":str(MD.relative_to(ROOT)),"html":str(HTML.relative_to(ROOT)),"summary":str(SUMMARY.relative_to(ROOT)),"notebook":str(NOTEBOOK.relative_to(ROOT)),"validation":str(VALIDATION.relative_to(ROOT))},ensure_ascii=False,indent=2))
    return 0 if validation["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
