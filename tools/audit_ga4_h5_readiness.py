#!/usr/bin/env python3
"""Read-only GA4 readiness audit for the Waje H5 property.

Credentials and OAuth tokens deliberately live outside the repository. This tool
only writes aggregate query results, event names, dimension metadata, and a
data-readiness assessment to the requested output directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


PROPERTY_ID = "504208609"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
AUTH_DIR = Path("/Users/robin/.config/gcloud-waje-analytics")
CLIENT_FILE = AUTH_DIR / "oauth-client.json"
TOKEN_FILE = AUTH_DIR / "ga4-readonly-token.json"

TECH_DIMENSIONS = [
    "deviceCategory",
    "browser",
    "operatingSystem",
    "operatingSystemVersion",
    "screenResolution",
    "country",
    "language",
    "sessionSourceMedium",
]

CAPABILITY_RULES = {
    "基础访问与投放归因": {"required": {"page_view", "session_start", "user_engagement"}},
    "游戏进入与加载": {"tokens": {"game_load", "game_ready", "game_start", "game_enter"}},
    "可下注与首注": {"tokens": {"bet_ready", "first_bet", "place_bet", "bet"}},
    "充值与提现行为": {"tokens": {"recharge", "charge", "withdraw", "deposit", "payment"}},
    "游戏结算": {"tokens": {"settlement", "game_end", "round_end", "payout"}},
    "前端异常与恢复": {"tokens": {"client_error", "js_error", "exception", "white_screen", "black_screen", "recovery", "retry"}},
    "Web Vitals 与页面性能": {"tokens": {"web_vital", "fcp", "lcp", "inp", "cls", "pageload", "page_load"}},
    "网络与低端机分层": {"tokens": {"network", "effective_type", "rtt", "downlink", "device_tier", "memory", "cpu"}},
    "版本、渠道与游戏分层": {"tokens": {"web_version", "release_id", "game_id", "vendor", "channel", "media_source"}},
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def token_credentials(interactive: bool) -> Credentials:
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError("未找到有效 GA4 只读凭证。请先运行 --authorize。")
        if not CLIENT_FILE.exists():
            raise RuntimeError(f"未找到专用 OAuth 客户端配置：{CLIENT_FILE}")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
        creds = flow.run_local_server(host="localhost", port=0, open_browser=True)
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(TOKEN_FILE, 0o600)
    return creds


def run_report(
    client: BetaAnalyticsDataClient,
    property_id: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str,
    end_date: str,
    limit: int = 10_000,
) -> dict[str, Any]:
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name=name) for name in dimensions],
        metrics=[Metric(name=name) for name in metrics],
        limit=limit,
        keep_empty_rows=False,
    )
    response = client.run_report(request)
    rows = []
    for row in response.rows:
        rows.append(
            {
                "dimensions": {
                    header.name: value.value
                    for header, value in zip(response.dimension_headers, row.dimension_values, strict=True)
                },
                "metrics": {
                    header.name: value.value
                    for header, value in zip(response.metric_headers, row.metric_values, strict=True)
                },
            }
        )
    return {
        "dimensions": dimensions,
        "metrics": metrics,
        "row_count": response.row_count,
        "rows": rows,
        "metadata": {
            "currency_code": response.metadata.currency_code,
            "time_zone": response.metadata.time_zone,
            "data_loss_from_other_row": response.metadata.data_loss_from_other_row,
            "subject_to_thresholding": response.metadata.subject_to_thresholding,
        },
    }


def available_names(metadata: Any) -> dict[str, list[dict[str, str]]]:
    return {
        "dimensions": [
            {"api_name": item.api_name, "ui_name": item.ui_name, "description": item.description}
            for item in metadata.dimensions
        ],
        "metrics": [
            {"api_name": item.api_name, "ui_name": item.ui_name, "description": item.description}
            for item in metadata.metrics
        ],
    }


def assess(event_rows: list[dict[str, Any]], metadata: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    event_counts: Counter[str] = Counter()
    for row in event_rows:
        event_name = row["dimensions"].get("eventName", "").lower()
        try:
            event_counts[event_name] += int(row["metrics"].get("eventCount", "0"))
        except ValueError:
            continue

    observed_events = set(event_counts)
    custom_names = {
        item["api_name"].lower()
        for collection in metadata.values()
        for item in collection
        if item["api_name"].startswith("custom") or item["api_name"].startswith("event")
    }
    capabilities = []
    for name, rule in CAPABILITY_RULES.items():
        matched = set(rule.get("required", set())) & observed_events
        tokens = rule.get("tokens", set())
        matched |= {event for event in observed_events if any(token in event for token in tokens)}
        parameter_matches = {item for item in custom_names if any(token in item for token in tokens)}
        if rule.get("required") and rule["required"].issubset(observed_events):
            status = "可直接分析"
        elif matched:
            status = "可辅助分析"
        else:
            status = "缺失需补充"
        capabilities.append(
            {
                "capability": name,
                "status": status,
                "matched_events": sorted(matched),
                "matched_custom_fields": sorted(parameter_matches),
            }
        )

    return {
        "observed_event_count": len(observed_events),
        "top_events": event_counts.most_common(50),
        "capabilities": capabilities,
        "required_technical_dimensions": TECH_DIMENSIONS,
        "interpretation_rule": "GA4 的页面、设备、来源数据不能替代认证业务数据中的充值、下注、结算与长期留存口径。",
    }


def audit(args: argparse.Namespace) -> Path:
    creds = token_credentials(interactive=False)
    client = BetaAnalyticsDataClient(credentials=creds)
    property_id = args.property_id
    metadata_response = client.get_metadata(name=f"properties/{property_id}/metadata")
    metadata = available_names(metadata_response)

    reports: dict[str, Any] = {}
    failures: list[dict[str, str]] = []
    queries = {
        "events_daily_90d": (["date", "eventName"], ["eventCount", "totalUsers"], "90daysAgo", "yesterday"),
        "events_28d": (["eventName"], ["eventCount", "totalUsers"], "28daysAgo", "yesterday"),
        "hosts_28d": (["hostName"], ["activeUsers", "sessions", "eventCount"], "28daysAgo", "yesterday"),
        "pages_28d": (["pagePath"], ["activeUsers", "screenPageViews", "eventCount"], "28daysAgo", "yesterday"),
    }
    for dimension in TECH_DIMENSIONS:
        queries[f"tech_{dimension}_28d"] = ([dimension], ["activeUsers", "sessions", "eventCount"], "28daysAgo", "yesterday")

    for key, (dimensions, metrics, start_date, end_date) in queries.items():
        try:
            reports[key] = run_report(client, property_id, dimensions, metrics, start_date, end_date)
        except Exception as exc:  # Individual unavailable dimensions must not stop the audit.
            failures.append({"query": key, "error": str(exc)})

    event_rows = reports.get("events_28d", {}).get("rows", [])
    property_timezone = reports.get("events_daily_90d", {}).get("metadata", {}).get("time_zone") or "unknown"
    payload = {
        "status": "partial" if failures else "ok",
        "generated_at": datetime.now(UTC).isoformat(),
        "property_id": property_id,
        "timezone": property_timezone,
        "privacy": "仅聚合 GA4 结果；不查询、保存或导出用户级标识、Cookie、广告标识或交易明细。",
        "metadata": metadata,
        "reports": reports,
        "assessment": assess(event_rows, metadata),
        "query_failures": failures,
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "ga4-h5-readiness.json"
    write_json(output_path, payload)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Waje H5 GA4 read-only readiness audit")
    parser.add_argument("--authorize", action="store_true", help="仅完成本机 analytics.readonly OAuth 授权")
    parser.add_argument("--audit", action="store_true", help="运行聚合级 GA4 完备性核查")
    parser.add_argument("--property-id", default=PROPERTY_ID)
    parser.add_argument(
        "--output-dir",
        default="data/outputs/ga4-h5-readiness",
        help="仅保存聚合输出的目录",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.authorize:
        token_credentials(interactive=True)
        print("GA4 只读授权完成；凭证仅保存于用户级受限目录。")
        return 0
    if args.audit:
        print(audit(args))
        return 0
    raise SystemExit("请选择 --authorize 或 --audit。")


if __name__ == "__main__":
    sys.exit(main())
