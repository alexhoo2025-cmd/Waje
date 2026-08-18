#!/usr/bin/env python3
"""Independent spot checks for the newcomer lifecycle report inputs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from inspect_xlsx import parse_date_styles, read_shared_strings, read_sheet, sheet_locations  # noqa: E402
import zipfile  # noqa: E402


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def date(value):
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def workbook(path: Path):
    with zipfile.ZipFile(path) as archive:
        shared = read_shared_strings(archive)
        styles = parse_date_styles(archive)
        return {name: read_sheet(archive, location, shared, styles)[0] for name, location in sheet_locations(archive)}


def check_new_package(path: Path):
    total_new = 0.0
    d7_num = 0.0
    recent_new = 0.0
    recent_d7_num = 0.0
    implied_denominator = 0.0
    for sheet_rows in workbook(path).values():
        header = [str(cell).replace("\n", "") for cell in sheet_rows[0]]
        if "新增人数" not in header:
            continue
        index = {name: i for i, name in enumerate(header) if name}
        for row in sheet_rows[1:]:
            cohort_date = date(row[index["日期"]] if len(row) > index["日期"] else None)
            new_users = number(row[index["新增人数"]] if len(row) > index["新增人数"] else None)
            if not cohort_date or not new_users or new_users <= 0:
                continue
            total_new += new_users
            if cohort_date <= dt.date(2026, 7, 20):
                d7 = number(row[index["7日留"]] if len(row) > index["7日留"] else None)
                if d7 is not None:
                    d7_num += new_users * d7
            if dt.date(2026, 6, 23) <= cohort_date <= dt.date(2026, 7, 20):
                d7 = number(row[index["7日留"]] if len(row) > index["7日留"] else None)
                if d7 is not None:
                    recent_new += new_users
                    recent_d7_num += new_users * d7
            rate = number(row[index["新增付费率"]] if len(row) > index["新增付费率"] else None)
            people = number(row[index["新增付费人数"]] if len(row) > index["新增付费人数"] else None)
            if rate and people is not None:
                implied_denominator += people / rate
    return {
        "total_new_users": int(total_new),
        "mature_d7_retention": round(d7_num / sum_new_before_cutoff(path, dt.date(2026, 7, 20)), 6),
        "recent_mature_d7_retention": round(recent_d7_num / recent_new, 6),
        "recent_mature_new_users": int(recent_new),
        "inferred_payment_denominator_per_new_user": round(implied_denominator / total_new, 6),
    }


def sum_new_before_cutoff(path: Path, cutoff: dt.date):
    total = 0.0
    for sheet_rows in workbook(path).values():
        header = [str(cell).replace("\n", "") for cell in sheet_rows[0]]
        if "新增人数" not in header:
            continue
        index = {name: i for i, name in enumerate(header) if name}
        for row in sheet_rows[1:]:
            cohort_date = date(row[index["日期"]] if len(row) > index["日期"] else None)
            new_users = number(row[index["新增人数"]] if len(row) > index["新增人数"] else None)
            if cohort_date and new_users and new_users > 0 and cohort_date <= cutoff:
                total += new_users
    return total


def check_lifecycle(path: Path):
    rows = workbook(path)["原始数据活跃周期"]
    header = [str(cell).replace("\n", "") for cell in rows[0]]
    index = {name: i for i, name in enumerate(header) if name}
    repurchase = []
    valid = 0
    for row in rows[1:]:
        if not date(row[index["日期"]] if len(row) > index["日期"] else None):
            continue
        valid += 1
        repurchase.append(number(row[index["当日复充总金额"]] if len(row) > index["当日复充总金额"] else None) or 0)
    return {"records": valid, "repurchase_amount_total": sum(repurchase), "nonzero_repurchase_records": sum(value != 0 for value in repurchase)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    args = parser.parse_args()
    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    sql_results = {}
    for source in artifact["sources"]:
        cursor = sqlite3.connect(":memory:").execute(source["query"]["sql"])
        sql_results[source["id"]] = len(cursor.fetchall())
    checks = {
        "new_package_raw_recompute": check_new_package(args.data_dir / "新包分析2026.7.27.xlsx"),
        "lifecycle_v2_raw_recompute": check_lifecycle(args.data_dir / "新包生命周期V2 - 含联运2026.7.27.xlsx"),
        "artifact_sql_rows": sql_results,
        "expected": {
            "total_new_users": 5292449,
            "mature_d7_retention": 0.183359,
            "recent_mature_d7_retention": 0.154208,
            "recent_mature_new_users": 638111,
            "inferred_payment_denominator_per_new_user": 0.757687,
            "lifecycle_records": 812,
            "lifecycle_repurchase_amount_total": 0,
        },
    }
    actual = checks["new_package_raw_recompute"]
    lifecycle = checks["lifecycle_v2_raw_recompute"]
    expected = checks["expected"]
    passed = (
        actual["total_new_users"] == expected["total_new_users"]
        and actual["mature_d7_retention"] == expected["mature_d7_retention"]
        and actual["recent_mature_d7_retention"] == expected["recent_mature_d7_retention"]
        and actual["recent_mature_new_users"] == expected["recent_mature_new_users"]
        and actual["inferred_payment_denominator_per_new_user"] == expected["inferred_payment_denominator_per_new_user"]
        and lifecycle["records"] == expected["lifecycle_records"]
        and lifecycle["repurchase_amount_total"] == expected["lifecycle_repurchase_amount_total"]
        and lifecycle["nonzero_repurchase_records"] == 0
        and sql_results == {
            "mature_retention_query": 6,
            "channel_h7_query": 8,
            "d7_period_query": 7,
            "lifecycle_pool_query": 4,
            "quality_checks_query": 4,
        }
    )
    checks["passed"] = passed
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
