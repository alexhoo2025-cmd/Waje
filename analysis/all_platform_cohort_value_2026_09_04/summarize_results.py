#!/usr/bin/env python3
"""Create reviewed aggregate summaries from the refreshed BigQuery result sets."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = Path(__file__).resolve().parent
RESULTS = ANALYSIS / "results"
PAYMENT = ANALYSIS / "payment_segmentation"
FIREBASE = ANALYSIS / "firebase_diagnosis"


def load(directory: Path, filename: str) -> list[dict[str, Any]]:
    data = json.loads((directory / filename).read_text(encoding="utf-8"))
    if data.get("status") not in {"ok", "no_data"}:
        raise RuntimeError(f"{filename}: {data.get('status')}")
    return data.get("aggregate_rows", [])


def weighted(rows: Iterable[dict[str, Any]], group_fields: list[str], metric_fields: list[str]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in group_fields)].append(row)
    output: list[dict[str, Any]] = []
    for key, items in sorted(groups.items()):
        value = {field: key[index] for index, field in enumerate(group_fields)}
        value["cohort_users"] = sum(int(item.get("cohort_users") or 0) for item in items)
        for metric in metric_fields:
            mature = [item for item in items if item.get(metric) is not None]
            denominator = sum(int(item.get("cohort_users") or 0) for item in mature)
            numerator = sum(float(item[metric]) * int(item.get("cohort_users") or 0) for item in mature)
            value[metric] = numerator / denominator if denominator else None
            value[f"{metric}_mature_users"] = denominator or None
        output.append(value)
    return output


def compact_payment_rows(rows: list[dict[str, Any]], period: str) -> list[dict[str, Any]]:
    return [
        {
            "period": period,
            "platform": row["platform"],
            "first_package_name": row["first_package_name"],
            "download_channel": row["download_channel"],
            "unique_paying_users": row["unique_paying_users"],
            "unique_new_registered_payers": row["unique_new_registered_payers"],
            "unique_first_payers": row["unique_first_payers"],
            "unique_old_payers_at_period_start": row.get("unique_old_payers_at_period_start"),
            "unique_old_payers_at_month_start": row.get("unique_old_payers_at_month_start"),
            "unique_repeat_payers_after_first_payment": row["unique_repeat_payers_after_first_payment"],
            "pay_amount": row["pay_amount"],
            "first_payment_amount": row["first_payment_amount"],
            "repeat_payment_amount": row["repeat_payment_amount"],
            "payer_arppu": row["payer_arppu"],
            "repeat_payer_arppu": row["repeat_payer_arppu"],
        }
        for row in rows
    ]


def h5_segment(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [
        row for row in rows
        if row["platform"] == "H5"
        and row["first_package_name"] == "com.wajegame.web"
        and row["download_channel"] == "PAWAJEBETH5"
    ]
    return matches[0] if len(matches) == 1 else None


def main() -> int:
    source_freshness = load(RESULTS, "01_source_freshness.json")
    source_lifecycle = load(RESULTS, "02_h5_natural_lifecycle_value.json")
    h5_daily = load(RESULTS, "03_h5_natural_daily_retention.json")
    platform_daily = load(RESULTS, "04_platform_daily_retention.json")
    h5_payment_daily = []
    for filename in [
        "05a_h5_natural_payment_2026_06.json",
        "05b1_h5_natural_payment_2026_07_01_15.json",
        "05b2_h5_natural_payment_2026_07_16_31.json",
        "05c1_h5_natural_payment_2026_08_01_15.json",
        "05c2_h5_natural_payment_2026_08_16_31.json",
    ]:
        h5_payment_daily.extend(load(RESULTS, filename))

    h5_metrics = [
        *(f"day_{day}_retention" for day in range(2, 15)),
        "day_30_retention", "day_60_retention", "day_90_retention",
    ]
    h5_monthly = weighted(
        [{**row, "cohort_month": row["cohort_date"][:7]} for row in h5_daily],
        ["cohort_month"],
        h5_metrics,
    )
    platform_metrics = [
        "day_2_retention", "day_3_retention", "day_7_retention", "day_14_retention",
        "day_30_retention", "day_60_retention", "day_90_retention",
    ]
    platform_monthly = weighted(
        [{**row, "cohort_month": row["cohort_date"][:7]} for row in platform_daily],
        ["cohort_month", "platform"],
        platform_metrics,
    )
    payment_metrics = [
        "day_1_payment_rate", "day_7_payment_rate", "day_14_payment_rate",
        "day_1_arpu", "day_7_arpu", "day_14_arpu",
    ]
    h5_payment_monthly = weighted(
        [{**row, "cohort_month": row["cohort_date"][:7]} for row in h5_payment_daily],
        ["cohort_month"],
        payment_metrics,
    )

    payment_monthly: list[dict[str, Any]] = []
    for filename, period in [
        ("06a_payment_segment_2026_06.json", "2026-06"),
        ("06b_payment_segment_2026_07.json", "2026-07"),
    ]:
        payment_monthly.extend(compact_payment_rows(load(PAYMENT, filename), period))
    payment_august_windows = compact_payment_rows(load(PAYMENT, "06c1_payment_segment_2026_08_01_15.json"), "2026-08-01/15")
    payment_august_windows.extend(compact_payment_rows(load(PAYMENT, "06c2_payment_segment_2026_08_16_31.json"), "2026-08-16/31"))
    payment_august_full = load(PAYMENT, "06e_h5_payment_stage_2026_08_full.json")[0]

    firebase_retention = load(FIREBASE, "07a_phenix_firebase_retention_diagnosis.json")
    firebase_inventory = load(FIREBASE, "07b_phenix_firebase_event_inventory.json")
    firebase_summary: dict[str, Any] = {"cohort_users": 0}
    for horizon, fields in {
        "day_2": ["day_2_any_event_users", "day_2_session_start_users", "day_2_page_view_users"],
        "day_4": ["day_4_any_event_users", "day_4_session_start_users", "day_4_page_view_users"],
    }.items():
        mature = [row for row in firebase_retention if row.get(fields[0]) is not None]
        denom = sum(int(row["cohort_users"]) for row in mature)
        firebase_summary[f"{horizon}_mature_cohort_users"] = denom
        for field in fields:
            users = sum(int(row.get(field) or 0) for row in mature)
            firebase_summary[field] = users
            firebase_summary[f"{field}_rate"] = users / denom if denom else None

    def single(rows: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
        return next((row for row in rows if row.get("cohort_month") == key), None)

    summary = {
        "metadata": {
            "report_data_cutoff": "2026-09-04",
            "firebase_data_cutoff": "2026-09-02",
            "business_timezone": "Africa/Lagos",
            "aggregate_only": True,
        },
        "source_freshness": source_freshness,
        "h5_lifecycle_source_monthly": source_lifecycle,
        "h5_strict_natural_retention_monthly": h5_monthly,
        "platform_retention_monthly": platform_monthly,
        "h5_strict_natural_payment_monthly": h5_payment_monthly,
        "payment_segmentation_monthly": payment_monthly,
        "payment_segmentation_august_windows": payment_august_windows,
        "payment_segmentation_august_full": payment_august_full,
        "h5_payment_segment_monthly": [
            {"period": period, "row": h5_segment([row for row in payment_monthly if row["period"] == period])}
            for period in ["2026-06", "2026-07"]
        ],
        "h5_payment_segment_august_windows": [
            {"period": period, "row": h5_segment([row for row in payment_august_windows if row["period"] == period])}
            for period in ["2026-08-01/15", "2026-08-16/31"]
        ],
        "phenix_firebase_retention_daily": firebase_retention,
        "phenix_firebase_summary": firebase_summary,
        "phenix_firebase_event_inventory": firebase_inventory,
        "important_rows": {
            "h5_lifecycle_june": single(source_lifecycle, "2026-06"),
            "h5_lifecycle_july": single(source_lifecycle, "2026-07"),
            "h5_lifecycle_august": single(source_lifecycle, "2026-08"),
            "h5_retention_june": single(h5_monthly, "2026-06"),
            "h5_retention_july": single(h5_monthly, "2026-07"),
            "h5_retention_august": single(h5_monthly, "2026-08"),
            "h5_payment_june": single(h5_payment_monthly, "2026-06"),
            "h5_payment_july": single(h5_payment_monthly, "2026-07"),
            "h5_payment_august": single(h5_payment_monthly, "2026-08"),
        },
    }
    (ANALYSIS / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "h5_retention_months": len(h5_monthly),
        "platform_retention_rows": len(platform_monthly),
        "payment_months": len(h5_payment_monthly),
        "payment_segment_rows": len(payment_monthly),
        "firebase_cohort_rows": len(firebase_retention),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
