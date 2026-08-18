#!/usr/bin/env python3
"""Reproducible analysis for the supplied newcomer and lifecycle workbooks.

The output intentionally distinguishes label-backed metrics from inferred
metrics. In particular, workbook fields named "终身" and "生命周期" are not
renamed to LTV or user age without an owner-confirmed definition.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from inspect_xlsx import parse_date_styles, read_shared_strings, read_sheet, sheet_locations
import zipfile


RETENTION_FIELDS = {
    1: "次留",
    3: "3日留",
    7: "7日留",
    15: "15日留",
    30: "30日留",
    60: "60日留",
}
CORE_FIELDS = [
    "新增人数",
    "终身",
    "新增付费率",
    "新增付费人数",
    "首充付费率",
    "首充付费人数",
] + list(RETENTION_FIELDS.values())


def as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    if isinstance(value, str):
        raw = value.strip().replace(",", "")
        if not raw:
            return None
        try:
            parsed = float(raw)
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None
    return None


def as_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def compact(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def read_workbook(path: Path) -> dict[str, list[list[Any]]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings = read_shared_strings(archive)
        date_styles = parse_date_styles(archive)
        return {
            name: read_sheet(archive, location, shared_strings, date_styles)[0]
            for name, location in sheet_locations(archive)
        }


def records(rows: list[list[Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    header = [str(value).strip().replace("\n", "") for value in rows[0]]
    answer = []
    for raw_row in rows[1:]:
        normalized = raw_row + [""] * (len(header) - len(raw_row))
        answer.append({header[index]: normalized[index] for index in range(len(header)) if header[index]})
    return answer


def valid_new_rows(rows: list[list[Any]]) -> list[dict[str, Any]]:
    answer = []
    for row in records(rows):
        cohort_date = as_date(row.get("日期"))
        new_users = as_number(row.get("新增人数"))
        if cohort_date and new_users is not None and new_users > 0:
            row["_date"] = cohort_date
            row["_new_users"] = new_users
            answer.append(row)
    return answer


def weighted_metric(rows: Iterable[dict[str, Any]], field: str) -> dict[str, Any]:
    numerator = 0.0
    denominator = 0.0
    valid_cohorts = 0
    for row in rows:
        value = as_number(row.get(field))
        weight = row["_new_users"]
        if value is not None:
            numerator += value * weight
            denominator += weight
            valid_cohorts += 1
    return {
        "value": compact(safe_div(numerator, denominator)),
        "cohorts": valid_cohorts,
        "new_users": int(denominator),
    }


def payment_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    row_list = list(rows)
    new_users = sum(row["_new_users"] for row in row_list)
    summary: dict[str, Any] = {"new_users": int(new_users), "cohorts": len(row_list)}
    for prefix, rate_field, people_field in (
        ("new_payment", "新增付费率", "新增付费人数"),
        ("first_charge", "首充付费率", "首充付费人数"),
    ):
        displayed_rate = weighted_metric(row_list, rate_field)
        people_total = sum(as_number(row.get(people_field)) or 0 for row in row_list)
        inferred_denominators = []
        reconciliation_ratios = []
        for row in row_list:
            rate = as_number(row.get(rate_field))
            people = as_number(row.get(people_field))
            if rate and rate > 0 and people is not None:
                implied = people / rate
                inferred_denominators.append(implied)
                reconciliation_ratios.append(implied / row["_new_users"])
        summary[prefix] = {
            "displayed_rate_weighted_by_new_users": displayed_rate["value"],
            "reported_people": int(people_total),
            "reported_people_per_new_user": compact(safe_div(people_total, new_users)),
            "inferred_denominator_total": compact(sum(inferred_denominators), 2),
            "inferred_denominator_per_new_user": compact(safe_div(sum(inferred_denominators), new_users)),
            "median_inferred_denominator_per_new_user": compact(statistics.median(reconciliation_ratios)) if reconciliation_ratios else None,
            "rate_count_rows": len(reconciliation_ratios),
        }
    return summary


def retention_summary(rows: Iterable[dict[str, Any]], horizons: Iterable[int]) -> dict[str, Any]:
    row_list = list(rows)
    return {
        f"d{horizon}": weighted_metric(row_list, RETENTION_FIELDS[horizon])
        for horizon in horizons
    }


def lifetime_column_summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    row_list = list(rows)
    new_users = sum(row["_new_users"] for row in row_list)
    values = [as_number(row.get("终身")) for row in row_list]
    values = [value for value in values if value is not None]
    return {
        "label": "终身",
        "cohort_value_sum": compact(sum(values), 2),
        "cohort_value_per_new_user": compact(safe_div(sum(values), new_users)),
        "populated_cohorts": len(values),
        "definition_status": "unconfirmed",
    }


def period_slice(rows: list[dict[str, Any]], end_date: dt.date, days: int) -> list[dict[str, Any]]:
    start_date = end_date - dt.timedelta(days=days - 1)
    return [row for row in rows if start_date <= row["_date"] <= end_date]


def newcomer_analysis(latest: dict[str, list[list[Any]]], previous: dict[str, list[list[Any]]]) -> dict[str, Any]:
    channel_rows = {name: valid_new_rows(rows) for name, rows in latest.items() if rows and "新增人数" in records(rows)[0]}
    all_rows = [row | {"_channel": channel} for channel, rows in channel_rows.items() for row in rows]
    as_of = max(row["_date"] for row in all_rows)
    all_dates = [row["_date"] for row in all_rows]
    result: dict[str, Any] = {
        "source_file": "新包分析2026.7.27.xlsx",
        "as_of_date": as_of.isoformat(),
        "channels": {},
        "all_channels": {
            "cohorts": len(all_rows),
            "new_users": int(sum(row["_new_users"] for row in all_rows)),
            "date_start": min(all_dates).isoformat(),
            "date_end": max(all_dates).isoformat(),
            "date_count": len(set(all_dates)),
        },
        "matured": {},
        "latest_matured_periods": {},
        "channel_h7_latest_28_days": [],
        "data_quality": {},
    }
    for channel, rows in channel_rows.items():
        dates = [row["_date"] for row in rows]
        result["channels"][channel] = {
            "cohorts": len(rows),
            "new_users": int(sum(row["_new_users"] for row in rows)),
            "date_start": min(dates).isoformat(),
            "date_end": max(dates).isoformat(),
        }
    for horizon in RETENTION_FIELDS:
        cutoff = as_of - dt.timedelta(days=horizon)
        matured = [row for row in all_rows if row["_date"] <= cutoff]
        result["matured"][f"d{horizon}"] = {
            "maturity_cutoff": cutoff.isoformat(),
            "cohorts": len(matured),
            "new_users": int(sum(row["_new_users"] for row in matured)),
            "retention": retention_summary(matured, [horizon])[f"d{horizon}"],
            "payment": payment_summary(matured),
            "lifetime_column": lifetime_column_summary(matured),
        }
    for horizon in (7, 30):
        cutoff = as_of - dt.timedelta(days=horizon)
        recent = period_slice(all_rows, cutoff, 28)
        prior = period_slice(all_rows, cutoff - dt.timedelta(days=28), 28)
        result["latest_matured_periods"][f"d{horizon}"] = {
            "recent_window": {
                "start": (cutoff - dt.timedelta(days=27)).isoformat(),
                "end": cutoff.isoformat(),
                "retention": retention_summary(recent, [1, 3, horizon]),
                "payment": payment_summary(recent),
                "new_users": int(sum(row["_new_users"] for row in recent)),
            },
            "prior_window": {
                "start": (cutoff - dt.timedelta(days=55)).isoformat(),
                "end": (cutoff - dt.timedelta(days=28)).isoformat(),
                "retention": retention_summary(prior, [1, 3, horizon]),
                "payment": payment_summary(prior),
                "new_users": int(sum(row["_new_users"] for row in prior)),
            },
        }
    h7_cutoff = as_of - dt.timedelta(days=7)
    for channel, rows in channel_rows.items():
        latest_28 = period_slice(rows, h7_cutoff, 28)
        h7 = retention_summary(latest_28, [1, 3, 7])
        payment = payment_summary(latest_28)
        result["channel_h7_latest_28_days"].append(
            {
                "channel": channel,
                "cohort_start": (h7_cutoff - dt.timedelta(days=27)).isoformat(),
                "cohort_end": h7_cutoff.isoformat(),
                "cohorts": len(latest_28),
                "new_users": int(sum(row["_new_users"] for row in latest_28)),
                "d1_retention": h7["d1"]["value"],
                "d3_retention": h7["d3"]["value"],
                "d7_retention": h7["d7"]["value"],
                "new_payment_rate": payment["new_payment"]["displayed_rate_weighted_by_new_users"],
                "first_charge_rate": payment["first_charge"]["displayed_rate_weighted_by_new_users"],
                "new_payment_people_per_new_user": payment["new_payment"]["reported_people_per_new_user"],
                "first_charge_people_per_new_user": payment["first_charge"]["reported_people_per_new_user"],
            }
        )
    result["channel_h7_latest_28_days"].sort(key=lambda row: row["new_users"], reverse=True)

    duplicate_keys = Counter((channel, row["_date"]) for channel, rows in channel_rows.items() for row in rows)
    missing = {
        field: sum(1 for row in all_rows if as_number(row.get(field)) is None)
        for field in CORE_FIELDS
    }
    immature_populated = {}
    for horizon, field in RETENTION_FIELDS.items():
        immature = [row for row in all_rows if row["_date"] > as_of - dt.timedelta(days=horizon)]
        nonzero = sum(1 for row in immature if (as_number(row.get(field)) or 0) != 0)
        immature_populated[f"d{horizon}"] = {"immature_cohorts": len(immature), "nonzero_metric_rows": nonzero}
    result["data_quality"] = {
        "duplicate_channel_date_keys": sum(count - 1 for count in duplicate_keys.values() if count > 1),
        "missing_core_field_counts": missing,
        "immature_retention_field_population": immature_populated,
        "rate_denominator_check": payment_summary(all_rows),
    }

    prior_channels = {name: valid_new_rows(rows) for name, rows in previous.items() if rows and "新增人数" in records(rows)[0]}
    overlap: dict[str, Any] = {}
    comparable_fields = ["新增人数", "终身", "新增付费率", "首充付费率", "次留", "7日留", "30日留", "60日留"]
    for channel in sorted(set(channel_rows) & set(prior_channels)):
        old_by_date = {row["_date"]: row for row in prior_channels[channel]}
        new_by_date = {row["_date"]: row for row in channel_rows[channel]}
        common_dates = sorted(set(old_by_date) & set(new_by_date))
        field_changes = {}
        for field in comparable_fields:
            changed = 0
            comparable = 0
            for day in common_dates:
                before = as_number(old_by_date[day].get(field))
                after = as_number(new_by_date[day].get(field))
                if before is not None and after is not None:
                    comparable += 1
                    if abs(before - after) > 1e-9:
                        changed += 1
            field_changes[field] = {"comparable_rows": comparable, "changed_rows": changed}
        overlap[channel] = {"overlap_cohorts": len(common_dates), "field_changes": field_changes}
    overlap_totals = {}
    for field in comparable_fields:
        overlap_totals[field] = {
            "comparable_rows": sum(item["field_changes"][field]["comparable_rows"] for item in overlap.values()),
            "changed_rows": sum(item["field_changes"][field]["changed_rows"] for item in overlap.values()),
        }
    result["data_quality"]["2026_07_06_vs_2026_07_27_overlap"] = {"by_channel": overlap, "totals": overlap_totals}
    return result


def lifecycle_analysis(workbook: dict[str, list[list[Any]]]) -> dict[str, Any]:
    rows = records(workbook["原始数据活跃周期"])
    valid = []
    for row in rows:
        date = as_date(row.get("日期"))
        lifecycle = as_number(row.get("生命周期"))
        if date and lifecycle is not None:
            row["_date"] = date
            row["_lifecycle"] = int(lifecycle)
            valid.append(row)
    by_lifecycle: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in valid:
        by_lifecycle[row["_lifecycle"]].append(row)
    metric_fields = {
        "user_days": "人数",
        "recharge_amount": "当日充值总金额",
        "repurchase_amount": "当日复充总金额",
        "full_bet_amount": "完全下注额",
        "revenue_amount": "营收",
    }
    lifecycle_rows = []
    for lifecycle, segment in sorted(by_lifecycle.items()):
        sums = {key: sum(as_number(row.get(field)) or 0 for row in segment) for key, field in metric_fields.items()}
        nonzero_repurchase_rows = sum(1 for row in segment if (as_number(row.get("当日复充总金额")) or 0) > 0)
        lifecycle_rows.append(
            {
                "lifecycle": lifecycle,
                "records": len(segment),
                **{key: compact(value, 2) for key, value in sums.items()},
                "repurchase_amount_share_of_recharge": compact(safe_div(sums["repurchase_amount"], sums["recharge_amount"])),
                "nonzero_repurchase_rows": nonzero_repurchase_rows,
            }
        )
    dates = [row["_date"] for row in valid]
    unique_dates = sorted(set(dates))
    expected_days = len(unique_dates)
    coverage_ranges = []
    range_start = unique_dates[0]
    range_end = unique_dates[0]
    for current in unique_dates[1:]:
        if current == range_end + dt.timedelta(days=1):
            range_end = current
        else:
            coverage_ranges.append({"start": range_start.isoformat(), "end": range_end.isoformat(), "days": (range_end - range_start).days + 1})
            range_start = current
            range_end = current
    coverage_ranges.append({"start": range_start.isoformat(), "end": range_end.isoformat(), "days": (range_end - range_start).days + 1})
    counts_by_date = Counter(row["_date"] for row in valid)
    all_recharge = sum(as_number(row.get("当日充值总金额")) or 0 for row in valid)
    all_repurchase = sum(as_number(row.get("当日复充总金额")) or 0 for row in valid)
    return {
        "source_file": "新包生命周期V2 - 含联运2026.7.27.xlsx",
        "source_sheet": "原始数据活跃周期",
        "date_start": min(dates).isoformat(),
        "date_end": max(dates).isoformat(),
        "date_count": expected_days,
        "contiguous_date_ranges": coverage_ranges,
        "records": len(valid),
        "expected_4_lifecycle_rows_per_date": sum(1 for count in counts_by_date.values() if count == 4),
        "recharge_amount": compact(all_recharge, 2),
        "repurchase_amount": compact(all_repurchase, 2),
        "repurchase_amount_share_of_recharge": compact(safe_div(all_repurchase, all_recharge)),
        "by_lifecycle": lifecycle_rows,
        "metric_scope_caveat": "该表按日期×生命周期汇总，人数为分层人次；不能据此计算新用户 cohort 的唯一用户复购率。",
    }


def build_output(data_dir: Path) -> dict[str, Any]:
    latest = read_workbook(data_dir / "新包分析2026.7.27.xlsx")
    previous = read_workbook(data_dir / "新包分析2026.7.6.xlsx")
    lifecycle = read_workbook(data_dir / "新包生命周期V2 - 含联运2026.7.27.xlsx")
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "analysis_scope": {
            "decision": "评估新包新用户的生命周期、留存与付费表现，并识别复购分析的可用边界。",
            "timezone": "文件未标注；沿用项目默认 Asia/Hong_Kong，待源系统确认。",
            "primary_source_precedence": [
                "新包分析2026.7.27.xlsx（最新新包 cohort 导出）",
                "新包生命周期V2 - 含联运2026.7.27.xlsx（GM 生命周期奖池分层汇总）",
                "新包分析2026.7.6.xlsx（用于快照可变性核查）",
            ],
        },
        "newcomer": newcomer_analysis(latest, previous),
        "lifecycle_pool": lifecycle_analysis(lifecycle),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build_output(args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
