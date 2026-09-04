#!/usr/bin/env python3
"""Validate that the Feishu V3.0 report and local archive match revision 754."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC = "https://ksg964l11fam.sg.larksuite.com/wiki/QYbiws4OEit03Uke92rlfzmcgWb"
LOCAL = PROJECT / "knowledge/01-产品/Waje-H5轻量化游戏新增用户行为与留存影响分析-DnDay-2026-09-01.md"
OUT = ROOT / "revision754_refresh_validation_2026_09_01.json"
ENV = os.environ.copy()
ENV["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
ENV["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"


def main() -> None:
    source = json.loads((ROOT / "origin_retention_refresh_2026_08_30.json").read_text(encoding="utf-8"))
    quality = json.loads((ROOT / "origin_retention_quality_2026_08_30.json").read_text(encoding="utf-8"))
    result = subprocess.run([CLI, "docs", "+fetch", "--doc", DOC, "--detail", "full", "--format", "json", "--as", "user"], cwd=PROJECT, env=ENV, text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(result.stderr)
    remote = json.loads(result.stdout)["data"]["document"]
    content = remote["content"]
    local = LOCAL.read_text(encoding="utf-8")
    checks = [
        ("source_revision", source["source"]["revision"] == 754),
        ("source_cutoff", source["source"]["as_of"] == "2026-08-30"),
        ("quality_gate", quality["status"] == "passed"),
        ("remote_revision", remote["revision_id"] >= 559),
        ("remote_source_cutoff", "完整至2026年8月30日" in content),
        ("remote_new_firstpay_section", "新增首充用户留存（截至8月30日）" in content),
        ("remote_h5_natural_d7", "H5自然D7 Day为<b>14.2%</b>" in content),
        ("remote_google_firstpay_d7", "H5 Google的D7 Day为<b>16.0%</b>" in content),
        ("remote_no_old_source_cutoff", "起源新增留存完整至8月29日" not in content),
        ("local_revision", "lark_revision: 559" in local),
        ("local_source_cutoff", "origin_retention_cutoff: 2026-08-30" in local),
        ("local_firstpay", "新增首充用户留存：Facebook 后续承接偏弱" in local),
        ("detail_comparison", "上线前留存 → 上线后留存（变化）" in content),
        ("phase_baseline_delta", "相对上线前基线" in content),
        ("metabase_snapshot_date", "统计时间：</b>2026年8月28日" in content),
        ("post_table_no_sample_counts", "149,876" not in content),
        ("charts", all((ROOT / "charts" / name).is_file() and (ROOT / "charts" / name).stat().st_size > 0 for name in [
            "01_起源四渠道DnDay留存对比.png",
            "02_起源上线前后DnDay留存变化.png",
            "03_起源同批注册DnDay留存曲线.png",
            "04_起源DnDay留存衰减.png",
            "05_起源轻量化节点D3Day留存.png",
            "06_新增首充用户DnDay留存_截止8月30日.png",
        ])),
    ]
    failed = [name for name, ok in checks if not ok]
    payload = {"status": "passed" if not failed else "failed", "source_revision": 754, "source_as_of": "2026-08-30", "report_revision": remote["revision_id"], "checks": [{"name": name, "ok": ok} for name, ok in checks], "failed": failed}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
