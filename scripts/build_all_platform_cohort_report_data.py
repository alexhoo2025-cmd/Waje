#!/usr/bin/env python3
"""Build reviewed aggregate-only snapshot for the all-platform lifecycle report."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis/all_platform_cohort_value_2026_09_03"
RESULTS = ANALYSIS / "results"
SNAPSHOT = ANALYSIS / "reviewed_snapshot.json"
SUMMARY = ANALYSIS / "report_summary.json"


def load(name: str) -> dict[str, Any]:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def rate(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def weighted(rows: list[dict[str, Any]], date_field: str, group_fields: list[str], metric_fields: list[str]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        group = tuple([row[date_field][:7], *[row[field] for field in group_fields]])
        grouped[group].append(row)
    result: list[dict[str, Any]] = []
    for group, items in sorted(grouped.items()):
        output = {"cohort_month": group[0]}
        output.update({field: group[index + 1] for index, field in enumerate(group_fields)})
        output["cohort_users"] = sum(int(item.get("cohort_users") or 0) for item in items)
        for field in metric_fields:
            mature = [item for item in items if item.get(field) is not None]
            denominator = sum(int(item.get("cohort_users") or 0) for item in mature)
            numerator = sum(float(item[field]) * int(item.get("cohort_users") or 0) for item in mature)
            output[field] = rate(numerator / denominator) if denominator else None
            output[f"{field}_mature_users"] = denominator or None
        result.append(output)
    return result


def source_query(label: str, table: str, files: list[str], filters: list[str], definitions: list[dict[str, str]], caveats: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": {
            "label": label,
            "tables": [table],
            "files": [{"label": item} for item in files],
            "filters": filters,
            "metricDefinitions": definitions,
            "caveats": caveats,
        },
        "rows": rows,
    }


def main() -> int:
    platform_rows: list[dict[str, Any]] = []
    h5_rows: list[dict[str, Any]] = []
    for month in ["2026-06", "2026-07", "2026-08"]:
        platform_rows.extend(load(f"17_platform_daily_retention_{month}.json")["rows"])
        h5_rows.extend(load(f"10_h5_natural_daily_retention_{month}.json")["rows"])
    retention_metrics = ["d2_retention", "d7_retention", "d14_retention", "d30_retention", "d60_retention", "d90_retention"]
    platform_monthly = weighted(platform_rows, "cohort_date", ["platform"], retention_metrics)
    h5_monthly = weighted(h5_rows, "cohort_date", [], [
        "day_2_retention", "day_3_retention", "day_4_retention", "day_5_retention", "day_6_retention", "day_7_retention", "day_8_retention", "day_9_retention", "day_10_retention", "day_11_retention", "day_12_retention", "day_13_retention", "day_14_retention", "day_30_retention", "day_60_retention", "day_90_retention",
    ])

    ares_rows = load("08_ares_monthly_channel_lifecycle.json")["rows"]
    h5_value = [
        {
            "cohort_month": row["cohort_month"],
            "new_users": row["new_users"],
            "ltv_1": rate(row.get("source_ltv_1_per_new_user")),
            "ltv_7": rate(row.get("source_ltv_7_per_new_user")),
            "ltv_14": rate(row.get("source_ltv_14_per_new_user")),
            "ltv_30": rate(row.get("source_ltv_30_per_new_user")),
            "ltv_60": rate(row.get("source_ltv_60_per_new_user")),
            "ltv_90": rate(row.get("source_ltv_90_per_new_user")),
            "source_pay_arpu": rate(row.get("source_pay_arpu")),
            "source_pay_arppu": rate(row.get("source_pay_arppu")),
            "source_pay_user_days": row.get("pay_users_count"),
        }
        for row in ares_rows
        if row["channel"] == "PAWAJEBETH5" and row["sub_channel"] == "PAWAJEBETH501"
    ]

    payment_short_rows = load("20_h5_natural_payment_short_horizon_2026_06_07.json")["rows"] + load("20_h5_natural_payment_short_horizon_2026_08.json")["rows"]
    strict_h5_payment_rows = []
    for month in ["2026-06", "2026-07", "2026-08"]:
        month_rows = [row for row in payment_short_rows if row["cohort_date"].startswith(month)]
        strict_h5_payment = {"cohort_month": month}
        for field in ["day_1_payment_rate", "day_7_payment_rate", "day_14_payment_rate", "day_1_arpu", "day_7_arpu", "day_14_arpu"]:
            mature = [row for row in month_rows if row.get(field) is not None]
            denominator = sum(int(row.get("cohort_users") or 0) for row in mature)
            numerator = sum(float(row[field]) * int(row.get("cohort_users") or 0) for row in mature)
            strict_h5_payment[field] = rate(numerator / denominator) if denominator else None
            strict_h5_payment[f"{field}_mature_users"] = denominator or None
        strict_h5_payment["cohort_users"] = sum(int(row.get("cohort_users") or 0) for row in month_rows)
        strict_h5_payment_rows.append(strict_h5_payment)

    payments: list[dict[str, Any]] = []
    for label, filename in [
        ("2026-06", "15_monthly_unique_payment_lifecycle_2026_06.json"),
        ("2026-07", "15_monthly_unique_payment_lifecycle_2026_07.json"),
        ("2026-09-mtd", "15_monthly_unique_payment_lifecycle_2026_09_mtd.json"),
    ]:
        for row in load(filename)["rows"]:
            if row["platform"] == "H5" and row["first_package_name"] == "com.wajegame.web" and row["download_channel"] == "PAWAJEBETH5":
                payments.append({"period": label, **row})

    august_package = [
        {"period": "2026-08", **row}
        for row in load("18_august_unique_first_repeat_by_package.json")["rows"]
        if row["platform"] == "H5" and row["first_package_name"] == "com.wajegame.web"
    ]

    source_status = [
        {"asset": "Ares lifecycle aggregate", "status": "provisional", "coverage": "2026-06-01 to 2026-09-02", "note": "Supports channel-level D2-D8/D14/D30/D60 and LTV1-LTV90; D9-D13 unavailable and channel is not a trusted platform key."},
        {"asset": "H5 strict natural retention", "status": "certified_for_scope", "coverage": "2026-06 to 2026-08 cohorts; active source begins 2026-06-30", "note": "Requires Web package plus PAWAJEBETH5 across download/first channel/subchannel; account-level active return, not same-package return."},
        {"asset": "H5 strict natural payment rate", "status": "certified_for_scope", "coverage": "2026-06 to 2026-08 Day1/Day7/Day14 mature cohorts", "note": "Uses the same strict registration cohort and deduplicated order_success facts; long-horizon payment rates remain outside this short-horizon run."},
        {"asset": "Unique payment lifecycle", "status": "partial", "coverage": "2026-06, 2026-07, 2026-08 package level, 2026-09 MTD", "note": "Successful order dedup plus full-profile first-pay history; August is available by first package but strict natural channel is not included."},
        {"asset": "Firebase", "status": "supplementary", "coverage": "H5 client behavior only", "note": "Not used for payment, LTV, or server retention facts."},
    ]

    queries = {
        "platform_retention": source_query(
            "Origin user daily profile and active-version facts", "wajenigeria.origin_hfyl.user_events + realtime_edw_user_version_daily",
            ["sql/17_platform_daily_retention_template.sql"],
            ["Cohort date: 2026-06-01 to 2026-08-31", "Retention: exact natural-day active record", "Data cutoff: 2026-09-02"],
            [{"label": "Platform active retention", "definition": "The share of a first-platform registration cohort with a daily active record on the specified natural-day offset.", "formula": "retained users / cohort users"}],
            ["Daily active data begins 2026-06-30, so earlier June short-term retention is N/A.", "This is account-level Waje activity, not a same-package-only return."],
            platform_monthly,
        ),
        "h5_natural_retention": source_query(
            "Strict H5 natural registration cohort", "wajenigeria.origin_hfyl.user_events + realtime_edw_user_version_daily",
            ["sql/10_h5_natural_daily_retention.sql"],
            ["First package: com.wajegame.web", "download_channel / first_channel / first_sub_channel: PAWAJEBETH5", "Data cutoff: 2026-09-02"],
            [{"label": "H5 natural retention", "definition": "The share of strictly mapped H5 natural registrants active on each lifecycle day.", "formula": "active cohort users / H5 natural cohort users"}],
            ["The strict map intentionally excludes PAWAJEBETH5 records with other first-channel values.", "D2-D14 is unavailable before daily active coverage begins on 2026-06-30."],
            h5_monthly,
        ),
        "h5_value": source_query(
            "Ares lifecycle aggregate", "wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel",
            ["sql/08_ares_monthly_channel_lifecycle.sql"],
            ["Channel: PAWAJEBETH5", "Sub-channel: PAWAJEBETH501", "Data cutoff: 2026-09-02"],
            [{"label": "Source lifecycle value", "definition": "Ares lifecycle value summed over mature daily channel rows and divided by the source new-user count.", "formula": "sum(source LTV value) / sum(source new users)"}],
            ["This is a channel-level source value, not a strict platform-attributed LTV.", "The source does not expose D9-D13 retention."],
            h5_value,
        ),
        "h5_natural_payment_rate": source_query(
            "Strict H5 natural cohort payment lifecycle", "wajenigeria.origin_hfyl.user_xlid + view_event_pay",
            ["sql/20_h5_natural_payment_short_horizon_template.sql"],
            ["Cohorts: 2026-06 through 2026-08", "First package/channel/subchannel: strict PAWAJEBETH5 H5 map", "Success event: order_success, deduplicated by day/user/order"],
            [{"label": "Strict H5 natural payment rate", "definition": "The share of a strict H5 natural registration cohort with one or more deduplicated successful orders by the stated lifecycle day.", "formula": "distinct successful payers / strict H5 natural cohort users"}],
            ["Day14 uses only cohorts mature by the 2026-09-02 cutoff; later August cohorts remain immature.", "This is success-order payment behavior, not a financial settlement or net-revenue measure."],
            strict_h5_payment_rows,
        ),
        "payment_lifecycle": source_query(
            "Deduplicated successful orders with historical first-pay profile", "wajenigeria.origin_hfyl.view_event_pay + user_info_all",
            ["sql/15_monthly_unique_payment_lifecycle_template.sql"],
            ["Success event: order_success", "Deduplication: target day x user x order number", "Periods: 2026-06, 2026-07, 2026-09 MTD"],
            [{"label": "Unique repeat payer", "definition": "A payer with at least one successful order after their historical first-pay date within the period.", "formula": "distinct users with order date > first pay date"}],
            ["New registered payers, first payers, and repeat payers are overlapping user lenses; do not add their user counts.", "2026-08 unique old-payer result is withheld because the all-platform query exceeds the 5 GiB per-query guardrail."],
            payments,
        ),
        "august_payment_package": source_query(
            "Deduplicated August first/repeat payer by first package", "wajenigeria.origin_hfyl.view_event_pay + user_info_all",
            ["sql/18_august_unique_first_repeat_by_package.sql"],
            ["Period: 2026-08-01 to 2026-08-31", "Success event: order_success", "Breakdown: first platform and first package only"],
            [{"label": "August unique repeat payer", "definition": "A unique payer with a successful August order after historical first pay, grouped by first platform and package.", "formula": "distinct users with order date > first pay date"}],
            ["The query intentionally omits channel to remain below the 5 GiB guardrail; it cannot represent strict PAWAJEBETH5 natural users."],
            august_package,
        ),
        "source_status": source_query(
            "Source coverage and data-quality audit", "multiple approved aggregate sources", ["sql/01_source_coverage.sql", "sql/04_payment_event_integrity.sql", "sql/06_profile_and_active_coverage.sql", "sql/11_order_success_status_profile.sql"],
            ["No user or order rows retained"], [], [], source_status,
        ),
    }
    snapshot = {
        "title": "全平台用户生命周期与付费价值分析｜H5 自然新增专题",
        "status": "reviewed_partial",
        "queries": queries,
        "metadata": {"data_cutoff_date": "2026-09-02", "analysis_window": "2026-06-01 to 2026-09-02", "aggregate_only": True},
    }
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"platform_monthly_retention": platform_monthly, "h5_natural_monthly_retention": h5_monthly, "h5_natural_channel_value": h5_value, "h5_natural_strict_payment_lifecycle": strict_h5_payment_rows, "h5_natural_payment_lifecycle": payments, "august_h5_package_payment_lifecycle": august_package, "source_status": source_status}
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"snapshot": str(SNAPSHOT.relative_to(ROOT)), "query_rows": {key: len(value["rows"]) for key, value in queries.items()}}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
