#!/usr/bin/env python3
"""Persist aggregate-only production Metabase TC results through 2026-09-01.

The rows below are copied from one read-only query against whot_center.order_log
inside the authenticated production Metabase session. No user, order, device, or
payment-instrument detail is retained.
"""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent

DAILY = [
    ("2026-08-19", 365432437, 286598361.30),
    ("2026-08-20", 375580607, 292062567.30),
    ("2026-08-21", 362805975, 286699050.07),
    ("2026-08-22", 366259737, 292863389.54),
    ("2026-08-23", 349317796, 276578512.15),
    ("2026-08-24", 352587027, 273486465.53),
    ("2026-08-25", 357900708, 269385112.99),
    ("2026-08-26", 367368926, 291979896.26),
    ("2026-08-27", 358960800, 285378465.56),
    ("2026-08-28", 372973898, 292034388.95),
    ("2026-08-29", 366206034, 284883512.24),
    ("2026-08-30", 365253024, 271270945.74),
    ("2026-08-31", 359683761, 286212402.83),
    ("2026-09-01", 390100600, 297726062.28),
]

CHANNELS = [
    ("WajeSpecial", 890423300, 695887923.89, 916112999, 708089827.93),
    ("PAWAJEIOS", 208943550, 172054604.57, 186028409, 138418492.04),
    ("PAWAJEBETH5", 92647538, 70259505.06, 91376541, 72012283.49),
    ("PAWAJEPALM2", 74952486, 58792870.02, 82447066, 64795941.33),
    ("PAWAJEH5", 43831916, 34322487.80, 47621362, 37314758.06),
    ("PAPAWJBETCY2", 33855170, 25116860.47, 34747248, 24879225.88),
    ("PAPAWAJEH5GA", 26582119, 17655077.86, 30287339, 22564476.58),
]

DAILY_SQL = """SELECT
  DATE(FROM_UNIXTIME(time)) AS business_date,
  SUM(CASE WHEN type = 1 AND status = 3 THEN amount ELSE 0 END) / 100.0 AS success_recharge_amount,
  SUM(CASE WHEN type = 2 AND status = 103 THEN amount ELSE 0 END) / 100.0 AS success_withdraw_amount,
  SUM(CASE WHEN type = 2 AND status = 103 THEN amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN type = 1 AND status = 3 THEN amount ELSE 0 END), 0) AS tc_rate
FROM whot_center.order_log
WHERE time >= UNIX_TIMESTAMP('2026-08-19 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-09-02 00:00:00')
GROUP BY 1 ORDER BY business_date;"""

CHANNEL_SQL = """SELECT
  u.reg_channel AS channel,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_0825_0828,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_0825_0828,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / NULLIF(SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) AS tc_0825_0828,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_0829_0901,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_0829_0901,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / NULLIF(SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) AS tc_0829_0901
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00')
  AND ((o.type = 1 AND o.status = 3) OR (o.type = 2 AND o.status = 103))
GROUP BY 1
HAVING recharge_0829_0901 > 0
ORDER BY recharge_0829_0901 DESC;"""


def period(rows):
    recharge = sum(row["success_recharge_amount"] for row in rows)
    withdraw = sum(row["success_withdraw_amount"] for row in rows)
    return {"recharge": recharge, "withdraw": withdraw, "tc": withdraw / recharge if recharge else None, "days": len(rows)}


def main():
    daily = [{"date": d, "success_recharge_amount": r, "success_withdraw_amount": w, "tc": w / r} for d, r, w in DAILY]
    before = period([row for row in daily if "2026-08-25" <= row["date"] <= "2026-08-28"])
    after = period([row for row in daily if "2026-08-29" <= row["date"] <= "2026-09-01"])
    channels = []
    for name, r1, w1, r2, w2 in CHANNELS:
        channels.append({
            "channel": name,
            "recharge_0825_0828": r1,
            "withdraw_0825_0828": w1,
            "tc_0825_0828": w1 / r1,
            "recharge_0829_0901": r2,
            "withdraw_0829_0901": w2,
            "tc_0829_0901": w2 / r2,
            "tc_change_pp": (w2 / r2 - w1 / r1) * 100,
        })
    payload = {
        "status": "certified_aggregate_only",
        "source": "production Metabase / whot_center.order_log",
        "cutoff": "2026-09-01",
        "timezone": "Asia/Hong_Kong",
        "tc_definition": "success withdrawal (type=2,status=103) / success cash recharge (type=1,status=3)",
        "daily": daily,
        "period_comparison": {"before_0825_0828": before, "after_0829_0901": after, "tc_change_pp": (after["tc"] - before["tc"]) * 100},
        "top_channels": channels,
        "scope_note": "Channel split uses registration channel and is an aggregate comparison, not event-time attribution.",
    }
    (ROOT / "metabase_tc_2026_09_01.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with (ROOT / "metabase_tc_daily_2026_08_19_09_01.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(daily[0])); writer.writeheader(); writer.writerows(daily)
    with (ROOT / "metabase_tc_channels_2026_08_25_09_01.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(channels[0])); writer.writeheader(); writer.writerows(channels)
    (ROOT / "sql_01_tc_complete_day_2026_08_19_09_01.sql").write_text(DAILY_SQL + "\n", encoding="utf-8")
    (ROOT / "sql_02_tc_channel_compare_2026_08_25_09_01.sql").write_text(CHANNEL_SQL + "\n", encoding="utf-8")
    print(json.dumps(payload["period_comparison"], ensure_ascii=False))


if __name__ == "__main__":
    main()
