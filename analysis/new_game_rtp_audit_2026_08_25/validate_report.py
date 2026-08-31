#!/usr/bin/env python3
"""Validate the local outputs for the Hilo/Plinko RTP observation report."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
KNOWLEDGE = WORKSPACE / "knowledge/02-数据/Waje-新上线游戏RTP与对照分析-2026-08-25.md"


def close(actual: float, expected: float, tolerance: float = 1e-9) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> None:
    data = json.loads((ROOT / "report_data.json").read_text(encoding="utf-8"))
    quality = json.loads((ROOT / "quality_checks.json").read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / "feishu_delivery_receipt.json").read_text(encoding="utf-8"))
    required_files = [ROOT / "report.md", KNOWLEDGE, ROOT / "feishu_release.xml", ROOT / "source_manifest.json", ROOT / "chart_manifest.json"]
    chart_paths = sorted((ROOT / "assets").glob("*.png"))
    errors: list[str] = []

    if quality.get("status") != "passed":
        errors.append("quality_checks_not_passed")
    if data.get("window") != {"start": "2026-08-21", "end": "2026-08-23"}:
        errors.append("unexpected_window")
    expected = {
        "Hilo": {"actual_rtp": 0.9773652664385318, "expected_rtp": 0.9649490268338781, "rtp_gap_pp": 0.01241623960465374},
        "Plinko": {"actual_rtp": 0.9703752560934683, "expected_rtp": 0.9648688549152074, "rtp_gap_pp": 0.005506401178260921},
    }
    for game, values in expected.items():
        actual = data.get("targets", {}).get(game, {})
        if actual.get("days") != 3:
            errors.append(f"{game}_day_coverage")
        for key, target_value in values.items():
            if not close(float(actual.get(key, -999)), target_value):
                errors.append(f"{game}_{key}")
    if len(chart_paths) != 4:
        errors.append("chart_count")
    for path in required_files + chart_paths:
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing_or_empty:{path.name}")
    for path in chart_paths:
        with Image.open(path) as image:
            if image.width < 1200 or image.height < 700:
                errors.append(f"chart_size:{path.name}")
    text = KNOWLEDGE.read_text(encoding="utf-8")
    for phrase in ["早期观察", "不构成最终故障鉴定", "提款总金额÷充值总金额", "2026年8月21日—8月23日"]:
        if phrase not in text:
            errors.append(f"missing_phrase:{phrase}")
    if receipt.get("readback", {}).get("status") != "passed":
        errors.append("feishu_readback_not_passed")
    result = {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "window": data["window"],
        "target_games": list(data["targets"]),
        "charts": [path.name for path in chart_paths],
        "feishu_url": receipt.get("document", {}).get("url"),
        "visual_check": receipt.get("visual_check"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
