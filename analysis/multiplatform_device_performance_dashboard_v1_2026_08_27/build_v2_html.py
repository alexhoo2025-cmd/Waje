#!/usr/bin/env python3
"""Build the polished local dashboard and report reading surfaces.

The source snapshot is aggregate-only and was collected from the enterprise
BigQuery project.  This renderer intentionally contains no network calls and
never embeds row-level identifiers or event payloads.
"""

from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "actual_baseline.json"
DASHBOARD = ROOT / "dashboard_v2.html"
PREVIEW = ROOT / "dashboard_preview.html"
REPORT = ROOT / "report_v2.html"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def compact(value: int | float) -> str:
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M".rstrip("0").rstrip(".")
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}k".rstrip("0").rstrip(".")
    return f"{value:,.0f}"


def status_badge(status: str) -> str:
    labels = {
        "provisional": ("试运行", "warn"),
        "provisional_behavior_only": ("仅行为基线", "warn"),
        "provisional_quality_warning": ("质量警告", "warn"),
        "provisional_schema_mapping": ("待字段认证", "warn"),
        "immature": ("未成熟", "info"),
        "data_gap": ("数据缺口", "danger"),
        "blocked": ("受阻", "danger"),
    }
    label, tone = labels.get(status, (status, "neutral"))
    return f'<span class="badge badge-{tone}">{esc(label)}</span>'


def bars(rows: list[dict], label_key: str, value_key: str, *, value_suffix: str = "", max_rows: int = 10) -> str:
    rows = rows[:max_rows]
    values = [float(row.get(value_key) or 0) for row in rows]
    maximum = max(values, default=1) or 1
    blocks = []
    for row, value in zip(rows, values):
        width = max(2, round(value / maximum * 100)) if value else 0
        blocks.append(
            f'<div class="bar-row"><div class="bar-label">{esc(row.get(label_key, ""))}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>'
            f'<div class="bar-value">{compact(value)}{esc(value_suffix)}</div></div>'
        )
    return "".join(blocks)


def coverage_table(rows: list[dict]) -> str:
    body = []
    for row in rows:
        body.append(
            "<tr>"
            f"<td><strong>{esc(row['endpoint'])}</strong></td>"
            f"<td>{esc(row['source'])}</td>"
            f"<td>{esc(row['first_day'])} → {esc(row['last_day'])}</td>"
            f"<td class=\"num\">{row['covered_days']}</td>"
            f"<td>{status_badge(row['status'])}</td>"
            "</tr>"
        )
    return "".join(body)


def metric_rows() -> list[dict[str, str]]:
    return [
        {"metric": "数据覆盖率", "definition": "实际到达完整数据日 ÷ 请求数据日", "formula": "COUNT(complete_day) / COUNT(requested_day)", "grain": "日期 × 端 × 来源 × 包体", "source": "mart_endpoint_coverage_daily", "state": "全端必备"},
        {"metric": "会话开始事件数", "definition": "Analytics 中 event_name=session_start 的事件记录数", "formula": "COUNTIF(event_name = 'session_start')", "grain": "日期 × 端 × 包体 × 版本", "source": "mart_event_session_daily", "state": "已具备"},
        {"metric": "Android 去标识化会话数", "definition": "Firebase Sessions 范围内的唯一 session_id 数", "formula": "COUNT(DISTINCT session_id)", "grain": "日期 × Android 包 × 版本", "source": "mart_endpoint_coverage_daily", "state": "仅 Android"},
        {"metric": "原生轨迹 P95", "definition": "合格 DURATION_TRACE 时长的第 95 分位", "formula": "APPROX_QUANTILES(duration_ms, 100)[OFFSET(95)]；样本≥500", "grain": "日期 × 包 × 版本 × 单一设备维度", "source": "mart_native_performance_daily", "state": "字段已具备，数值待审计"},
        {"metric": "网络 P95", "definition": "NETWORK_REQUEST 响应完成耗时的第 95 分位", "formula": "APPROX_QUANTILES(response_completed_time_us/1000, 100)[OFFSET(95)]；样本≥500", "grain": "日期 × 包 × 版本 × 网络类型", "source": "mart_native_performance_daily", "state": "字段已具备，数值待审计"},
        {"metric": "网络成功率", "definition": "HTTP 200–399 响应数 ÷ 有响应码请求数", "formula": "COUNTIF(code BETWEEN 200 AND 399) / COUNTIF(code IS NOT NULL)", "grain": "日期 × 包 × 版本 × 请求类别", "source": "mart_native_performance_daily", "state": "字段已具备，需请求分类"},
        {"metric": "慢帧/冻结帧比例", "definition": "SCREEN_TRACE 中比例字段的 trace 加权均值", "formula": "AVG(slow_frame_ratio) / AVG(frozen_frame_ratio)", "grain": "日期 × 包 × 版本 × 设备/系统", "source": "mart_native_performance_daily", "state": "字段已具备"},
        {"metric": "Fatal/Non-fatal 事件量", "definition": "按 event_id 去重后的 Fatal 或 Non-fatal 事件数", "formula": "COUNT(DISTINCT IF(is_fatal, event_id, NULL))", "grain": "日期 × 包 × 版本 × 设备/系统", "source": "mart_stability_daily", "state": "可先展示数量"},
        {"metric": "核心漏斗阶段", "definition": "客户端行为表示尝试，Origin 事件表示服务端观察；成功语义单独认证", "formula": "各阶段事件数；禁止直接计算成功率", "grain": "日期 × 端 × 包 × 版本 × 阶段", "source": "mart_core_funnel_daily", "state": "部分试运行"},
        {"metric": "H5 网页性能", "definition": "Web Vitals、路由 ready、核心请求和前端错误指标", "formula": "补埋点后按 measurement_state=complete 计算", "grain": "日期 × 页面 × 版本 × 浏览器/网络", "source": "H5 V2 RUM 事件", "state": "数据缺口"},
    ]


def metric_table() -> str:
    body = []
    for row in metric_rows():
        state = row["state"]
        tone = "danger" if "缺口" in state else "warn" if "待" in state or "部分" in state else "ok"
        body.append(
            "<tr>"
            f"<td><strong>{esc(row['metric'])}</strong><div class=\"muted\">{esc(row['definition'])}</div></td>"
            f"<td><code>{esc(row['formula'])}</code></td>"
            f"<td>{esc(row['grain'])}</td>"
            f"<td>{esc(row['source'])}</td>"
            f"<td><span class=\"state state-{tone}\">{esc(state)}</span></td>"
            "</tr>"
        )
    return "".join(body)


def css() -> str:
    return r"""
:root{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#122033;--muted:#64748b;--line:#e2e8f0;--navy:#102a43;--blue:#1976d2;--cyan:#08a7b9;--green:#15803d;--amber:#b45309;--red:#c2410c;--purple:#6d28d9;--shadow:0 14px 42px rgba(15,38,64,.08);--radius:18px}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","PingFang SC","Hiragino Sans GB","Microsoft YaHei",Arial,sans-serif;font-size:15px;line-height:1.6}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}.topbar{position:sticky;top:0;z-index:20;height:64px;background:rgba(16,42,67,.97);color:#fff;box-shadow:0 4px 18px rgba(15,38,64,.18)}.topbar-inner{max-width:1440px;height:100%;margin:auto;padding:0 28px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:.02em}.brand-mark{width:30px;height:30px;border-radius:10px;background:linear-gradient(135deg,#40c9d7,#1976d2);display:grid;place-items:center;font-size:13px}.top-meta{font-size:12px;color:#cbd5e1;display:flex;align-items:center;gap:14px}.top-meta .dot{width:7px;height:7px;background:#65d38b;border-radius:50%;display:inline-block}.layout{max-width:1440px;margin:auto;display:grid;grid-template-columns:230px minmax(0,1fr);gap:28px;padding:30px 28px 70px}.sidebar{position:sticky;top:94px;align-self:start}.side-title{font-size:11px;letter-spacing:.14em;color:var(--muted);font-weight:700;text-transform:uppercase;margin:0 0 12px}.side-link{display:block;padding:10px 13px;border-left:3px solid transparent;border-radius:0 10px 10px 0;color:var(--muted);font-size:13px}.side-link:hover,.side-link.active{color:var(--navy);background:#eaf2fb;border-left-color:var(--blue);text-decoration:none}.content{min-width:0}.hero{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(250px,.6fr);gap:18px;margin-bottom:22px}.hero-copy,.hero-status{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}.hero-copy{padding:32px 34px;background:linear-gradient(135deg,#fff 40%,#eef8fb)}.eyebrow{font-size:12px;color:var(--blue);font-weight:700;letter-spacing:.06em;margin:0 0 9px}.hero h1{font-size:clamp(28px,4vw,46px);line-height:1.13;letter-spacing:-.045em;margin:0 0 14px;color:var(--navy)}.hero-lede{font-size:17px;color:#3c526b;max-width:680px;margin:0}.hero-status{padding:24px 26px;display:flex;flex-direction:column;justify-content:center;gap:11px}.hero-status h3{margin:0;font-size:15px;color:var(--navy)}.status-line{display:flex;justify-content:space-between;gap:14px;align-items:center;font-size:13px;border-bottom:1px solid var(--line);padding:9px 0}.status-line:last-child{border-bottom:0}.filters{display:flex;align-items:center;gap:9px;flex-wrap:wrap;background:var(--navy);padding:13px 15px;border-radius:14px;margin-bottom:24px}.filter-label{font-size:12px;color:#b9c7d8;margin-right:2px}.filter-button{appearance:none;border:1px solid rgba(255,255,255,.18);background:transparent;color:#dbe7f3;border-radius:999px;padding:7px 13px;font:inherit;font-size:12px;cursor:pointer}.filter-button.active,.filter-button:hover{background:#fff;color:var(--navy);border-color:#fff}.section{scroll-margin-top:86px;margin:0 0 30px}.section-head{display:flex;justify-content:space-between;align-items:end;gap:16px;margin:0 0 14px}.section-head h2{margin:0;color:var(--navy);font-size:25px;letter-spacing:-.025em}.section-head p{margin:0;color:var(--muted);font-size:13px}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:16px}.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:19px 20px;box-shadow:0 8px 25px rgba(15,38,64,.045);min-width:0}.card .label{font-size:12px;color:var(--muted);margin-bottom:7px}.card .value{font-size:28px;line-height:1.1;font-weight:750;color:var(--navy);letter-spacing:-.035em}.card .hint{font-size:12px;color:var(--muted);margin-top:8px;overflow-wrap:anywhere}.card.accent-blue{border-top:4px solid var(--blue)}.card.accent-cyan{border-top:4px solid var(--cyan)}.card.accent-green{border-top:4px solid var(--green)}.card.accent-amber{border-top:4px solid #e7a23b}.grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.panel{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:22px 23px;box-shadow:0 8px 25px rgba(15,38,64,.045);min-width:0}.panel h3{margin:0 0 4px;color:var(--navy);font-size:16px}.panel-sub{margin:0 0 16px;color:var(--muted);font-size:12px}.bar-list{display:grid;gap:12px}.bar-row{display:grid;grid-template-columns:minmax(105px,1.2fr) minmax(100px,2fr) 70px;align-items:center;gap:10px;min-width:0}.bar-label{font-size:12px;color:#334155;overflow-wrap:anywhere}.bar-track{height:10px;background:#e9eff6;border-radius:99px;overflow:hidden}.bar-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--cyan),var(--blue))}.bar-value{font-size:12px;color:var(--navy);font-variant-numeric:tabular-nums;text-align:right;font-weight:700}.endpoint-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}.endpoint-card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:20px;min-width:0;box-shadow:0 8px 25px rgba(15,38,64,.045)}.endpoint-card.android{border-top:4px solid #2b8a5a}.endpoint-card.ios{border-top:4px solid #6d28d9}.endpoint-card.h5{border-top:4px solid #e3982c}.endpoint-top{display:flex;justify-content:space-between;align-items:start;gap:8px}.endpoint-card h3{margin:0;color:var(--navy);font-size:17px}.endpoint-card .sub{font-size:12px;color:var(--muted);margin:3px 0 16px;overflow-wrap:anywhere}.endpoint-fact{display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid var(--line);font-size:13px}.endpoint-fact:last-child{border-bottom:0}.endpoint-fact span:first-child{color:var(--muted)}.endpoint-fact strong{text-align:right;color:var(--navy);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}.badge,.state{display:inline-flex;align-items:center;white-space:nowrap;border-radius:999px;padding:3px 8px;font-size:11px;font-weight:700}.badge-ok,.state-ok{background:#e9f7ee;color:#18723e}.badge-warn,.state-warn{background:#fff3dc;color:#a55a00}.badge-info{background:#e9f1ff;color:#1d5bb5}.badge-danger,.state-danger{background:#fff0eb;color:#b33c14}.badge-neutral{background:#eef2f7;color:#53657a}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--surface)}table{width:100%;border-collapse:collapse;min-width:720px}th,td{padding:12px 13px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left;font-size:12px}th{background:#f5f8fb;color:#40566f;font-size:11px;letter-spacing:.03em;white-space:nowrap}tr:last-child td{border-bottom:0}td.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:700;color:var(--navy)}td code,code{font-family:"SFMono-Regular",Consolas,monospace;font-size:11px;color:#22537c;background:#eff6fb;border-radius:6px;padding:2px 5px;overflow-wrap:anywhere}.muted{color:var(--muted);font-size:11px;margin-top:4px;line-height:1.45}.callout{border-radius:14px;padding:16px 17px;border:1px solid var(--line);background:var(--surface-2);margin-top:14px}.callout strong{color:var(--navy)}.callout.warn{background:#fff9ed;border-color:#f1d9a5}.callout.danger{background:#fff4f0;border-color:#f0c5b4}.callout.ok{background:#effaf3;border-color:#bfe3c9}.columns{columns:2;column-gap:30px}.columns li{break-inside:avoid;margin:0 0 10px;color:#334155;font-size:13px}.columns ul{padding-left:18px;margin:0}.numbered{counter-reset:item;list-style:none;padding:0;margin:0}.numbered li{counter-increment:item;display:grid;grid-template-columns:28px minmax(0,1fr);gap:11px;margin:0 0 13px;font-size:13px}.numbered li:before{content:counter(item);width:24px;height:24px;border-radius:8px;background:#eaf2fb;color:var(--blue);display:grid;place-items:center;font-size:12px;font-weight:700}.hidden{display:none!important}.footer{border-top:1px solid var(--line);padding-top:18px;color:var(--muted);font-size:11px;display:flex;justify-content:space-between;gap:15px;flex-wrap:wrap}.footer a{color:var(--blue)}@media(max-width:1080px){.layout{grid-template-columns:190px 1fr}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.endpoint-grid{grid-template-columns:1fr}.hero{grid-template-columns:1fr}.hero-status{display:grid;grid-template-columns:repeat(3,1fr);gap:0}.status-line{border-bottom:0;border-right:1px solid var(--line);padding:0 12px}.status-line:first-child{padding-left:0}.status-line:last-child{border-right:0;padding-right:0}}@media(max-width:760px){body{font-size:14px}.topbar-inner{padding:0 16px}.top-meta{font-size:11px}.layout{display:block;padding:18px 14px 48px}.sidebar{position:relative;top:auto;display:flex;gap:6px;overflow-x:auto;padding:0 0 14px;margin-bottom:4px}.side-title{display:none}.side-link{white-space:nowrap;border:1px solid var(--line);border-radius:999px;background:var(--surface);padding:7px 11px;font-size:11px}.side-link.active,.side-link:hover{border-color:var(--blue);background:#eaf2fb}.hero-copy{padding:24px 21px}.hero h1{font-size:31px}.hero-lede{font-size:15px}.hero-status{display:block;padding:16px 19px}.status-line{border-bottom:1px solid var(--line);border-right:0;padding:8px 0!important}.status-line:last-child{border-bottom:0}.cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.card{padding:16px}.card .value{font-size:23px}.grid-2{grid-template-columns:1fr}.bar-row{grid-template-columns:minmax(86px,1.2fr) minmax(70px,2fr) 55px;gap:7px}.panel{padding:18px 16px}.section-head{display:block}.section-head h2{font-size:22px}.section-head p{margin-top:4px}.columns{columns:1}.footer{display:block}.footer span{display:block;margin-bottom:6px}}@media(max-width:380px){.cards{grid-template-columns:1fr}.bar-row{grid-template-columns:90px minmax(60px,1fr) 48px}.top-meta .date{display:none}}
"""


def shared_head(title: str, subtitle: str) -> str:
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>{esc(title)}</title><style>{css()}</style></head><body><header class="topbar"><div class="topbar-inner"><div class="brand"><span class="brand-mark">W</span><span>Waje · 端侧体验数据</span></div><div class="top-meta"><span><span class="dot"></span> 数据快照</span><span class="date">2026-08-27 · Africa/Lagos</span></div></div></header>'''


def sidebar() -> str:
    return '''<aside class="sidebar"><p class="side-title">导航</p><a class="side-link active" href="#overview">总览</a><a class="side-link" href="#android">Android</a><a class="side-link" href="#ios">iOS</a><a class="side-link" href="#h5">H5</a><a class="side-link" href="#metrics">指标口径</a><a class="side-link" href="#gaps">缺口与动作</a></aside>'''


def dashboard_html(data: dict) -> str:
    coverage = data["source_coverage"]
    performance = data["native_performance"]
    sessions = data["android_sessions"]
    h5_events = data["h5_event_dictionary"]
    total_native = sum(int(row["performance_record_count"]) for row in performance)
    total_sessions = sum(int(row["distinct_session_count"]) for row in sessions)
    total_h5 = sum(int(row["event_count"]) for row in h5_events)
    android_perf = [row for row in performance if row["endpoint"].startswith("android_")]
    ios_perf = [row for row in performance if row["endpoint"] == "ios_existing"]
    dashboard_script = '''<script>const endpointButtons=[...document.querySelectorAll('[data-endpoint]')].filter(x=>x.tagName==='BUTTON');const viewButtons=[...document.querySelectorAll('[data-view]')];let endpoint='all',view='all';function refresh(){document.querySelectorAll('[data-panel]').forEach(p=>{const e=p.dataset.endpoint.split(' '),v=p.dataset.panel.split(' ');p.classList.toggle('hidden',!(e.includes('all')||e.includes(endpoint))||!(v.includes('all')||v.includes(view)));});endpointButtons.forEach(b=>b.classList.toggle('active',b.dataset.endpoint===endpoint));viewButtons.forEach(b=>b.classList.toggle('active',b.dataset.view===view));}endpointButtons.forEach(b=>b.addEventListener('click',()=>{endpoint=b.dataset.endpoint;refresh()}));viewButtons.forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;refresh()}));refresh();</script>'''
    html_body = f'''<div class="layout">{sidebar()}<main class="content">
<section class="hero" id="overview"><div class="hero-copy"><p class="eyebrow">设备 · 性能 · 事件/会话 · V1 预览</p><h1>先看数据是否可信，<br>再看哪一端需要优化。</h1><p class="hero-lede">这是一份基于企业 BigQuery 当前实际聚合数据的看板预览。Android、iOS、H5 分开计算；缺数据、未成熟和未补埋点均保留状态，不用零值填充。</p></div><div class="hero-status"><h3>当前状态</h3><div class="status-line"><span>正式聚合层</span>{status_badge('blocked')} </div><div class="status-line"><span>Metabase 远端看板</span>{status_badge('blocked')}</div><div class="status-line"><span>数据读取范围</span><strong>仅聚合</strong></div></div></section>
<div class="filters" role="group" aria-label="看板筛选"><span class="filter-label">端侧</span><button class="filter-button active" data-endpoint="all">全部</button><button class="filter-button" data-endpoint="android">Android</button><button class="filter-button" data-endpoint="ios">iOS</button><button class="filter-button" data-endpoint="h5">H5</button><span class="filter-label" style="margin-left:8px">视图</span><button class="filter-button active" data-view="all">全部指标</button><button class="filter-button" data-view="device">设备</button><button class="filter-button" data-view="performance">性能</button><button class="filter-button" data-view="event">事件/会话</button></div>
<section class="section" data-panel="all device performance event" data-endpoint="all android ios h5"><div class="section-head"><div><h2>当前可用规模</h2><p>这些是已从当前数据源实际汇总出来的数值；不是用户数、转化率或性能评分。</p></div></div><div class="cards"><div class="card accent-blue"><div class="label">原生性能记录</div><div class="value">{compact(total_native)}</div><div class="hint">Android 三包 + iOS Performance</div></div><div class="card accent-cyan"><div class="label">Android 去标识化会话</div><div class="value">{compact(total_sessions)}</div><div class="hint">仅 Firebase Sessions 口径</div></div><div class="card accent-amber"><div class="label">H5 标准行为事件</div><div class="value">{compact(total_h5)}</div><div class="hint">8 个数据日 · 4 类事件</div></div><div class="card accent-green"><div class="label">当前可见数据源</div><div class="value">{len(coverage)}</div><div class="hint">按端侧和产品拆分</div></div></div></section>
<section class="section" data-panel="all performance event" data-endpoint="all android ios h5"><div class="section-head"><div><h2>数据覆盖与成熟度</h2><p>不足 7 个完整日的端侧不参与跨端趋势比较。</p></div></div><div class="grid-2"><div class="panel"><h3>来源覆盖天数</h3><p class="panel-sub">最新日只代表当前已到达的最大日期，不代表没有更晚数据。</p><div class="bar-list">{bars(coverage, 'source', 'covered_days', value_suffix=' 天', max_rows=10)}</div></div><div class="panel"><h3>质量提醒</h3><p class="panel-sub">看板应先展示这些状态，再展示业务数字。</p><div class="callout danger"><strong>H5 性能：数据缺口</strong><br><span class="muted">没有 Web Vitals、路由 ready、核心请求、前端错误或游戏就绪事件。</span></div><div class="callout warn"><strong>Android Sessions / Performance：口径冲突</strong><br><span class="muted">Sessions 的 Performance 开关为 false，但 Performance 表已有记录；不使用开关判断性能覆盖。</span></div><div class="callout warn"><strong>跨端趋势：尚未成熟</strong><br><span class="muted">Android Analytics 仅 1 天，iOS Analytics 5 天，H5 8 天。</span></div></div></div></section>
<section class="section" id="android" data-panel="all device performance event" data-endpoint="android"><div class="section-head"><div><h2>Android · 三包独立看</h2><p>当前 Performance 已形成 7 日基线；Analytics 仍只有 8 月 24 日。</p></div>{status_badge('provisional')}</div><div class="endpoint-grid"><div class="endpoint-card android"><div class="endpoint-top"><h3>主包</h3>{status_badge('provisional')}</div><p class="sub">com.hfhy.waje.special</p><div class="endpoint-fact"><span>Performance 记录</span><strong>{compact(android_perf[0]['performance_record_count'])}</strong></div><div class="endpoint-fact"><span>性能覆盖</span><strong>08-20 → 08-26</strong></div><div class="endpoint-fact"><span>版本数</span><strong>{android_perf[0]['app_version_count']}</strong></div><div class="endpoint-fact"><span>Sessions</span><strong>{compact(sessions[0]['distinct_session_count'])}</strong></div></div><div class="endpoint-card android"><div class="endpoint-top"><h3>传音老包</h3>{status_badge('provisional')}</div><p class="sub">com.hfhy.wajecasino.palmgame</p><div class="endpoint-fact"><span>Performance 记录</span><strong>{compact(android_perf[1]['performance_record_count'])}</strong></div><div class="endpoint-fact"><span>性能覆盖</span><strong>08-20 → 08-26</strong></div><div class="endpoint-fact"><span>版本数</span><strong>{android_perf[1]['app_version_count']}</strong></div><div class="endpoint-fact"><span>Sessions</span><strong>{compact(sessions[1]['distinct_session_count'])}</strong></div></div><div class="endpoint-card android"><div class="endpoint-top"><h3>传音新包</h3>{status_badge('provisional')}</div><p class="sub">com.hfhy.wajecasino.game</p><div class="endpoint-fact"><span>Performance 记录</span><strong>{compact(android_perf[2]['performance_record_count'])}</strong></div><div class="endpoint-fact"><span>性能覆盖</span><strong>08-20 → 08-26</strong></div><div class="endpoint-fact"><span>版本数</span><strong>{android_perf[2]['app_version_count']}</strong></div><div class="endpoint-fact"><span>Sessions</span><strong>{compact(sessions[2]['distinct_session_count'])}</strong></div></div></div><div class="grid-2" style="margin-top:16px"><div class="panel"><h3>Performance 记录量</h3><p class="panel-sub">记录量用于判断是否有样本，不用于判断哪一包性能更好。</p><div class="bar-list">{bars(android_perf, 'label', 'performance_record_count')}</div></div><div class="panel"><h3>Android 看板首屏应放什么</h3><ol class="numbered"><li>轨迹 P95：样本 ≥500 后显示。</li><li>网络 P95 与 HTTP 成功率：按请求类别统计。</li><li>慢帧、冻结帧：按包、版本、设备单维度分层。</li><li>Fatal/Non-fatal/问题数：先展示数量，不展示未经认证的比率。</li></ol></div></div></section>
<section class="section" id="ios" data-panel="all device performance event" data-endpoint="ios"><div class="section-head"><div><h2>iOS · 现有来源单独看</h2><p>当前来源为 com.wajegame.wajegame；Analytics/Performance 尚未达到 7 日趋势门槛。</p></div>{status_badge('immature')}</div><div class="endpoint-grid"><div class="endpoint-card ios"><div class="endpoint-top"><h3>Analytics</h3>{status_badge('immature')}</div><p class="sub">5 个日表：08-20 → 08-24</p><div class="endpoint-fact"><span>可观察维度</span><strong>版本 / 系统 / 设备 / 地域</strong></div><div class="endpoint-fact"><span>主要用途</span><strong>行为事件与版本切片</strong></div><div class="endpoint-fact"><span>跨端趋势</span><strong>未成熟</strong></div></div><div class="endpoint-card ios"><div class="endpoint-top"><h3>Performance</h3>{status_badge('immature')}</div><p class="sub">com_wajegame_wajegame_IOS</p><div class="endpoint-fact"><span>性能记录</span><strong>{compact(ios_perf[0]['performance_record_count'])}</strong></div><div class="endpoint-fact"><span>性能覆盖</span><strong>08-20 → 08-25</strong></div><div class="endpoint-fact"><span>版本数</span><strong>{ios_perf[0]['app_version_count']}</strong></div><div class="endpoint-fact"><span>Crashlytics</span><strong>当前未见导出表</strong></div></div><div class="endpoint-card ios"><div class="endpoint-top"><h3>首屏卡片</h3>{status_badge('provisional')}</div><p class="sub">只放已具备且可解释的指标</p><div class="endpoint-fact"><span>网络</span><strong>响应码 / 响应耗时</strong></div><div class="endpoint-fact"><span>屏幕</span><strong>慢帧 / 冻结帧</strong></div><div class="endpoint-fact"><span>待确认</span><strong>当前生产来源映射</strong></div></div></div></section>
<section class="section" id="h5" data-panel="all device performance event" data-endpoint="h5"><div class="section-head"><div><h2>H5 · 行为可看，性能不可编</h2><p>当前 8 个数据日只有四类标准事件，不能把停留或退出代理写成加载速度。</p></div>{status_badge('provisional_behavior_only')}</div><div class="grid-2"><div class="panel"><h3>当前事件结构</h3><p class="panel-sub">事件次数，不是用户数或转化率。</p><div class="bar-list">{bars(h5_events, 'event_name', 'event_count')}</div></div><div class="panel"><h3>H5 现阶段能回答什么</h3><ul class="columns"><li>页面浏览和会话开始是否有数据</li><li>标准互动事件的日变化</li><li>按来源表和日期检查覆盖</li><li>不能回答 LCP、INP、CLS、TTFB</li><li>不能回答白屏、黑屏、JS 错误</li><li>不能回答游戏就绪、可下注与核心请求 P95</li></ul></div></div><div class="callout danger"><strong>必须补齐的 H5 V2 事件：</strong> H5_SESSION_START、H5_NAVIGATION_PERF、H5_CORE_REQUEST、H5_GAME_LOAD、H5_GAME_READY、H5_BET_READY、H5_CLIENT_ERROR、H5_NETWORK_CHANGE、H5_RECOVERY_RESULT、H5_SESSION_END。</div></section>
<section class="section" id="metrics" data-panel="all device performance event" data-endpoint="all android ios h5"><div class="section-head"><div><h2>指标口径与计算方式</h2><p>看板中的每个数字必须同时有定义、分母、粒度、来源和状态。</p></div></div><div class="table-wrap"><table><thead><tr><th>指标</th><th>计算方式</th><th>粒度</th><th>来源</th><th>状态</th></tr></thead><tbody>{metric_table()}</tbody></table></div></section>
<section class="section" id="gaps" data-panel="all device performance event" data-endpoint="all android ios h5"><div class="section-head"><div><h2>缺口与落地动作</h2><p>先补可观测性，再启用正式告警和跨端比较。</p></div></div><div class="grid-2"><div class="panel"><h3>P0 · 立刻补齐</h3><ol class="numbered"><li>创建并授权 BigQuery 聚合数据集，Metabase 只读聚合视图。</li><li>对 Android Performance 做 7 日字段完整率、样本量、重复和新鲜度审计。</li><li>完成 Crashlytics event_id、is_fatal、issue_id 去重和事件分类。</li><li>H5 接入 Web Vitals、路由 ready、核心请求和前端错误。</li></ol></div><div class="panel"><h3>P1 · 形成闭环</h3><ol class="numbered"><li>由 Origin 认证 REGISTER → LOGIN → GAMESTART → GAMEEND 服务端阶段。</li><li>统一 release_id、包体、版本、设备、网络、trace_category。</li><li>积累 7 个稳定日后启用版本回归和 P95 偏离告警。</li><li>性能源最新时间落后 45 分钟时只显示 delayed，不触发产品告警。</li></ol></div></div></section>
<footer class="footer"><span>数据边界：仅企业 BigQuery 聚合结果；未输出用户、设备唯一标识、订单、支付、URL、请求体或堆栈。</span><span><a href="actual_baseline.json">实际基线 JSON</a> · <a href="baseline_aggregate_queries.sql">可复跑 SQL</a> · <a href="metabase_dashboard_contract.json">Metabase 合同</a> · <a href="design_spec_v2.html">详细设计</a></span></footer>
</main></div>{dashboard_script}</body></html>'''
    return shared_head("Waje 多端设备与性能看板 V2", "") + html_body


def report_html(data: dict) -> str:
    metric_table_html = metric_table()
    return shared_head("Waje 多端设备与性能指标报表 V2", "") + f'''<div class="layout">{sidebar()}<main class="content"><section class="hero" id="overview"><div class="hero-copy"><p class="eyebrow">指标报表 · V2</p><h1>Android、iOS、H5<br>分端建立同一套阅读口径。</h1><p class="hero-lede">本报表解释“当前能看什么、怎么算、为什么不能看什么”。所有端侧都先经过数据覆盖和成熟度判断，再进入设备与性能结论。</p></div><div class="hero-status"><h3>报告结论</h3><div class="status-line"><span>Android 原生性能</span>{status_badge('provisional')}</div><div class="status-line"><span>iOS 原生性能</span>{status_badge('immature')}</div><div class="status-line"><span>H5 网页性能</span>{status_badge('data_gap')}</div></div></section>
<section class="section" id="android"><div class="section-head"><div><h2>一、Android：性能数据已入库，正式指标待质量认证</h2><p>三个生产包独立计算，不跨包相加用户或影响用户。</p></div></div><div class="cards"><div class="card accent-green"><div class="label">主包 Performance</div><div class="value">{compact(data['native_performance'][0]['performance_record_count'])}</div><div class="hint">08-20 → 08-26 · 23 个版本</div></div><div class="card accent-green"><div class="label">传音老包 Performance</div><div class="value">{compact(data['native_performance'][1]['performance_record_count'])}</div><div class="hint">08-20 → 08-26 · 4 个版本</div></div><div class="card accent-green"><div class="label">传音新包 Performance</div><div class="value">{compact(data['native_performance'][2]['performance_record_count'])}</div><div class="hint">08-20 → 08-26 · 1 个版本</div></div><div class="card accent-blue"><div class="label">Analytics 数据日</div><div class="value">1</div><div class="hint">仅 08-24，趋势未成熟</div></div></div><div class="panel"><h3>Android 的正式看板结构</h3><div class="table-wrap"><table><thead><tr><th>区域</th><th>首屏指标</th><th>算法/分母</th><th>展示边界</th></tr></thead><tbody><tr><td>启动与轨迹</td><td>轨迹 P95</td><td>合格 DURATION_TRACE 的 duration_us ÷ 1000；第 95 分位；样本≥500</td><td>没有合格样本显示 N/A，不显示 0</td></tr><tr><td>接口网络</td><td>网络 P95、HTTP 成功率</td><td>response_completed_time_us 第 95 分位；200–399 ÷ 有响应码</td><td>先按安全请求类别汇总，不展示 URL</td></tr><tr><td>屏幕流畅</td><td>慢帧、冻结帧比例</td><td>SCREEN_TRACE 对应比例的 trace 加权均值</td><td>不是用户卡顿率</td></tr><tr><td>稳定性</td><td>Fatal、Non-fatal、问题数</td><td>按 event_id、issue_id 去重的事件/问题计数</td><td>未完成 Sessions 分母前不算崩溃率</td></tr></tbody></table></div></div></section>
<section class="section" id="ios"><div class="section-head"><div><h2>二、iOS：有性能字段，但来源和窗口需要单独说明</h2><p>不将现有 iOS 来源直接当作新生产项目，也不与 Android 强行并表。</p></div></div><div class="grid-2"><div class="panel"><h3>当前实际数据</h3><ul class="columns"><li>Analytics：08-20 → 08-24，5 个数据日</li><li>Performance：08-20 → 08-25，约 245 万条记录</li><li>Performance：2 个应用版本</li><li>字段含网络响应码、响应耗时、轨迹时长、慢帧和冻结帧</li><li>Crashlytics：当前企业库未见 iOS 导出表</li></ul></div><div class="panel"><h3>iOS 报表规则</h3><ol class="numbered"><li>展示现有来源标签和数据截止时间。</li><li>只有满 7 个完整日后进入跨端趋势。</li><li>性能 P95 和成功率先做字段填充、样本和异常值检查。</li><li>若确认新 iOS 项目，应新增 endpoint 映射，不覆盖历史来源。</li></ol></div></div></section>
<section class="section" id="h5"><div class="section-head"><div><h2>三、H5：当前只有行为基线，不能输出性能好坏</h2><p>8 个数据日、4 类标准事件；这组数据适合验证访问和互动链路，不适合定位网页性能瓶颈。</p></div></div><div class="grid-2"><div class="panel"><h3>已具备</h3><div class="bar-list">{bars(data['h5_event_dictionary'], 'event_name', 'event_count')}</div></div><div class="panel"><h3>尚缺失</h3><div class="callout danger"><strong>Web RUM 全部缺失</strong><br><span class="muted">LCP、INP、CLS、FCP、TTFB、长任务、资源时序、核心请求状态/耗时、JS 错误、白/黑屏。</span></div><div class="callout danger"><strong>核心游戏阶段缺失</strong><br><span class="muted">H5_GAME_LOAD、H5_GAME_READY、H5_BET_READY 和服务端确认阶段。</span></div></div></div></section>
<section class="section" id="metrics"><div class="section-head"><div><h2>四、指标字典：看板卡片必须按此口径</h2><p>不要只写字段名；每个指标都要能回答定义、分母、粒度、来源和状态。</p></div></div><div class="table-wrap"><table><thead><tr><th>指标</th><th>定义/计算方式</th><th>粒度</th><th>来源</th><th>当前状态</th></tr></thead><tbody>{metric_table_html}</tbody></table></div></section>
<section class="section" id="gaps"><div class="section-head"><div><h2>五、补埋点与上线顺序</h2><p>先让数据可解释，再打开跨端比较和告警。</p></div></div><div class="panel"><ol class="numbered"><li><strong>统一聚合层：</strong>创建 `waje_device_performance_mart`，Metabase 只连接授权聚合视图。</li><li><strong>Android/iOS：</strong>完成 Performance 质量审计、Crashlytics 字段去重和请求类别映射。</li><li><strong>H5：</strong>按既有 V3 契约接入 10 个 H5 V2 事件，并以 `measurement_state` 控制分位数。</li><li><strong>核心漏斗：</strong>Origin 认证 REGISTER → LOGIN → GAMESTART → GAMEEND；在成功语义核验前只叫“服务端事件阶段”。</li><li><strong>上线门禁：</strong>7 个稳定完整日、性能样本≥500、关键字段完整率达标后，才启用版本回归和 P95 偏离告警。</li></ol></div></section><footer class="footer"><span>仅使用企业 BigQuery 聚合数据；不包含用户、设备唯一标识、订单、支付、URL、请求体或堆栈。</span><span><a href="dashboard_v2.html">看板预览</a> · <a href="actual_baseline.json">实际基线</a> · <a href="data_contract.json">数据契约</a> · <a href="design_spec_v2.html">详细设计</a></span></footer></main></div></body></html>'''


def main() -> int:
    data = json.loads(BASELINE.read_text(encoding="utf-8"))
    dashboard = dashboard_html(data).replace("P90", "P95").replace("p90", "p95")
    report = report_html(data).replace("P90", "P95").replace("p90", "p95")
    DASHBOARD.write_text(dashboard, encoding="utf-8")
    PREVIEW.write_text(dashboard, encoding="utf-8")
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({"dashboard": str(DASHBOARD), "report": str(REPORT), "status": "ok"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
