#!/usr/bin/env python3
"""Build a traceable 30-day EasyWin RTP readout from the Lark readback snapshot."""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/outputs/lifecycle_joint/2026-09-11/lark-after/values/aIE757.json"
RAW_ROOT = ROOT / "data/raw/lifecycle_joint"
START = dt.date(2026, 8, 12)
END = dt.date(2026, 9, 10)
GAME = "EasyWin"


def number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    if text.endswith("%"):
        return float(text[:-1]) / 100
    try:
        return float(text)
    except ValueError:
        return None


def iso_date(value: str) -> str:
    year, month, day = (int(part) for part in value.strip().split("/"))
    return f"{year:04d}-{month:02d}-{day:02d}"


def source_rows() -> list[dict[str, str]]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    clean_lines = [re.sub(r"^\[row=\d+\]\s*", "", line) for line in payload["annotated_csv"].splitlines()]
    return list(csv.DictReader(io.StringIO("\n".join(clean_lines))))


def daily_rows() -> list[dict[str, object]]:
    selected: dict[str, dict[str, object]] = {}
    for row in source_rows():
        if row.get("游戏", "").strip().casefold() != GAME.casefold():
            continue
        try:
            business_date = iso_date(row["日期"])
        except (KeyError, TypeError, ValueError):
            continue
        if not START.isoformat() <= business_date <= END.isoformat():
            continue
        if business_date in selected:
            raise ValueError(f"duplicate EasyWin date: {business_date}")
        bet = number(row.get("基础下注额"))
        profit = number(row.get("基础实际盈利"))
        shown_rtp = number(row.get("基础真实回报比"))
        if bet is None or profit is None or bet <= 0:
            raise ValueError(f"invalid EasyWin row: {business_date}")
        calculated_rtp = 1 - profit / bet
        if shown_rtp is None or abs(calculated_rtp - shown_rtp) > 0.000051:
            raise ValueError(f"RTP mismatch: {business_date}")
        selected[business_date] = {
            "date": business_date,
            "base_bet": bet,
            "actual_profit": profit,
            "actual_rtp": calculated_rtp,
            "status": "complete",
        }

    output = []
    cursor = START
    while cursor <= END:
        key = cursor.isoformat()
        output.append(selected.get(key, {
            "date": key,
            "base_bet": None,
            "actual_profit": None,
            "actual_rtp": None,
            "status": "missing",
        }))
        cursor += dt.timedelta(days=1)
    return output


def validate_raw_overlap(rows: list[dict[str, object]]) -> dict[str, object]:
    by_date = {str(row["date"]): row for row in rows}
    checked = 0
    mismatches = []
    for path in sorted(RAW_ROOT.glob("*/*/tables.json")):
        business_date = path.parent.name
        if not START.isoformat() <= business_date <= END.isoformat():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        headers = payload["headers"]["game"]
        index = {str(header).strip(): position for position, header in enumerate(headers)}
        source_row = next(
            (row for row in payload["rows"]["game"] if str(row[index["游戏"]]).strip().casefold() == GAME.casefold()),
            None,
        )
        if source_row is None:
            continue
        checked += 1
        daily = by_date.get(business_date)
        raw_bet = number(source_row[index["基础下注额"]])
        raw_profit = number(source_row[index["基础实际盈利"]])
        if daily is None or daily["base_bet"] is None or abs(float(daily["base_bet"]) - float(raw_bet or 0)) > 0.01 or abs(float(daily["actual_profit"]) - float(raw_profit or 0)) > 0.01:
            mismatches.append(business_date)
    return {"overlap_days_checked": checked, "mismatch_dates": mismatches, "status": "passed" if not mismatches else "failed"}


def main() -> None:
    rows = daily_rows()
    complete = [row for row in rows if row["status"] == "complete"]
    missing = [str(row["date"]) for row in rows if row["status"] != "complete"]
    total_bet = sum(float(row["base_bet"]) for row in complete)
    total_profit = sum(float(row["actual_profit"]) for row in complete)
    cumulative_rtp = 1 - total_profit / total_bet
    overlap = validate_raw_overlap(rows)
    if overlap["status"] != "passed":
        raise ValueError(f"raw overlap mismatch: {overlap['mismatch_dates']}")

    minimum = min(complete, key=lambda row: float(row["actual_rtp"]))
    maximum = max(complete, key=lambda row: float(row["actual_rtp"]))
    summary = {
        "schema_version": 1,
        "status": "partial" if missing else "ok",
        "generated_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds"),
        "game": GAME,
        "window": {"start": START.isoformat(), "end": END.isoformat(), "timezone": "Asia/Hong_Kong", "requested_days": len(rows)},
        "coverage": {"complete_days": len(complete), "missing_dates": missing},
        "metrics": {
            "total_base_bet": total_bet,
            "total_actual_profit": total_profit,
            "cumulative_actual_rtp": cumulative_rtp,
            "lowest_daily_rtp": {"date": minimum["date"], "value": minimum["actual_rtp"]},
            "highest_daily_rtp": {"date": maximum["date"], "value": maximum["actual_rtp"]},
        },
        "definition": "累计实际RTP = 1 - Σ基础实际盈利 / Σ基础下注额；不是每日RTP算术平均。",
        "unit": "沿用源表数值单位，未擅自标注币种。",
        "source": {"label": "生命周期价值飞书文档回读", "revision": 1608, "path": str(SOURCE.relative_to(ROOT))},
        "validation": {"lark_values_complete": True, "raw_overlap": overlap},
    }

    with (OUT / "easywin-daily.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "base_bet", "actual_profit", "actual_rtp", "status"])
        writer.writeheader()
        writer.writerows(rows)

    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_lines = [
        "# EasyWin 过去30日基础RTP、下注及盈利", "",
        f"窗口：{START.isoformat()}—{END.isoformat()}（香港时间）；覆盖 {len(complete)}/{len(rows)} 天；缺失：{'、'.join(missing) or '无'}。", "",
        f"累计基础下注额：{total_bet:,.2f}",
        f"累计基础实际盈利：{total_profit:,.2f}",
        f"累计实际RTP：{cumulative_rtp * 100:.2f}%", "",
        "计算：累计实际RTP = 1 - Σ基础实际盈利 / Σ基础下注额；不是每日RTP算术平均。", "",
        "| 日期 | 基础下注额 | 基础实际盈利 | 实际RTP | 状态 |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        if row["status"] != "complete":
            md_lines.append(f'| {row["date"]} | — | — | — | 缺失 |')
        else:
            md_lines.append(f'| {row["date"]} | {float(row["base_bet"]):,.2f} | {float(row["actual_profit"]):,.2f} | {float(row["actual_rtp"]) * 100:.2f}% | 完整 |')
    (OUT / "report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    chart_input = {
        "schemaVersion": 1,
        "id": "easywin-daily-rtp-30d",
        "queryId": "easywin_daily_rtp_lark_revision_1608",
        "title": "EasyWin 每日实际RTP｜2026-08-12—09-10",
        "description": "14日窗口报告中的140.68%是其子窗口累计值；本图展示30日窗口内每日波动。9月3日缺失，不补零。",
        "chart": {"type": "line", "x": "date", "y": "rtp_pct", "showXAxisLabel": True, "xLabel": "业务日期", "yLabel": "实际RTP（%）"},
        "rows": [{"date": row["date"], "rtp_pct": None if row["actual_rtp"] is None else round(float(row["actual_rtp"]) * 100, 4)} for row in rows],
        "source": {
            "label": "生命周期价值飞书文档回读 revision 1608",
            "files": [{"label": "生命周期奖池分游戏汇总", "path": str(SOURCE.relative_to(ROOT))}],
            "filters": {"game": GAME, "date_start": START.isoformat(), "date_end": END.isoformat()},
            "caveats": ["2026-09-03缺失，不补零；29个有效日与17个本地原始快照重叠值一致。", "数值单位沿用源表，未擅自标注币种。"],
        },
        "generatedAt": summary["generated_at"],
        "theme": "codex-classic",
    }
    (OUT / "chart-input.json").write_text(json.dumps(chart_input, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    chart_sources = {
        "schemaVersion": 1,
        "items": [{
            "id": "easywin-daily-rtp-trend",
            "title": "EasyWin每日实际RTP如何波动？",
            "queries": [{
                "id": "easywin-daily-rtp-lark-1608",
                "source": {
                    "label": "生命周期价值飞书文档回读",
                    "files": [{"label": "生命周期奖池分游戏汇总"}],
                    "metricDefinitions": [{"label": "每日实际RTP", "definition": "每日实际RTP按1减去基础实际盈利除以基础下注额计算。"}],
                    "filters": ["游戏：EasyWin"],
                    "caveats": ["2026-09-03缺失且未补零。"],
                    "evidenceFlow": [{"kind": "validation", "title": "重叠校验", "detail": "29个有效日中有17日可与本地原始快照交叉核对，下注额和实际盈利均一致。"}],
                },
                "reportingPeriod": "2026-08-12至2026-09-10，香港时间",
                "columns": [{"field": "date", "label": "日期"}, {"field": "actual_rtp", "label": "实际RTP"}],
                "rows": [{"date": row["date"], "actual_rtp": row["actual_rtp"]} for row in rows],
                "preview": {"kind": "partial", "note": "30个请求日期中29日有值，缺失日保留为空。", "totalRows": len(rows)},
            }],
        }],
    }
    (OUT / "chart-sources-input.json").write_text(json.dumps(chart_sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    totals_sources = {
        "schemaVersion": 1,
        "items": [{
            "id": "easywin-30d-totals",
            "title": "EasyWin过去30日窗口的累计下注、盈利和RTP是多少？",
            "queries": [{
                "id": "easywin-daily-and-total-lark-1608",
                "source": {
                    "label": "生命周期价值飞书文档回读",
                    "files": [{"label": "生命周期奖池分游戏汇总"}],
                    "metricDefinitions": [
                        {"label": "累计基础下注额", "definition": "累计基础下注额是窗口内29个有效日期的基础下注额之和。"},
                        {"label": "累计基础实际盈利", "definition": "累计基础实际盈利是窗口内29个有效日期的基础实际盈利之和；负值表示该口径下累计亏损。"},
                        {"label": "累计实际RTP", "definition": "累计实际RTP按1减去累计基础实际盈利除以累计基础下注额计算，不是每日RTP的算术平均。"},
                    ],
                    "filters": ["游戏：EasyWin"],
                    "caveats": ["2026-09-03缺失，因此这是30日窗口内29个有效日的累计值，不是完整30日值。", "数值单位沿用源表，未擅自标注币种。"],
                    "evidenceFlow": [{"kind": "validation", "title": "重叠校验", "detail": "17个日期与本地原始快照交叉核对，下注额和实际盈利无差异。"}],
                },
                "reportingPeriod": "2026-08-12至2026-09-10，香港时间",
                "columns": [
                    {"field": "date", "label": "日期"},
                    {"field": "base_bet", "label": "基础下注额"},
                    {"field": "actual_profit", "label": "基础实际盈利"},
                    {"field": "actual_rtp", "label": "实际RTP"},
                    {"field": "status", "label": "状态"},
                ],
                "rows": rows,
                "preview": {"kind": "partial", "note": "完整列出30个请求日期；缺失日数值为空。", "totalRows": len(rows)},
                "methods": [{"language": "calculation", "code": f"累计RTP = 1 - ({total_profit:.2f} / {total_bet:.2f}) = {cumulative_rtp * 100:.4f}%"}],
            }],
        }],
    }
    (OUT / "totals-sources-input.json").write_text(json.dumps(totals_sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
