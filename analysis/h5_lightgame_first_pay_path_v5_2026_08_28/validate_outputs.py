#!/usr/bin/env python3
"""Fail-closed validation for V5 aggregate outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
REQUIRED = [
    "01_new_user_first_pay_conversion.csv",
    "02_first_pay_path_groups.csv",
    "03_postpay_game_depth.csv",
    "04_repeat_pay.csv",
    "analysis_summary.json",
]
FORBIDDEN = {"gid", "user_id", "user_key", "order_id", "device_id", "round_id", "serial_num"}


def main() -> None:
    checks: list[dict] = []
    missing = [name for name in REQUIRED if not (RESULTS / name).exists()]
    checks.append({"check": "required_files", "pass": not missing, "detail": missing})
    if missing:
        (ROOT / "validation.json").write_text(json.dumps({"status": "blocked", "checks": checks}, indent=2), encoding="utf-8")
        raise SystemExit("blocked_missing_results")

    for path in sorted(RESULTS.glob("*.csv")):
        frame = pd.read_csv(path)
        lower = {column.lower() for column in frame.columns}
        leaked = sorted(lower & FORBIDDEN)
        checks.append({"check": f"no_sensitive_columns:{path.name}", "pass": not leaked, "detail": leaked})

    conversion = pd.read_csv(RESULTS / "01_new_user_first_pay_conversion.csv")
    checks.append({
        "check": "first_pay_rate_bounds",
        "pass": bool(conversion["first_pay_rate_d15"].between(0, 1).all()),
        "detail": None,
    })

    paths = pd.read_csv(RESULTS / "02_first_pay_path_groups.csv")
    shares = paths.groupby("period")["user_share"].sum()
    checks.append({
        "check": "path_share_sum",
        "pass": bool(((shares - 1).abs() <= 0.002).all()),
        "detail": shares.to_dict(),
    })
    checks.append({
        "check": "public_group_minimum",
        "pass": bool((paths["first_pay_users"] >= 30).all()),
        "detail": int(paths["first_pay_users"].min()),
    })

    depth = pd.read_csv(RESULTS / "03_postpay_game_depth.csv")
    checks.append({
        "check": "replay_rate_bounds",
        "pass": bool(depth["replay_rate"].between(0, 1).all()),
        "detail": None,
    })
    checks.append({
        "check": "replay_numerator_denominator",
        "pass": bool((depth["replay_users"] <= depth["first_pay_users"]).all()),
        "detail": None,
    })

    summary = json.loads((RESULTS / "analysis_summary.json").read_text(encoding="utf-8"))
    std = summary["standardization"]
    decomposition_error = abs(
        std["total_change_pp"]
        - std["within_channel_quality_effect_pp"]
        - std["channel_mix_effect_pp"]
    )
    checks.append({
        "check": "channel_decomposition_reconciles",
        "pass": decomposition_error <= 1e-8,
        "detail": decomposition_error,
    })

    passed = all(item["pass"] for item in checks)
    result = {"status": "passed" if passed else "failed", "checks": checks}
    (ROOT / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if not passed:
        raise SystemExit("validation_failed")


if __name__ == "__main__":
    main()

