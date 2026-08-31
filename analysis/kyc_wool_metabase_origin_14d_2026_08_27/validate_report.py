#!/usr/bin/env python3
"""Validate the aggregate-only KYC / Origin 14-day report artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT.parents[1] / "knowledge" / "02-数据" / "Waje-KYC人脸与羊毛风险综合分析-2026-08-27.md"


def main() -> None:
    data = json.loads((ROOT / "source_snapshot.json").read_text(encoding="utf-8"))
    checks = json.loads((ROOT / "source_checks.json").read_text(encoding="utf-8"))
    assert data["period"] == "2026-08-13 至 2026-08-26"
    assert len(data["kyc_daily"]) == 14
    assert len(data["origin_daily"]) == 14
    assert checks["metabase"]["returned_rows"] == 28
    assert checks["origin"]["returned_rows"] == 14
    assert checks["origin"]["status"] == "provisional_filter_display_mismatch"
    report = (ROOT / "report.md").read_text(encoding="utf-8")
    archive = ARCHIVE.read_text(encoding="utf-8")
    assert report == archive
    for forbidden in ("用户id", "设备id", "启动IP", "邮箱", "银行卡号", "BVN号码", "NIN号码"):
        assert forbidden not in data["data"].__str__()
    for name in (
        "01_提现触发人脸认证漏斗.png",
        "02_App与H5认证质量对比.png",
        "03_端到端成功率趋势.png",
        "04_全站提充比趋势.png",
    ):
        path = ROOT / name
        assert path.exists() and path.stat().st_size > 10_000
        image = Image.open(path)
        assert image.size == (1400, 760)
    print(json.dumps({"status": "passed", "archive": str(ARCHIVE), "charts": 4}, ensure_ascii=False))


if __name__ == "__main__":
    main()
