#!/usr/bin/env python3
"""Compute aggregate-only Phoenix Firebase cohort retention and purchase-event rate.

The script never writes user identifiers, URLs, event parameter values, order data,
or credentials. It queries only Waje's `wajenigeria` project and enforces a 5 GiB
dry-run limit per statement / 25 GiB limit for the run.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from google.auth import default as default_credentials
from google.auth.transport.requests import Request
from google.cloud import bigquery


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "wajenigeria"
DATASET_ID = "analytics_517134955"
LOCATION = "europe-west4"
CHANNEL_MARKER = "p=h5phx"
REQUESTED_START = dt.date(2026, 8, 27)
MAX_BYTES_PER_QUERY = 5 * 1024**3
MAX_BYTES_PER_RUN = 25 * 1024**3
OUT_DIR = ROOT / "analysis/phenix_firebase_retention_payment_2026_09_03"
SQL_DIR = OUT_DIR / "sql"
RESULT_PATH = OUT_DIR / "firebase_cohort_results.json"
RECEIPT_PATH = OUT_DIR / "execution_receipt.json"
HTML_PATH = ROOT / "output/html/Phenix渠道Firebase留存与付费率-2026-09-03.html"
VALIDATOR = Path("/Users/robin/.codex/skills/waje-bigquery-readonly/scripts/validate_readonly_sql.py")


def safe(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe(item) for item in value]
    if hasattr(value, "items") and not isinstance(value, (str, bytes)):
        return {str(key): safe(item) for key, item in value.items()}
    return value


def save_json(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_sql(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["python3", str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "passed" if result.returncode == 0 else "failed",
        "message": (result.stdout + result.stderr).strip(),
    }


def query_sql(start: dt.date, cutoff: dt.date) -> tuple[str, str]:
    start_s = start.isoformat()
    cutoff_s = cutoff.isoformat()
    suffix_start = start.strftime("%Y%m%d")
    suffix_cutoff = cutoff.strftime("%Y%m%d")
    cohort = f"""-- Aggregate-only Phoenix cohort retention; no identifiers or URL values are returned.
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS activity_date,
    event_name,
    user_pseudo_id,
    EXISTS (
      SELECT 1
      FROM UNNEST(event_params) AS parameter
      WHERE parameter.key = 'page_location'
        AND REGEXP_CONTAINS(
          LOWER(COALESCE(parameter.value.string_value, '')),
          r'(^|[?&])p=h5phx([&#]|$)'
        )
    ) AS h5phx_marker
  FROM `{PROJECT_ID}.{DATASET_ID}.events_*`
  WHERE REGEXP_CONTAINS(_TABLE_SUFFIX, r'^\d{{8}}$')
    AND _TABLE_SUFFIX BETWEEN '{suffix_start}' AND '{suffix_cutoff}'
    AND event_date BETWEEN '{suffix_start}' AND '{suffix_cutoff}'
    AND user_pseudo_id IS NOT NULL
    AND user_pseudo_id != ''
),
cohort AS (
  SELECT user_pseudo_id, MIN(activity_date) AS cohort_date
  FROM raw_events
  WHERE event_name = 'first_visit' AND h5phx_marker
  GROUP BY user_pseudo_id
),
active_day AS (
  SELECT DISTINCT user_pseudo_id, activity_date
  FROM raw_events
  WHERE event_name = 'session_start'
),
daily AS (
  SELECT
    cohort.cohort_date,
    COUNT(DISTINCT cohort.user_pseudo_id) AS cohort_users,
    COUNT(DISTINCT IF(active_day.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 1 DAY), cohort.user_pseudo_id, NULL)) AS day_plus_1_users,
    COUNT(DISTINCT IF(active_day.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 3 DAY), cohort.user_pseudo_id, NULL)) AS day_plus_3_users,
    COUNT(DISTINCT IF(active_day.activity_date = DATE_ADD(cohort.cohort_date, INTERVAL 7 DAY), cohort.user_pseudo_id, NULL)) AS day_plus_7_users
  FROM cohort
  LEFT JOIN active_day USING (user_pseudo_id)
  GROUP BY cohort.cohort_date
)
SELECT
  cohort_date,
  cohort_users,
  IF(DATE '{cutoff_s}' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), day_plus_1_users, NULL) AS day_plus_1_retained_users,
  IF(DATE '{cutoff_s}' >= DATE_ADD(cohort_date, INTERVAL 1 DAY), SAFE_DIVIDE(day_plus_1_users, cohort_users), NULL) AS day_plus_1_active_retention_rate,
  IF(DATE '{cutoff_s}' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), day_plus_3_users, NULL) AS day_plus_3_retained_users,
  IF(DATE '{cutoff_s}' >= DATE_ADD(cohort_date, INTERVAL 3 DAY), SAFE_DIVIDE(day_plus_3_users, cohort_users), NULL) AS day_plus_3_active_retention_rate,
  IF(DATE '{cutoff_s}' >= DATE_ADD(cohort_date, INTERVAL 7 DAY), day_plus_7_users, NULL) AS day_plus_7_retained_users,
  IF(DATE '{cutoff_s}' >= DATE_ADD(cohort_date, INTERVAL 7 DAY), SAFE_DIVIDE(day_plus_7_users, cohort_users), NULL) AS day_plus_7_active_retention_rate,
  DATE '{cutoff_s}' AS data_cutoff_date
FROM daily
WHERE cohort_users >= 10
ORDER BY cohort_date"""
    inventory = f"""-- Aggregate-only event inventory for Phoenix cohort; no identifiers or URL values are returned.
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS activity_date,
    event_name,
    user_pseudo_id,
    EXISTS (
      SELECT 1
      FROM UNNEST(event_params) AS parameter
      WHERE parameter.key = 'page_location'
        AND REGEXP_CONTAINS(
          LOWER(COALESCE(parameter.value.string_value, '')),
          r'(^|[?&])p=h5phx([&#]|$)'
        )
    ) AS h5phx_marker
  FROM `{PROJECT_ID}.{DATASET_ID}.events_*`
  WHERE REGEXP_CONTAINS(_TABLE_SUFFIX, r'^\d{{8}}$')
    AND _TABLE_SUFFIX BETWEEN '{suffix_start}' AND '{suffix_cutoff}'
    AND event_date BETWEEN '{suffix_start}' AND '{suffix_cutoff}'
    AND user_pseudo_id IS NOT NULL
    AND user_pseudo_id != ''
),
cohort AS (
  SELECT user_pseudo_id, MIN(activity_date) AS cohort_date
  FROM raw_events
  WHERE event_name = 'first_visit' AND h5phx_marker
  GROUP BY user_pseudo_id
)
SELECT
  raw_events.event_name,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(raw_events.user_pseudo_id) AS approx_cohort_subjects,
  MIN(raw_events.activity_date) AS first_observed_date,
  MAX(raw_events.activity_date) AS last_observed_date
FROM raw_events
JOIN cohort USING (user_pseudo_id)
WHERE raw_events.activity_date BETWEEN cohort.cohort_date AND DATE '{cutoff_s}'
GROUP BY raw_events.event_name
HAVING APPROX_COUNT_DISTINCT(raw_events.user_pseudo_id) >= 10
ORDER BY event_count DESC, raw_events.event_name"""
    return cohort, inventory


def payment_sql(start: dt.date, cutoff: dt.date, events: list[str]) -> str:
    suffix_start = start.strftime("%Y%m%d")
    suffix_cutoff = cutoff.strftime("%Y%m%d")
    literal_events = ", ".join("'" + event.replace("'", "\\'") + "'" for event in events)
    return f"""-- Aggregate-only Firebase purchase-event rate for Phoenix cohort.
-- Event names are exact standard GA4 purchase events discovered in the cohort inventory.
WITH raw_events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS activity_date,
    event_name,
    user_pseudo_id,
    EXISTS (
      SELECT 1
      FROM UNNEST(event_params) AS parameter
      WHERE parameter.key = 'page_location'
        AND REGEXP_CONTAINS(
          LOWER(COALESCE(parameter.value.string_value, '')),
          r'(^|[?&])p=h5phx([&#]|$)'
        )
    ) AS h5phx_marker
  FROM `{PROJECT_ID}.{DATASET_ID}.events_*`
  WHERE REGEXP_CONTAINS(_TABLE_SUFFIX, r'^\d{{8}}$')
    AND _TABLE_SUFFIX BETWEEN '{suffix_start}' AND '{suffix_cutoff}'
    AND event_date BETWEEN '{suffix_start}' AND '{suffix_cutoff}'
    AND user_pseudo_id IS NOT NULL
    AND user_pseudo_id != ''
),
cohort AS (
  SELECT user_pseudo_id, MIN(activity_date) AS cohort_date
  FROM raw_events
  WHERE event_name = 'first_visit' AND h5phx_marker
  GROUP BY user_pseudo_id
),
paid AS (
  SELECT DISTINCT cohort.user_pseudo_id
  FROM cohort
  JOIN raw_events USING (user_pseudo_id)
  WHERE raw_events.activity_date >= cohort.cohort_date
    AND raw_events.event_name IN ({literal_events})
)
SELECT
  COUNT(*) AS cohort_users,
  COUNT(paid.user_pseudo_id) AS purchase_event_users,
  SAFE_DIVIDE(COUNT(paid.user_pseudo_id), COUNT(*)) AS purchase_event_rate,
  DATE '{cutoff.isoformat()}' AS data_cutoff_date
FROM cohort
LEFT JOIN paid USING (user_pseudo_id)"""


def write_query(path: Path, sql: str) -> dict[str, Any]:
    path.write_text(sql + "\n", encoding="utf-8")
    return {
        "sql_file": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "validation": validate_sql(path),
    }


def run_query(client: bigquery.Client, sql_meta: dict[str, Any]) -> dict[str, Any]:
    result = dict(sql_meta)
    if sql_meta["validation"]["status"] != "passed":
        result["status"] = "blocked_sql_validation"
        return result
    sql_path = ROOT / sql_meta["sql_file"]
    sql = sql_path.read_text(encoding="utf-8")
    try:
        dry = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False,
                maximum_bytes_billed=MAX_BYTES_PER_QUERY,
            ),
            location=LOCATION,
        )
        bytes_processed = int(dry.total_bytes_processed or 0)
        result["dry_run_bytes"] = bytes_processed
        if bytes_processed > MAX_BYTES_PER_QUERY:
            result["status"] = "blocked_cost"
            return result
        job = client.query(
            sql,
            job_config=bigquery.QueryJobConfig(
                use_legacy_sql=False,
                use_query_cache=False,
                maximum_bytes_billed=MAX_BYTES_PER_QUERY,
            ),
            location=LOCATION,
        )
        rows = [safe(dict(row.items())) for row in job.result(timeout=240)]
        result.update({
            "status": "ok" if rows else "no_data",
            "job_id": job.job_id,
            "total_bytes_processed": int(job.total_bytes_processed or 0),
            "total_bytes_billed": int(job.total_bytes_billed or 0),
            "row_count": len(rows),
            "aggregate_rows": rows,
        })
    except Exception as exc:  # Keep the receipt informative without retaining credential details.
        result.update({"status": "query_failed", "error_type": type(exc).__name__, "error": str(exc)[:360]})
    return result


def pct(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"{float(value) * 100:.2f}%"


def number(value: Any) -> str:
    return "N/A" if value is None else f"{int(value):,}"


def table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(item)}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{item}</td>" for item in row) + "</tr>" for row in rows)
    return f"<div class=\"table-wrap\"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


def render_html(payload: dict[str, Any]) -> str:
    retention = payload.get("retention", {}).get("aggregate_rows", [])
    inventory = payload.get("event_inventory", {}).get("aggregate_rows", [])
    payment = payload.get("payment", {}).get("aggregate_rows", [])
    cutoff = payload.get("source", {}).get("data_cutoff_date", "N/A")
    first = retention[0] if retention else {}
    total_cohort = sum(int(row.get("cohort_users") or 0) for row in retention)
    def weighted(offset: str) -> tuple[int, int, str]:
        rows = [row for row in retention if row.get(f"{offset}_retained_users") is not None]
        denom = sum(int(row.get("cohort_users") or 0) for row in rows)
        numerator = sum(int(row.get(f"{offset}_retained_users") or 0) for row in rows)
        return numerator, denom, pct(numerator / denom) if denom else "N/A"
    d1_num, d1_den, d1_rate = weighted("day_plus_1")
    d3_num, d3_den, d3_rate = weighted("day_plus_3")
    d7_num, d7_den, d7_rate = weighted("day_plus_7")
    payment_row = payment[0] if payment else None
    pay_rate = pct(payment_row.get("purchase_event_rate")) if payment_row else "N/A"
    pay_users = number(payment_row.get("purchase_event_users")) if payment_row else "N/A"
    pay_event_names = ", ".join(payload.get("payment", {}).get("confirmed_event_names", [])) or "未识别到标准 purchase 事件"
    retention_rows = [[
        html.escape(str(row.get("cohort_date", ""))), number(row.get("cohort_users")),
        f"{number(row.get('day_plus_1_retained_users'))} / {pct(row.get('day_plus_1_active_retention_rate'))}",
        f"{number(row.get('day_plus_3_retained_users'))} / {pct(row.get('day_plus_3_active_retention_rate'))}",
        f"{number(row.get('day_plus_7_retained_users'))} / {pct(row.get('day_plus_7_active_retention_rate'))}",
    ] for row in retention]
    event_rows = [[
        html.escape(str(row.get("event_name", ""))), number(row.get("event_count")),
        number(row.get("approx_cohort_subjects")), html.escape(str(row.get("first_observed_date", ""))),
        html.escape(str(row.get("last_observed_date", ""))),
    ] for row in inventory]
    payment_html = (
        f"<span class=\"value\">{pay_rate}</span><p class=\"hint\">{pay_users} 名含 purchase 事件主体；事件：<code>{html.escape(pay_event_names)}</code></p>"
        if payment_row else
        "<span class=\"value na\">N/A</span><p class=\"hint\">当前 cohort 未识别到标准 GA4 purchase / in_app_purchase 事件；不以页面、表单或支付发起替代。</p>"
    )
    return f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Phenix Firebase 留存与付费率</title><style>
:root{{--navy:#102a43;--blue:#1769e0;--ink:#1e293b;--muted:#64748b;--line:#dbe5ef;--bg:#f5f8fc;--card:#fff;--warn:#b45309;--warnbg:#fff7e4;--ok:#0f766e;--shadow:0 10px 26px rgba(15,42,67,.08)}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif}}.hero{{background:linear-gradient(118deg,#0f2740,#1d5aa6);color:#fff;padding:45px 24px 49px}}.wrap,main{{max-width:1080px;margin:auto}}.eyebrow{{color:#b9d9ff;font-size:12px;font-weight:700;letter-spacing:.12em}}h1{{font-size:clamp(29px,5vw,46px);line-height:1.18;margin:8px 0 11px}}.hero p{{margin:0;color:#e0edfc}}.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}}.chip{{font-size:12px;border:1px solid rgba(255,255,255,.28);border-radius:999px;padding:4px 10px}}main{{padding:27px 24px 64px}}h2{{font-size:25px;color:var(--navy);margin:31px 0 8px}}h3{{margin:0 0 4px;font-size:16px;color:var(--navy)}}.notice{{margin:20px 0;padding:16px 18px;border:1px solid #f0cd7e;border-left:5px solid var(--warn);border-radius:13px;background:var(--warnbg)}}.notice p{{margin:3px 0 0}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:19px 0}}.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px;box-shadow:var(--shadow)}}.label{{display:block;color:var(--muted);font-size:12px}}.value{{display:block;color:var(--navy);font-size:29px;font-weight:800;line-height:1.1;margin:7px 0}}.value.na{{color:var(--warn)}}.hint{{margin:0;color:var(--muted);font-size:12px}}.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:13px;background:#fff;box-shadow:var(--shadow);margin:12px 0 17px}}table{{width:100%;border-collapse:collapse;min-width:740px}}th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:#f1f6fc;color:#334e68;font-size:12px;white-space:nowrap}}td{{font-size:13px}}tr:last-child td{{border-bottom:0}}code{{font-size:12px}}.source{{background:#edf5ff;border:1px solid #c9dcf8;border-radius:14px;padding:16px 18px}}.source ul{{margin:7px 0 0;padding-left:20px}}.footer{{margin-top:36px;padding-top:17px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}}@media(max-width:800px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}@media(max-width:560px){{.hero{{padding:34px 18px 39px}}main{{padding:21px 15px 48px}}.grid{{grid-template-columns:1fr}}}}
</style></head><body><header class=\"hero\"><div class=\"wrap\"><div class=\"eyebrow\">WAJE · PHENIX · FIREBASE EVENT EXPORT</div><h1>Phenix 渠道：Firebase 留存与付费率</h1><p>基于首访 URL 含 <code>p=h5phx</code> 的 Firebase cohort；所有结果均为聚合计算，不包含用户、URL 或支付明细。</p><div class=\"chips\"><span class=\"chip\">数据截止日：{html.escape(str(cutoff))}</span><span class=\"chip\">数据集：{DATASET_ID}</span><span class=\"chip\">渠道标记：{CHANNEL_MARKER}</span></div></div></header><main>
<div class=\"notice\"><b>解读方式：</b><p>“次日 / Day+3 / Day+7”均表示首访后的自然日偏移。只有已达到对应观察日的 cohort 才计入加权汇总；未成熟数据为 N/A，不作为 0%。</p></div>
<section><h2>核心结果</h2><div class=\"grid\"><article class=\"card\"><span class=\"label\">可用 Phoenix 首访 cohort</span><span class=\"value\">{number(total_cohort)}</span><p class=\"hint\">以各 cohort 日期求和；同一用户只计入其最早标记首访日</p></article><article class=\"card\"><span class=\"label\">次日活跃留存</span><span class=\"value\">{d1_rate}</span><p class=\"hint\">{number(d1_num)} / {number(d1_den)} 个已成熟 cohort 主体</p></article><article class=\"card\"><span class=\"label\">Day+3 活跃留存</span><span class=\"value\">{d3_rate}</span><p class=\"hint\">{number(d3_num)} / {number(d3_den)} 个已成熟 cohort 主体</p></article><article class=\"card\"><span class=\"label\">Firebase purchase 事件付费率</span>{payment_html}</article></div></section>
<section><h2>分 cohort 留存</h2><p class=\"hint\">每一格为“留存主体数 / 留存率”。Day+7 若尚无成熟 cohort，会显示 N/A。</p>{table(["首访日期","首访 cohort","次日活跃","Day+3 活跃","Day+7 活跃"], retention_rows)}</section>
<section><h2>Phoenix cohort 事件核验</h2><p class=\"hint\">仅列出至少 10 个主体的事件；这一步用于确认是否真的存在标准 GA4 purchase 成功事件。</p>{table(["事件","事件量","约覆盖主体","最早日期","最晚日期"], event_rows)}</section>
<section class=\"source\"><h3>计算边界</h3><ul><li>留存的活跃判定为 <code>session_start</code>；它反映 Firebase 行为回访，不等同于服务端登录或下注留存。</li><li>付费率仅使用标准 <code>purchase</code> / <code>in_app_purchase</code> 事件；若这些事件未进入该 Firebase 数据流，结果显示 N/A，不以支付页面或表单代替。</li><li>结果仅适用于带 <code>p=h5phx</code> 的首访 cohort，不能与其他 Firebase 数据集或 Origin 渠道数据直接相加。</li></ul></section><footer class=\"footer\">来源：Firebase Analytics BigQuery 导出 <code>{PROJECT_ID}.{DATASET_ID}.events_*</code>。SQL、查询作业回执和聚合结果位于 <code>analysis/phenix_firebase_retention_payment_2026_09_03/</code>。本页面不加载外部资源。</footer></main></body></html>"""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SQL_DIR.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "run_id": "phenix_firebase_retention_payment_2026_09_03",
        "status": "not_started",
        "project_id": PROJECT_ID,
        "dataset_id": DATASET_ID,
        "channel_marker": CHANNEL_MARKER,
        "safety": {
            "aggregate_only": True,
            "user_identifiers_returned": False,
            "urls_returned": False,
            "payment_details_returned": False,
            "credentials_saved": False,
            "remote_systems_modified": False,
        },
    }
    try:
        credentials, adc_project = default_credentials(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not credentials.valid:
            credentials.refresh(Request())
        if not credentials.valid:
            raise RuntimeError("Application default credentials are invalid")
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials, location=LOCATION)
        receipt["auth"] = {"status": "valid", "adc_project": adc_project, "credential_type": type(credentials).__name__}
    except Exception as exc:
        receipt.update({"status": "blocked_authentication", "error_type": type(exc).__name__, "error": str(exc)[:360]})
        save_json(RECEIPT_PATH, receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2

    try:
        table_dates = []
        for item in client.list_tables(f"{PROJECT_ID}.{DATASET_ID}"):
            match = re.fullmatch(r"events_(\d{8})", item.table_id)
            if match:
                table_dates.append(dt.datetime.strptime(match.group(1), "%Y%m%d").date())
        complete_dates = sorted(day for day in table_dates if day <= dt.date.today() - dt.timedelta(days=1))
    except Exception as exc:
        receipt.update({"status": "blocked_metadata", "error_type": type(exc).__name__, "error": str(exc)[:360]})
        save_json(RECEIPT_PATH, receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 2

    observed = [day for day in complete_dates if day >= REQUESTED_START]
    if not observed:
        receipt.update({"status": "no_complete_source_data", "complete_tables": []})
        save_json(RECEIPT_PATH, receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 3
    source_start, cutoff = observed[0], observed[-1]
    expected_dates = {source_start + dt.timedelta(days=index) for index in range((cutoff - source_start).days + 1)}
    missing_dates = sorted(expected_dates - set(observed))
    receipt["source"] = {
        "requested_start": REQUESTED_START.isoformat(),
        "source_start": source_start.isoformat(),
        "data_cutoff_date": cutoff.isoformat(),
        "complete_table_dates": [day.isoformat() for day in observed],
        "missing_complete_dates": [day.isoformat() for day in missing_dates],
    }
    if missing_dates:
        receipt["status"] = "blocked_source_gap"
        save_json(RECEIPT_PATH, receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 3

    retention_sql, inventory_sql = query_sql(source_start, cutoff)
    retention_meta = write_query(SQL_DIR / "01_h5phx_first_visit_cohort_retention.sql", retention_sql)
    inventory_meta = write_query(SQL_DIR / "02_h5phx_cohort_event_inventory.sql", inventory_sql)
    retention = run_query(client, retention_meta)
    inventory = run_query(client, inventory_meta)
    queries = {"retention": retention, "event_inventory": inventory}
    dry_total = sum(int(item.get("dry_run_bytes") or 0) for item in queries.values())
    if dry_total > MAX_BYTES_PER_RUN:
        receipt.update({"status": "blocked_total_cost", "queries": queries, "dry_run_total_bytes": dry_total})
        save_json(RECEIPT_PATH, receipt)
        return 3
    if retention["status"] != "ok" or inventory["status"] not in {"ok", "no_data"}:
        receipt.update({"status": "query_failed", "queries": queries, "dry_run_total_bytes": dry_total})
        save_json(RECEIPT_PATH, receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 3

    inventory_names = {str(row.get("event_name")) for row in inventory.get("aggregate_rows", [])}
    confirmed_purchase_events = [name for name in ["purchase", "in_app_purchase"] if name in inventory_names]
    payment: dict[str, Any] = {"status": "not_available", "confirmed_event_names": confirmed_purchase_events, "aggregate_rows": []}
    if confirmed_purchase_events:
        payment_meta = write_query(SQL_DIR / "03_h5phx_purchase_event_rate.sql", payment_sql(source_start, cutoff, confirmed_purchase_events))
        payment = run_query(client, payment_meta)
        payment["confirmed_event_names"] = confirmed_purchase_events
        dry_total += int(payment.get("dry_run_bytes") or 0)
        if dry_total > MAX_BYTES_PER_RUN:
            receipt.update({"status": "blocked_total_cost", "queries": {**queries, "payment": payment}, "dry_run_total_bytes": dry_total})
            save_json(RECEIPT_PATH, receipt)
            return 3
        if payment["status"] != "ok":
            receipt.update({"status": "query_failed", "queries": {**queries, "payment": payment}, "dry_run_total_bytes": dry_total})
            save_json(RECEIPT_PATH, receipt)
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
            return 3

    payload = {
        "status": "ok" if payment.get("status") == "ok" else "ok_payment_event_unavailable",
        "source": receipt["source"],
        "retention": retention,
        "event_inventory": inventory,
        "payment": payment,
        "dry_run_total_bytes": dry_total,
    }
    save_json(RESULT_PATH, payload)
    HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(render_html(payload), encoding="utf-8")
    receipt.update({
        "status": payload["status"],
        "queries": {
            "retention": {key: value for key, value in retention.items() if key != "aggregate_rows"},
            "event_inventory": {key: value for key, value in inventory.items() if key != "aggregate_rows"},
            "payment": {key: value for key, value in payment.items() if key != "aggregate_rows"},
        },
        "dry_run_total_bytes": dry_total,
        "outputs": {
            "aggregate_results": str(RESULT_PATH.relative_to(ROOT)),
            "html": str(HTML_PATH.relative_to(ROOT)),
        },
    })
    save_json(RECEIPT_PATH, receipt)
    print(json.dumps({"status": receipt["status"], "html": receipt["outputs"]["html"], "source": receipt["source"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
