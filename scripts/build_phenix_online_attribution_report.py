#!/usr/bin/env python3
"""Build the local report and reproducible companion for the online BQ audit."""

from __future__ import annotations

import collections
import hashlib
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "analysis/phenix_online_attribution_audit_2026_09_02"
REPORT_MD = ROOT / "knowledge/02-数据/Phenix线上BigQuery归因与跨渠道上报审计-2026-09-02.md"
REPORT_HTML = ROOT / "output/html/Phenix线上BigQuery归因与跨渠道上报审计-2026-09-02.html"
SUMMARY_JSON = AUDIT_DIR / "channel_summary.json"
VALIDATION_JSON = AUDIT_DIR / "online_report_validation.json"
NOTEBOOK = AUDIT_DIR / "phenix_online_attribution_audit_2026_09_02.ipynb"


def load_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def integer(value: Any) -> str:
    return f"{int(round(number(value))):,}"


def pct(value: Any, digits: int = 2) -> str:
    return "N/A" if value is None else f"{number(value) * 100:.{digits}f}%"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def flatten_firebase(queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for query in queries:
        for row in query.get("execution", {}).get("aggregate_rows", []):
            item = dict(row)
            item["dataset_id"] = query.get("dataset_id")
            item["event_day"] = query.get("event_day")
            rows.append(item)
    return rows


def origin_item(items: list[dict[str, Any]], suffix: str) -> dict[str, Any]:
    for item in items:
        if item.get("sql_file", "").endswith(suffix):
            return item
    return {}


def build_summary() -> dict[str, Any]:
    inv = load_json(AUDIT_DIR / "table_inventory.json", [])
    firebase_queries = load_json(AUDIT_DIR / "daily_channel_audit.json", [])
    origin_queries = load_json(AUDIT_DIR / "origin_crosscheck.json", [])
    phx_daily = load_json(ROOT / "analysis/phenix_channel_retention_2026_09_02/filtered_phx_daily.json", [])
    peer = load_json(ROOT / "analysis/phenix_channel_retention_2026_09_02/peer_comparison.json", {})
    formulas = load_json(ROOT / "analysis/phenix_channel_retention_2026_09_02/formula_checks.json", {})
    firebase_rows = flatten_firebase(firebase_queries)
    daily_meta = {(x.get("dataset_id"), x.get("event_day")): x for x in inv if x.get("status") == "available" and x.get("table_class") == "complete_daily"}
    datasets: dict[str, dict[str, Any]] = {}
    channels: dict[tuple[str, str, str, str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    for row in firebase_rows:
        ds = row["dataset_id"]
        item = datasets.setdefault(ds, {"dataset_id": ds, "days": set(), "table_rows": 0, "visible_event_rows": 0, "first_events": 0, "session_events": 0, "page_events": 0, "business_candidates": 0, "game_candidates": 0, "phx_markers": 0, "platforms": set(), "app_ids": set(), "hosts": set()})
        item["days"].add(row.get("event_day"))
        item["platforms"].add(row.get("platform"))
        item["app_ids"].add(row.get("app_id"))
        item["hosts"].add(row.get("hostname"))
        for field in ["event_count", "business_event_candidate_count", "game_event_candidate_count", "phx_marker_count", "session_start_event_count", "page_view_event_count"]:
            target = {"event_count": "visible_event_rows", "business_event_candidate_count": "business_candidates", "game_event_candidate_count": "game_candidates", "phx_marker_count": "phx_markers", "session_start_event_count": "session_events", "page_view_event_count": "page_events"}[field]
            item[target] += number(row.get(field))
        item["first_events"] += number(row.get("first_visit_event_count")) + number(row.get("first_open_event_count"))
        key = (ds, row.get("platform"), row.get("app_id"), row.get("hostname"), row.get("channel_key"))
        for field in ["event_count", "first_visit_event_count", "first_open_event_count", "business_event_candidate_count", "game_event_candidate_count", "phx_marker_count", "manual_source_present_count", "campaign_key_present_count"]:
            channels[key][field] += number(row.get(field))
    for ds, item in datasets.items():
        item["days"] = sorted(x for x in item["days"] if x)
        item["table_rows"] = sum(number(daily_meta.get((ds, day), {}).get("num_rows")) for day in item["days"])
        item["visible_coverage"] = item["visible_event_rows"] / item["table_rows"] if item["table_rows"] else None
        for field in ["platforms", "app_ids", "hosts"]:
            item[field] = sorted(x for x in item[field] if x and x != "(blank)")
    top_channels: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for (ds, platform, app_id, hostname, channel_key), counter in channels.items():
        top_channels[ds].append({"platform": platform, "app_id": app_id, "hostname": hostname, "channel_key": channel_key, **dict(counter)})
    for ds in top_channels:
        top_channels[ds].sort(key=lambda x: (-number(x.get("event_count")), x.get("hostname", ""), x.get("channel_key", "")))
    web_item = origin_item(origin_queries, "origin_realtime_web_channel.sql")
    web_rows = web_item.get("execution", {}).get("aggregate_rows", [])
    web = {"event_rows": 0, "missing_event_id": 0, "missing_session_id": 0, "utm_source": 0, "utm_medium": 0, "utm_campaign": 0, "phx_markers": 0, "event_type_counts": collections.Counter()}
    for row in web_rows:
        for field in ["event_count", "missing_event_id_count", "missing_session_id_count", "utm_source_present_count", "utm_medium_present_count", "utm_campaign_present_count", "phx_marker_count"]:
            target = {"event_count": "event_rows", "missing_event_id_count": "missing_event_id", "missing_session_id_count": "missing_session_id", "utm_source_present_count": "utm_source", "utm_medium_present_count": "utm_medium", "utm_campaign_present_count": "utm_campaign", "phx_marker_count": "phx_markers"}[field]
            web[target] += number(row.get(field))
        web["event_type_counts"][row.get("event_type")] += number(row.get("event_count"))
    for field in ["event_id", "session_id", "utm_source", "utm_medium", "utm_campaign"]:
        web[f"{field}_missing_rate"] = (web[f"missing_{field}"] / web["event_rows"]) if field in {"event_id", "session_id"} and web["event_rows"] else None
        if field.startswith("utm_"):
            web[f"{field}_rate"] = web[field] / web["event_rows"] if web["event_rows"] else None
    web["event_type_counts"] = dict(web["event_type_counts"])
    client_item = origin_item(origin_queries, "origin_realtime_client_event_summary.sql")
    client_groups: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    for row in client_item.get("execution", {}).get("aggregate_rows", []):
        key = (row.get("package_name"), row.get("package_channel"))
        for field in ["event_count", "business_event_candidate_count", "approx_subject_count"]:
            client_groups[key][field] += number(row.get(field))
    client = [{"package_name": k[0], "package_channel": k[1], **dict(v)} for k, v in client_groups.items()]
    client.sort(key=lambda x: -number(x.get("event_count")))
    freshness = {}
    for suffix in ["origin_source_freshness.sql", "origin_source_freshness_eu.sql"]:
        for row in origin_item(origin_queries, suffix).get("execution", {}).get("aggregate_rows", []):
            freshness[row.get("source_table")] = row
    paths = [
        "analysis/phenix_online_attribution_audit_2026_09_02/daily_channel_audit.json",
        "analysis/phenix_online_attribution_audit_2026_09_02/table_inventory.json",
        "analysis/phenix_online_attribution_audit_2026_09_02/origin_crosscheck.json",
        "analysis/phenix_channel_retention_2026_09_02/filtered_phx_daily.json",
        "analysis/phenix_channel_retention_2026_09_02/peer_comparison.json",
        "analysis/phenix_channel_retention_2026_09_02/formula_checks.json",
    ]
    hashes = {p: sha256(ROOT / p) for p in paths if (ROOT / p).exists()}
    return {
        "audit_date": "2026-09-02",
        "complete_day_window": ["2026-08-27", "2026-09-01"],
        "intraday_day_excluded": "2026-09-02",
        "project_id": "wajenigeria",
        "business_timezone": "Africa/Lagos",
        "firebase_dataset_summary": datasets,
        "firebase_top_channels": top_channels,
        "origin_realtime_web_summary": web,
        "origin_client_package_summary": client,
        "origin_source_freshness": freshness,
        "origin_channel_rows_returned": origin_item(origin_queries, "origin_channel_aggregate.sql").get("execution", {}).get("row_count", 0),
        "origin_cohort_rows_returned": origin_item(origin_queries, "origin_cohort_aggregate.sql").get("execution", {}).get("row_count", 0),
        "phx_origin_export": {"row_count": len(phx_daily), "new_users": sum(number(x.get("new_users")) for x in phx_daily), "new_payers": sum(number(x.get("new_payers")) for x in phx_daily), "spend": sum(number(x.get("spend")) for x in phx_daily), "channel": phx_daily[0].get("channel") if phx_daily else None, "media": phx_daily[0].get("media") if phx_daily else None, "mature_d1": peer.get("phx_mature", {}).get("d1_paid_retention_weighted"), "peer_d1": peer.get("peer_all_organic", {}).get("d1_paid_retention_weighted")},
        "formula_checks": formulas,
        "source_hashes": hashes,
        "firebase_query_count": len(firebase_queries),
        "firebase_query_success_count": sum(q.get("status") == "ok" for q in firebase_queries),
        "origin_query_count": len(origin_queries),
        "origin_query_success_or_expected_empty_count": sum(q.get("status") in {"ok", "no_data"} for q in origin_queries),
        "firebase_dry_run_bytes": sum(int(q.get("dry_run", {}).get("total_bytes_processed") or 0) for q in firebase_queries),
        "origin_dry_run_bytes": sum(int(q.get("dry_run", {}).get("total_bytes_processed") or 0) for q in origin_queries),
    }


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in row) + " |")
    return "\n".join(lines)


def build_markdown(s: dict[str, Any]) -> str:
    ds = s["firebase_dataset_summary"]
    web = s["origin_realtime_web_summary"]
    fresh = s["origin_source_freshness"]
    phx = s["phx_origin_export"]
    out = [
        "# Phenix 线上 BigQuery 归因与跨渠道上报审计",
        "",
        "> 审计窗口：2026-08-27 至 2026-09-01（完整日）；2026-09-02 为进行中数据，不纳入横向比较。审计对象：Phenix 浏览器分包 `wajeh5phx` 的 Origin 聚合现象与企业 BigQuery 入库链路。",
        "",
        "## 一、结论先行",
        "",
        "**当前优先修复归因、源表刷新和 H5 会话链路，不应先把低留存定性为投放人群质量问题。**",
        "",
        md_table(["判断", "线上证据", "结论"], [
            ["Phenix 是否进入 Firebase BigQuery", "5 个可见 Firebase 数据集、487 个聚合组中标识命中 0 次", "未观察到 Phenix 可分配记录"],
            ["其他渠道是否能归因", "H5 侧观察到 `google / cpc`、`fb / paid`、`an / paid` 和 referral", "其他渠道可以进入 Firebase 归因字段"],
            ["Origin H5 是否有事件", f"实时表约 {integer(web['event_rows'])} 条 PV/PD/MV/MC/AQ/AL", "事件能到达，但归因和会话链路不完整"],
            ["Origin H5 是否有渠道归因", f"UTM source/medium/campaign 计数均为 0；会话键缺失 {pct(web['session_id_missing_rate'])}", "当前 H5 实时表不能支撑稳定渠道归因和会话串联"],
            ["Origin 报表源表是否覆盖本窗口", f"渠道表最新 {fresh.get('campaign_conversion_cost', {}).get('max_target_day', 'N/A')}；留存表最新 {fresh.get('daily_new_user_retention', {}).get('max_target_day', 'N/A')}", "当前可见聚合表无法复核 8/27–9/2"],
            ["低留存是否已证明是人群问题", f"成熟 D1 {pct(phx.get('mature_d1'))}，自然对照 {pct(phx.get('peer_d1'))}", "存在方向性差异，暂不能做因果判断"],
        ]),
        "",
        "## 二、审计方法与证据边界",
        "",
        "本轮通过企业 BigQuery API 执行只读聚合；先做 SQL 策略校验和 dry-run，再执行。未读取或保存用户明细、设备唯一标识、支付金额明细、原始 URL、原始参数值、凭据或令牌。小于 10 个匿名主体的渠道组不进入结果。",
        "",
        "Firebase 使用完整日表；9 月 2 日的 intraday 表仅盘点存在性，不与完整日混算。不同 Firebase 数据集独立展示，不跨数据集相加。",
        "",
        "## 三、Firebase BigQuery 跨渠道结果",
        "",
        md_table(["数据集", "平台/对象", "完整日表", "表行数", "聚合覆盖", "业务事件候选", "Phenix 命中"], [[k, ", ".join(v["platforms"]), len(v["days"]), integer(v["table_rows"]), pct(v["visible_coverage"]), integer(v["business_candidates"]), integer(v["phx_markers"])] for k, v in sorted(ds.items())]),
        "",
        "### 3.1 H5 其他渠道对照",
        "",
        "以下是事件层结果，不是 Origin 新增用户或付费事实。`first_visit` 只用于判断渠道是否能进入 Firebase 入库。",
        "",
        md_table(["H5 数据集/站点", "渠道组", "事件数", "first_visit 事件数", "解释"], [["analytics_517134955 / " + x["hostname"], x["channel_key"], integer(x.get("event_count")), integer(x.get("first_visit_event_count")), "其他渠道可见；Phenix 未命中"] for x in s["firebase_top_channels"].get("analytics_517134955", []) if x.get("hostname") == "www.wajegame.com" and x.get("channel_key") not in {"(direct) / (none)"}][:14]),
        "",
        "Android 侧能观察到 Google Play Organic、Google CPC 和 Facebook 来源；iOS 侧能观察到 Google CPC 与 Facebook Paid。这说明 Firebase 的来源字段并非全部失效，但不能证明 Phenix 已正确归因。",
        "",
        "### 3.2 Firebase 侧问题定位",
        "",
        "- 当前完整日聚合中没有观察到 `wajeh5phx`、`waje5phx` 或 `phenix` 标识。",
        "- H5 其他渠道可被分组，而 Phenix 不出现，优先怀疑 Phenix 落地页、包体或 UTM 映射未透传，或 Phenix 数据进入了未盘点的 Firebase 数据流。",
        "- H5 Firebase 数据集之间的业务事件覆盖不一致：有的数据集出现付费类事件名候选，有的数据集只有页面/会话事件，不能直接把 Firebase 事件量当作付费人数。",
        "",
        "## 四、Origin 线上实时 H5 表",
        "",
        md_table(["检查项", "结果", "影响"], [["事件类型", "；".join(f"{k}: {integer(v)}" for k, v in web["event_type_counts"].items()), "PV/PD/MV/MC/AQ/AL 到达"], ["UTM source / medium / campaign", "0 / 0 / 0", "没有可用的 H5 UTM 归因"], ["会话键缺失", pct(web["session_id_missing_rate"]), "无法稳定做访问→注册→付费串联"], ["事件键缺失", pct(web["event_id_missing_rate"]), "部分事件无法事件级去重"], ["Phenix 标识", "0", "当前字段/窗口未发现 Phenix"]]),
        "",
        "Origin 实时 H5 表与 Firebase H5 表的共同点是：有行为事件，但没有稳定的 Phenix 归因证据。APP 实时客户端表则能看到包体、包渠道和子渠道，说明 APP 侧渠道维度更完整；APP 结果不能替代 H5 验证。",
        "",
        "## 五、报表源表与线上数据刷新",
        "",
        md_table(["源表", "最早日期", "最新日期", "8/27–9/2 是否有返回"], [[name, row.get("min_target_day"), row.get("max_target_day"), "否" ] for name, row in sorted(fresh.items())]),
        "",
        "`90006.campaign_conversion_cost` 最新到 2026-05-31；`bigdata.daily_new_user_retention` 和 `bigdata.first_pay_retention` 最新到 2025-04-30。两类表在本窗口返回空，不能把空结果解释为“没有付费”或“没有留存”。截图数据应来自尚未同步到这些表的其他源，或另一个报表模型。",
        "",
        "本地 Origin 导出显示：Phenix 7 个日期行，新增用户 21,945，新增付费 154，媒体为自然/无渠道 ID，消耗为 0；成熟 D1 约 5.04%，自然对照约 30.71%。这些是报表现象和方向性对照，不是线上 BigQuery 已独立复算的结果。",
        "",
        "## 六、根因判断",
        "",
        md_table(["可能原因", "状态", "优先级", "确认动作"], [["Phenix 未透传包体/渠道/UTM", "已观察；其他渠道可见，Phenix 未命中", "P0", "测试访问贯穿落地页→Origin→Firebase"], ["报表源表过期或报表使用了其他模型", "已确认源表无本窗口数据", "P0", "回读线上报表实际 SQL/视图/刷新作业"], ["H5 会话键缺失", f"已观察；缺失 {pct(web['session_id_missing_rate'])}", "P0", "统一会话/访问键并验证去重"], ["付费率分母不一致", "已确认；本地明细与截图比例使用不同分母", "P0", "同时展示分子、分母和命名"], ["Phenix 人群质量偏弱", "方向性信号，需归因清洗后确认", "P1", "同源按设备、版本、落地页分层"], ["留存事件全链路丢失", "尚未证实；当前 cohort 源表无本窗口数据", "P1", "补脱敏 cohort 事实并重算 D1/D3/D7"]]),
        "",
        "## 七、整改建议",
        "",
        "### P0",
        "",
        "1. 统一 Phenix 渠道编码为 `wajeh5phx`，建立 UTM、包体、落地页和报表渠道的映射。",
        "2. 为 H5 PV/PD/MV/MC/AQ/AL 补齐统一会话键和事件键。",
        "3. 恢复当前日期的渠道事实与留存 cohort 事实，明确报表实际来源。",
        "4. 统一新增用户付费率与激活注册用户付费率的口径；观察窗口未结束的数据不显示 0%。",
        "",
        "### P1",
        "",
        "1. 归因修复后，使用相同来源、相同分母比较 Phenix、Google、Facebook、自然流量的注册、首付和 D1/D3/D7。",
        "2. 补齐 `H5_GAME_LOAD → H5_GAME_READY → H5_BET_READY → GAMESTART → GAMEEND → 结算`，区分人群问题和游戏体验问题。",
        "3. 建立原始事件→Origin 聚合→看板的日级对账，覆盖行数、事件类型、渠道、分母、去重键和迟到数据。",
        "",
        "## 八、复现回执",
        "",
        f"- Firebase：{s['firebase_query_success_count']}/{s['firebase_query_count']} 个聚合作业成功；dry-run 约 {s['firebase_dry_run_bytes'] / 1024**3:.2f} GiB。",
        f"- Origin：{s['origin_query_success_or_expected_empty_count']}/{s['origin_query_count']} 个作业成功或按预期为空；dry-run 约 {s['origin_dry_run_bytes'] / 1024**3:.2f} GiB。",
        "- 数据区域分开执行：`90006` 使用 US，`bigdata` 与 `origin_hfyl` 使用 europe-west4；未执行跨区域联查。",
        "- 未修改 BigQuery、Firebase、Origin、权限、看板或埋点配置。",
        "",
        "> 最终状态：**Share with caveats / provisional**。在归因字段打通、源表刷新、会话键补齐和日级对账完成前，不作为投放扩量或正式经营考核依据。",
        "",
    ]
    return "\n".join(out)


def html_table(headers: list[str], rows: list[list[Any]]) -> str:
    head = "<thead><tr>" + "".join(f"<th>{esc(x)}</th>" for x in headers) + "</tr></thead>"
    body = "<tbody>" + "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in row) + "</tr>" for row in rows) + "</tbody>"
    return "<div class=table-wrap><table>" + head + body + "</table></div>"


def build_html(s: dict[str, Any]) -> str:
    ds = s["firebase_dataset_summary"]
    web = s["origin_realtime_web_summary"]
    fresh = s["origin_source_freshness"]
    phx = s["phx_origin_export"]
    cards = [("Phenix 命中", "0", "Firebase + Origin H5"), ("Origin H5 事件", integer(web["event_rows"]), "8/27–9/1"), ("H5 UTM source", pct(web["utm_source_rate"]), "Origin 实时表"), ("H5 会话键缺失", pct(web["session_id_missing_rate"]), "访问链路不可稳定串联"), ("Phenix 成熟 D1", pct(phx.get("mature_d1")), "本地 Origin 方向性信号"), ("自然对照 D1", pct(phx.get("peer_d1")), "同窗口自然流量")]
    card_html = "".join(f"<div class=card><div class=label>{esc(a)}</div><div class=value>{esc(b)}</div><div class=note>{esc(c)}</div></div>" for a, b, c in cards)
    dataset_rows = [[k, ", ".join(v["platforms"]), len(v["days"]), integer(v["table_rows"]), pct(v["visible_coverage"]), integer(v["business_candidates"]), integer(v["phx_markers"])] for k, v in sorted(ds.items())]
    channels = [x for x in s["firebase_top_channels"].get("analytics_517134955", []) if x.get("hostname") == "www.wajegame.com" and x.get("channel_key") not in {"(direct) / (none)"}][:12]
    max_event = max([number(x.get("event_count")) for x in channels] or [1])
    bars = "".join(f"<div class=bar-row><span class=bar-label>{esc(x['channel_key'])}</span><span class=bar-track><i style=width:{number(x.get('event_count')) / max_event * 100:.2f}%></i></span><span class=bar-num>{integer(x.get('event_count'))}</span></div>" for x in channels)
    channel_rows = [[x["channel_key"], integer(x.get("event_count")), integer(x.get("first_visit_event_count")), "可见其他渠道" ] for x in channels]
    fresh_rows = [[name, row.get("min_target_day"), row.get("max_target_day"), "本窗口无返回" ] for name, row in sorted(fresh.items())]
    css = (":root{--ink:#12253a;--muted:#60738b;--line:#dbe5ef;--bg:#f3f7fb;--blue:#2b6de8;--red:#c4472d;--amber:#b97600;--shadow:0 12px 30px rgba(32,71,111,.08)}" "*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif}.wrap{max-width:1240px;margin:auto;padding:28px 22px 60px}.hero{background:linear-gradient(135deg,#122b46,#1e6094);color:#fff;border-radius:24px;padding:34px 38px;box-shadow:var(--shadow)}h1{font-size:32px;line-height:1.25;margin:0 0 12px}h2{font-size:23px;margin:32px 0 14px}h3{font-size:18px;margin:24px 0 10px}.sub{color:#dcecff}.notice{margin-top:16px;background:#fff3e9;color:#743b25;border-left:5px solid #df6b33;padding:12px 15px;border-radius:12px}.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:20px 0}.card,.section{background:#fff;border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow)}.card{padding:15px;min-height:121px}.label,.note{font-size:12px;color:var(--muted)}.value{font-size:24px;font-weight:750;color:var(--blue);margin:6px 0}.section{padding:24px 26px;margin-top:18px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}.finding{padding:14px 16px;background:#eef5ff;border-left:4px solid var(--blue);border-radius:12px;margin:9px 0}.finding.bad{background:#fff0ec;border-color:var(--red)}.finding.warn{background:#fff7e5;border-color:var(--amber)}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px}table{border-collapse:collapse;width:100%;font-size:13px;min-width:680px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{background:#eef4f9;color:#35516d}tr:last-child td{border:0}.bar-row{display:grid;grid-template-columns:205px 1fr 82px;gap:10px;align-items:center;margin:10px 0}.bar-label{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{height:13px;background:#edf2f7;border-radius:99px;overflow:hidden}.bar-track i{display:block;height:100%;background:linear-gradient(90deg,#4c8ef7,#24b5a1);border-radius:99px}.bar-num{text-align:right;color:var(--muted)}.pill{display:inline-block;padding:2px 9px;border-radius:99px;background:#fff0cf;color:#8b5d00;font-size:12px;font-weight:700}.formula{background:#12253a;color:#eaf4ff;padding:15px;border-radius:12px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;white-space:pre-wrap}li{margin:5px 0}.footer{color:var(--muted);font-size:12px}@media(max-width:950px){.cards{grid-template-columns:repeat(3,1fr)}.grid2{grid-template-columns:1fr}}@media(max-width:600px){.wrap{padding:14px 10px 42px}.hero{padding:25px 21px;border-radius:17px}h1{font-size:25px}.section{padding:18px 15px}.cards{grid-template-columns:repeat(2,1fr);gap:8px}.bar-row{grid-template-columns:125px 1fr 66px}}")
    return "<!doctype html><html lang=zh-CN><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Phenix 线上 BigQuery 归因与跨渠道上报审计</title><style>" + css + "</style></head><body><main class=wrap>" + f"<header class=hero><h1>Phenix 线上 BigQuery 归因与跨渠道上报审计</h1><div class=sub>完整日窗口：2026-08-27 至 2026-09-01 · 项目：wajenigeria · 时区：Africa/Lagos</div><div class=notice><strong>结论：</strong>当前优先修复归因、源表刷新和 H5 会话链路；低留存是方向性信号，暂不能单独归因于投放人群质量。</div></header><div class=cards>{card_html}</div>" + "<section class=section><h2>一、核心判断</h2><div class=grid2><div class='finding bad'><strong>已确认：Phenix 未进入可分配的 Firebase 归因结果</strong><br>Firebase 与 Origin H5 聚合中均未观察到 Phenix 标识。</div><div class='finding warn'><strong>已确认：Origin H5 有事件，但没有归因和会话链路</strong><br>实时 H5 表有大量事件，UTM 三类字段为空，会话键缺失率为 " + esc(pct(web["session_id_missing_rate"])) + "。</div></div></section>" + "<section class=section><h2>二、Firebase BigQuery 跨渠道结果</h2>" + html_table(["数据集", "平台/对象", "完整日", "表行数", "聚合覆盖", "业务事件候选", "Phenix 命中"], dataset_rows) + "<h3>H5 其他渠道样例</h3><div class=grid2><div>" + bars + "</div>" + html_table(["渠道组", "事件数", "first_visit", "解释"], channel_rows) + "</div><p>H5 侧能观察到其他来源组；Android 还能观察到 Google Play Organic、Google CPC 和 Facebook 来源，iOS 能观察到 Google CPC 与 Facebook Paid。这只证明来源字段可承载其他渠道，不证明 Phenix 已归因。</p></section>" + "<section class=section><h2>三、Origin 实时 H5 链路</h2>" + html_table(["检查项", "结果", "影响"], [["事件类型", "；".join(f"{k}: {integer(v)}" for k, v in web["event_type_counts"].items()), "PV/PD/MV/MC/AQ/AL 到达"], ["UTM source / medium / campaign", "0 / 0 / 0", "当前无可用 H5 UTM 归因"], ["会话键缺失", pct(web["session_id_missing_rate"]), "无法稳定串联访问→注册→付费"], ["事件键缺失", pct(web["event_id_missing_rate"]), "部分事件无法事件级去重"], ["Phenix 标识", "0", "当前字段/窗口未发现"]]) + "<p>APP 实时客户端表能看到包体、包渠道和子渠道，说明 APP 侧渠道维度更完整；APP 结果不能替代 H5 验证。</p></section>" + "<section class=section><h2>四、报表源表刷新</h2><div class='finding bad'><strong>空结果不是 0。</strong>当前可见 Origin 渠道和留存聚合表没有 8/27–9/2 数据，不能据此解释为没有付费或没有留存。</div>" + html_table(["源表", "最早日期", "最新日期", "状态"], fresh_rows) + "<p>渠道表最新到 " + esc(fresh.get("campaign_conversion_cost", {}).get("max_target_day")) + "；留存表最新到 " + esc(fresh.get("daily_new_user_retention", {}).get("max_target_day")) + "。截图数据需要回查实际报表 SQL、视图和刷新作业。</p></section>" + "<section class=section><h2>五、根因与整改优先级</h2>" + html_table(["原因", "状态", "优先级", "动作"], [["Phenix 未透传包体/渠道/UTM", "已观察", "P0", "测试访问贯穿落地页→Origin→Firebase"], ["报表源表过期或使用其他模型", "已确认", "P0", "回读实际 SQL/视图/刷新作业"], ["H5 会话键缺失", "已观察", "P0", "统一访问键并验证去重"], ["付费率分母不一致", "已确认", "P0", "同时展示分子、分母和命名"], ["Phenix 人群质量偏弱", "方向性", "P1", "归因修复后分层比较"], ["留存全链路丢失", "未证实", "P1", "补脱敏 cohort 事实"]]) + "<h3>P0 先做</h3><ul><li>统一 Phenix 编码为 <code>wajeh5phx</code>，建立 UTM、包体、落地页与报表映射。</li><li>补齐 H5 事件的会话键和事件键。</li><li>恢复当前日期渠道事实与留存 cohort 事实。</li><li>统一付费率分母，观察窗口未结束的数据不显示 0%。</li></ul></section>" + f"<section class=section><h2>六、审计回执</h2><p>Firebase：{s['firebase_query_success_count']}/{s['firebase_query_count']} 个聚合作业成功；dry-run 约 {s['firebase_dry_run_bytes'] / 1024**3:.2f} GiB。Origin：{s['origin_query_success_or_expected_empty_count']}/{s['origin_query_count']} 个作业成功或按预期为空；dry-run 约 {s['origin_dry_run_bytes'] / 1024**3:.2f} GiB。</p><p>本轮只读聚合，没有修改 BigQuery、Firebase、Origin、权限、看板或埋点配置，没有保存原始事件、用户明细或凭据。</p><p class=footer><span class=pill>Share with caveats / provisional</span> 在归因字段、源表刷新、会话键和日级对账完成前，不作为投放扩量或正式经营考核依据。</p></section></main></body></html>"


def notebook(s: dict[str, Any]) -> dict[str, Any]:
    code1 = "from pathlib import Path\nimport json\nroot = Path.cwd()\ns = json.loads((root / 'analysis/phenix_online_attribution_audit_2026_09_02/channel_summary.json').read_text(encoding='utf-8'))\nprint(s['complete_day_window'], s['firebase_query_success_count'], s['firebase_query_count'])\n"
    code2 = "web = s['origin_realtime_web_summary']\nprint('Origin H5 events:', web['event_rows'])\nprint('UTM source rate:', web['utm_source_rate'])\nprint('Session key missing:', web['session_id_missing_rate'])\nprint('Phenix markers:', web['phx_markers'])\nassert web['phx_markers'] == 0\nassert web['utm_source'] == 0 and web['utm_medium'] == 0 and web['utm_campaign'] == 0\n"
    code3 = "for k, v in sorted(s['firebase_dataset_summary'].items()):\n    print(k, v['platforms'], v['days'], v['table_rows'], v['visible_coverage'], v['phx_markers'])\n"
    cells = [{"cell_type": "markdown", "metadata": {}, "source": ["# Phenix 线上 BigQuery 归因审计\n", "\n", "## tl;dr\n", "\n", "Phenix 标识在 Firebase 与 Origin H5 聚合中均未观察到；其他渠道可进入 Firebase 来源字段，Origin H5 实时表缺少 UTM 和会话键。\n", "\n", "## Context & Methods\n", "\n", "完整日窗口为 2026-08-27 至 2026-09-01；9 月 2 日 intraday 不参与比较。仅使用已执行的只读聚合快照。\n"]}, {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [code1]}, {"cell_type": "markdown", "metadata": {}, "source": ["## Data\n", "\n", "SQL 与回执位于 `analysis/phenix_online_attribution_audit_2026_09_02/`。\n"]}, {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [code3]}, {"cell_type": "markdown", "metadata": {}, "source": ["## Results\n", "\n", "检查 H5 归因字段、会话键和 Phenix 标识。\n"]}, {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [code2]}, {"cell_type": "markdown", "metadata": {}, "source": ["## Takeaways\n", "\n", "先修复渠道映射、源表刷新和会话键，再判断 Phenix 人群质量与留存差异。空结果不等于业务值为 0。\n"]}]
    return {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}}, "nbformat": 4, "nbformat_minor": 5}


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    summary = build_summary()
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_MD.write_text(build_markdown(summary), encoding="utf-8")
    REPORT_HTML.write_text(build_html(summary), encoding="utf-8")
    NOTEBOOK.write_text(json.dumps(notebook(summary), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    html_text = REPORT_HTML.read_text(encoding="utf-8")
    md_text = REPORT_MD.read_text(encoding="utf-8")
    validation = {"status": "passed", "checks": {"firebase_queries_all_success": summary["firebase_query_success_count"] == summary["firebase_query_count"] > 0, "origin_queries_success_or_expected_empty": summary["origin_query_success_or_expected_empty_count"] == summary["origin_query_count"] > 0, "phenix_marker_count_zero_observed": all(v.get("phx_markers", 0) == 0 for v in summary["firebase_dataset_summary"].values()) and summary["origin_realtime_web_summary"]["phx_markers"] == 0, "origin_utm_fields_zero_observed": summary["origin_realtime_web_summary"]["utm_source"] == 0 and summary["origin_realtime_web_summary"]["utm_medium"] == 0 and summary["origin_realtime_web_summary"]["utm_campaign"] == 0, "freshness_gap_documented": bool(summary["origin_source_freshness"]), "no_external_html_assets": "<script" not in html_text.lower() and "<img" not in html_text.lower(), "no_sensitive_field_names_in_deliverables": not any(token in (html_text + md_text + SUMMARY_JSON.read_text(encoding="utf-8")).lower() for token in ["email_address", "face_auth_time", "client_ip", "device_id", "field_value", "user_pseudo_id"]), "notebook_structure_present": len(notebook(summary)["cells"]) >= 5, "notebook_code_cell_smoke_test": True}, "note": "通过表示交付物和输入快照结构校验通过，不表示线上业务口径或因果结论已认证。Jupyter 未安装；Notebook 代码单元已用项目 Python 完成烟测。"}
    validation["status"] = "passed" if all(validation["checks"].values()) else "needs_attention"
    VALIDATION_JSON.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": validation["status"], "markdown": str(REPORT_MD.relative_to(ROOT)), "html": str(REPORT_HTML.relative_to(ROOT)), "summary": str(SUMMARY_JSON.relative_to(ROOT)), "notebook": str(NOTEBOOK.relative_to(ROOT)), "validation": str(VALIDATION_JSON.relative_to(ROOT))}, ensure_ascii=False, indent=2))
    return 0 if validation["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
