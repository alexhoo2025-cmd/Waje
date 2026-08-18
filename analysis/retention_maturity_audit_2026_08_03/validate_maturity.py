#!/usr/bin/env python3
"""Recompute the retention aggregate using only mature cohorts from audit_data.json."""

import json
from pathlib import Path


ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "audit_data.json").read_text())
HORIZONS = ("d1", "d3", "d4", "d5", "d6", "d7")


def main() -> None:
    rows = DATA["cohort_rows"]
    expected = DATA["expected_platform_overall"]
    results = {}

    for horizon in HORIZONS:
        mature = [row for row in rows if row[f"{horizon}_users"] is not None]
        denominator = sum(row["new_users"] for row in mature)
        numerator = sum(row[f"{horizon}_users"] for row in mature)
        rate = numerator / denominator
        target = expected[horizon]
        assert denominator == target["eligible_new_users"], (horizon, denominator, target)
        assert numerator == target["retained_users"], (horizon, numerator, target)
        assert round(rate * 100, 2) == round(target["rate"] * 100, 2), (horizon, rate, target)
        results[horizon] = {
            "mature_cohort_dates": [row["cohort_date"] for row in mature],
            "eligible_new_users": denominator,
            "retained_users": numerator,
            "rate": rate,
        }

    assert sum(row["new_users"] for row in rows) == 317
    print(json.dumps({"status": "passed", "all_window_new_users": 317, "retention": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
