#!/usr/bin/env python3
"""Validate the August monthly report artifacts without reading any row-level business data."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.figures = 0
        self.details = 0
        self.summary = ""
        self.in_summary = False
        self.external_scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.table = {"rows": []}
            self.tables.append(self.table)
        elif tag == "tr" and self.table is not None:
            self.row = []
            self.table["rows"].append(self.row)
        elif tag == "figure":
            self.figures += 1
        elif tag == "details":
            self.details += 1
        elif tag == "summary":
            self.in_summary = True
        elif tag == "script":
            self.external_scripts.append(attrs.get("src") or "inline")

    def handle_endtag(self, tag):
        if tag == "summary":
            self.in_summary = False
        elif tag == "tr":
            self.row = None

    def handle_data(self, data):
        value = " ".join(data.split())
        if not value:
            return
        if self.row is not None:
            self.row.append(value)
        if self.in_summary:
            self.summary += value


def main():
    weekly = json.loads((OUT / "weekly_overview.json").read_text())
    monthly = json.loads((OUT / "monthly_overview.json").read_text())
    detail = json.loads((OUT / "display_detail_lifecycle_3_4_50.json").read_text())
    games = json.loads((OUT / "game_summary.json").read_text())
    third_party = json.loads((OUT / "third_party_tada_pp.json").read_text())
    distribution = json.loads((OUT / "distribution_analysis.json").read_text())
    package_plan = json.loads((OUT / "package_split_plan.json").read_text())
    source = json.loads((OUT / "source_manifest.json").read_text())
    quality = json.loads((OUT / "quality_checks.json").read_text())
    tc = json.loads((OUT / "tc_daily.json").read_text())
    new_user = json.loads((OUT / "new_user_context.json").read_text())
    feishu = json.loads((OUT / "feishu_readback.json").read_text())
    html_path = ROOT / "output/html/Waje-8月全产品TC比拆解分析与审计-2026-09-03.html"
    parser = Parser()
    html_text = html_path.read_text(encoding="utf-8")
    parser.feed(html_text)
    checks = {
        "lifecycle_dates_31": len(source["dates"]) == 31 and all(r["row_count_match"] for r in source["dates"]),
        "weekly_date_partition_31": sum(r["expected_days"] for r in weekly) == 31 and sum(r["observed_days"] for r in weekly) == 31,
        "weekly_bet_reconciles_month": abs(sum(r["full_bet"] for r in weekly) - monthly["full_bet"]) < 0.01,
        "game_bet_shares_reconcile": all(row.get("bet_share") is not None for row in games) and abs(sum(row["bet_share"] for row in games) - 1.0) < 1e-9,
        "game_profit_shares_reconcile": all(row.get("profit_share") is not None for row in games) and abs(sum(row["profit_share"] for row in games) - 1.0) < 1e-9,
        "third_party_tada_pp_share_reconciles": third_party.get("data_state") == "actual_aggregate" and abs(third_party["combined_bet"] / monthly["full_bet"] - third_party["combined_share"]) < 1e-12 and abs(third_party["combined_share"] - 0.5150605599867992) < 1e-9,
        "distribution_summary_reconciles": distribution.get("data_state") == "actual_aggregate" and abs(distribution["top5_bet_share"] - sum(row["bet_share"] for row in games[:5])) < 1e-12 and abs(distribution["top5_profit_share"] - sum(row["profit_share"] for row in sorted(games, key=lambda row: row["actual_profit"], reverse=True)[:5])) < 1e-12,
        "package_split_plan_documented": package_plan.get("status") == "not_available_in_current_lifecycle_snapshot" and package_plan.get("required_platform_values") == ["Android", "H5"] and "package_name" in package_plan.get("required_dimensions", []),
        "monthly_detail_124": len(json.loads((OUT / "monthly_detail_124.json").read_text())) == 124,
        "display_detail_filtered": len(detail) == 50 and {r["lifecycle"] for r in detail} == {3, 4} and all((r["full_bet"] or 0) > 0 for r in detail),
        "tc_31_dates": len(tc["rows"]) == 31 and not tc["missing_dates"],
        "tc_overlap_passed": not tc["overlap_mismatches"],
        "no_removed_columns_unlogged": "removed_display_columns" in quality,
        "html_tables": [len(t["rows"]) - 1 for t in parser.tables] == [4, 4, 15, 31, 8, 50],
        "html_figures": parser.figures == 6,
        "html_details": parser.details == 1 and "124行" in parser.summary and "50行" in parser.summary and "12行" in html_text,
        "html_no_external_scripts": not parser.external_scripts,
        "new_user_weighted_average": all(new_user.get("weighted_average", {}).get(key) is not None for key in ("new_pay_rate", "d1_retention", "d3_retention", "d7_retention")),
        "new_user_highlighted_analysis": "总体加权平均" in html_text and "简要分析" in html_text and "context-high" in html_text and "context-low" in html_text,
        "html_game_share_analysis": "下注额占比" in html_text and "51.51%" in html_text and "TaDa" in html_text and "PP" in html_text,
        "html_distribution_recommendations": "分布汇总与推荐策略" in html_text and "后续包体拆分方案" in html_text and "盈利占比" in html_text and "主要游戏实际盈利贡献" in html_text,
        "html_signed_deviation_color_scale": "绿色系表示正偏离" in html_text and "红色系表示负偏离" in html_text and "deviation-positive" in html_text and "deviation-negative" in html_text,
        "html_tc_signed_color_scale": "绿色表示高于基线" in html_text and "红色表示低于基线" in html_text and "tc-positive" in html_text and "tc-negative" in html_text,
        "feishu_readback": feishu["status"] == "passed" and feishu["display_detail_rows"] == 50 and feishu.get("image_count") == 6 and "distribution_analysis" in feishu.get("readback_scopes", []) and "package_split_plan" in feishu.get("readback_scopes", []),
    }
    value = {"status": "passed" if all(checks.values()) else "failed", "checks": checks, "html_bytes": html_path.stat().st_size, "feishu_revision": feishu["revision_id"]}
    (OUT / "validation.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(value, ensure_ascii=False))


if __name__ == "__main__":
    main()
