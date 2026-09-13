#!/usr/bin/env python3
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYSIS = ROOT / "tada-tc-2026-09-10-vs-prior7.json"
LEDGER = ROOT / "tada-query-ledger.json"
OUTPUT = ROOT / "tada-tc-2026-09-10-receipt.json"

analysis = json.loads(ANALYSIS.read_text())
ledger = json.loads(LEDGER.read_text())
rows = analysis["daily"]

expected_dates = [(date(2026, 9, 3) + timedelta(days=i)).isoformat() for i in range(8)]
actual_dates = [row["biz_date"] for row in rows]
assert actual_dates == expected_dates, (actual_dates, expected_dates)
assert all(row["duplicate_recharge_rows"] == 0 for row in rows)
assert all(row["duplicate_withdraw_rows"] == 0 for row in rows)

for row in rows:
    expected_tc = row["withdraw"] / row["recharge"]
    assert abs(row["tc_rate"] - expected_tc) < 1e-9

prior = rows[:7]
weighted_tc = sum(row["withdraw"] for row in prior) / sum(row["recharge"] for row in prior)
assert abs(weighted_tc - analysis["summary"]["prior7_tc_weighted"]) < 1e-9

entries = ledger["entries"]
assert len(entries) == 3
assert all(entry["status"] == "completed" for entry in entries)
assert all(entry["actual_bytes"] <= 5 * 1024**3 for entry in entries)
total_bytes = sum(entry["actual_bytes"] for entry in entries)
assert total_bytes <= 25 * 1024**3

restricted_keys = {"user_id", "xl_id", "order_no", "serial_num", "transaction_key"}
assert not any(restricted_keys.intersection(row) for row in rows)

receipt = {
    "status": "passed",
    "scope": {
        "business_timezone": "Africa/Lagos",
        "start": expected_dates[0],
        "end": expected_dates[-1],
        "comparison": "2026-09-10 versus daily average and weighted TC for 2026-09-03 through 2026-09-09",
    },
    "checks": {
        "date_coverage": True,
        "tc_formula_recomputed": True,
        "prior7_weighted_tc_recomputed": True,
        "duplicate_money_rows_zero": True,
        "aggregate_only": True,
        "each_query_under_5_gib": True,
        "audit_under_25_gib": True,
    },
    "query_jobs": [
        {
            "sql": entry["sql"],
            "job_id": entry["job_id"],
            "actual_bytes": entry["actual_bytes"],
        }
        for entry in entries
    ],
    "total_actual_bytes": total_bytes,
}
OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(receipt, ensure_ascii=False))
