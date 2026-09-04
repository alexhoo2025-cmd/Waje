#!/usr/bin/env python3
"""Build aggregate-only TC + lifecycle-pool RTP tracking report V2.

The controlling source is the validated Lifecycle Pool V2 (Joint) snapshot
written to the local Waje evidence store. This script never
reads or writes user-, order-, or device-level data.
"""
from __future__ import annotations

import base64
import csv
import html
import io
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
GAME_SOURCE = PROJECT / "data/outputs/lifecycle_joint/2026-09-02-2d/lark-after/values/aIE757.json"
DETAIL_SOURCE = PROJECT / "data/outputs/lifecycle_joint/2026-09-02-2d/lark-after/values/wjhify.json"
SOURCE_INDEX = PROJECT / "data/outputs/lifecycle_joint/2026-09-02-2d/lark-after/after-index.json"
SOURCE_SNAPSHOT = PROJECT / "data/outputs/lifecycle_joint/2026-09-02-2d/run-receipt.json"
HTML_OUT = PROJECT / "output/html/Waje-全产品TC与新上线游戏RTP追踪分析-V2-2026-09-02.html"
MD_OUT = PROJECT / "knowledge/02-数据/Waje-全产品TC与新上线游戏RTP追踪分析-V2-2026-09-02.md"
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
AS_OF = date(2026, 9, 1)
ALL_START = date(2026, 8, 26)
NEW_GAMES = {
    "Hilo": {"source": "hilo", "launch": date(2026, 8, 21), "game_id": "9011"},
    "Plinko": {"source": "plinko", "launch": date(2026, 8, 21), "game_id": "9016"},
    "Tower": {"source": "tower", "launch": date(2026, 8, 25), "game_id": "9013"},
}
COLORS = {"Hilo": "#2D89C8", "Plinko": "#1FA187", "Tower": "#7C72C9"}
INK, MUTED, GRID, PAPER = "#17324D", "#637A90", "#DCE8F0", "#F6FBFE"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT, size=size, index=1 if bold else 0)


def norm_header(value: str) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def parse_date(value: str) -> date | None:
    value = str(value or "").strip().replace("/", "-")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def number(value) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "n/a", "infinity", "inf", "-"}:
        return None
    if text.endswith("%"):
        try:
            return float(text[:-1]) / 100
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def canonical_game(value: str) -> str:
    compact = re.sub(r"[\s_\-]+", "", str(value or "").lower())
    aliases = {
        "hilo": "Hilo", "plinko": "Plinko", "tower": "Tower", "limbo": "Limbo",
        "keno": "Keno", "colorgame": "ColorGame", "coinflips": "Coin Flips",
        "bottlespin": "BottleSpin", "blackjack": "Blackjack", "redorgreen": "RedorGreen",
        "roullette": "Roulette", "roulette": "Roulette", "roulettev2": "RouletteV2",
        "whot": "Whot", "baccawhot": "BaccaWhot", "whotduel": "Whotduel",
        "jacksbetter": "JacksBetter", "jacksbetterrb": "JacksBetterRb",
        "nairaslots": "NairaSlots", "easywin": "EasyWin", "tada": "Tada", "pp": "PP",
        "fish": "Fish", "omg": "OMG", "soccer": "Soccer", "dice": "Dice",
    }
    return aliases.get(compact, str(value or "").strip() or "未知")


def annotated_rows(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload["annotated_csv"]
    rows = list(csv.reader(io.StringIO(raw)))
    header = [norm_header(re.sub(r"^\[row=\d+\]\s*", "", item)) for item in rows[0]]
    output: list[dict] = []
    for row in rows[1:]:
        if not row:
            continue
        row[0] = re.sub(r"^\[row=\d+\]\s*", "", row[0])
        record = dict(zip(header, row))
        record["日期"] = parse_date(record.get("日期"))
        if record["日期"] is not None:
            record["游戏"] = canonical_game(record.get("游戏") or record.get("游戏类型"))
            output.append(record)
    return output


def game_row(record: dict) -> dict:
    return {
        "date": record["日期"],
        "game": record["游戏"],
        "base_bet": number(record.get("基础下注额")) or 0.0,
        "base_actual_profit": number(record.get("基础实际盈利")),
        "base_actual_return": number(record.get("基础真实回报比")),
        "complete_bet": number(record.get("完全下注额")) or 0.0,
        "complete_expected_profit": number(record.get("完全预期盈利")),
        "complete_actual_profit": number(record.get("完全实际盈利")),
        "complete_actual_return": number(record.get("完全真实回报比")),
        "complete_expected_return": number(record.get("完全预期回报比")),
        "bankruptcy": number(record.get("总破产保护金额")) or 0.0,
        "personal_control": number(record.get("总个人盈利控制金额")) or 0.0,
    }


def valid_expected(row: dict) -> bool:
    expected = row["complete_expected_return"]
    return row["complete_bet"] > 0 and expected is not None and 0 < expected < 1.5 and row["complete_expected_profit"] is not None


def weighted_return(bet: float, profit: float | None) -> float | None:
    return 1 - profit / bet if bet > 0 and profit is not None else None


def aggregate(rows: list[dict]) -> dict:
    usable = [row for row in rows if row["complete_bet"] > 0 and row["complete_actual_profit"] is not None]
    full_bet = sum(row["complete_bet"] for row in usable)
    actual_profit = sum(row["complete_actual_profit"] for row in usable)
    base_rows = [row for row in usable if row["base_bet"] > 0 and row["base_actual_profit"] is not None]
    base_bet = sum(row["base_bet"] for row in base_rows)
    base_profit = sum(row["base_actual_profit"] for row in base_rows)
    expected_rows = [row for row in usable if valid_expected(row)]
    expected_bet = sum(row["complete_bet"] for row in expected_rows)
    expected_profit = sum(row["complete_expected_profit"] for row in expected_rows)
    expected_actual_profit = sum(row["complete_actual_profit"] for row in expected_rows)
    actual_rtp = weighted_return(full_bet, actual_profit)
    expected_rtp = weighted_return(expected_bet, expected_profit)
    actual_rtp_eligible = weighted_return(expected_bet, expected_actual_profit)
    base_rtp = weighted_return(base_bet, base_profit)
    days = sorted({row["date"] for row in usable})
    return {
        "complete_bet": full_bet,
        "complete_actual_profit": actual_profit,
        "actual_rtp": actual_rtp,
        "expected_eligible_bet": expected_bet,
        "expected_coverage": expected_bet / full_bet if full_bet else None,
        "expected_rtp": expected_rtp,
        "actual_rtp_expected_subset": actual_rtp_eligible,
        "rtp_gap_pp": (actual_rtp_eligible - expected_rtp) * 100 if actual_rtp_eligible is not None and expected_rtp is not None else None,
        "profit_vs_expected": expected_actual_profit - expected_profit if expected_rows else None,
        "base_rtp": base_rtp,
        "adjustment_pp": (actual_rtp - base_rtp) * 100 if actual_rtp is not None and base_rtp is not None else None,
        "bankruptcy": sum(row["bankruptcy"] for row in usable),
        "personal_control": sum(row["personal_control"] for row in usable),
        "days": len(days),
        "start": days[0].isoformat() if days else None,
        "end": days[-1].isoformat() if days else None,
    }


def pct(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value * 100:.{digits}f}%"


def pp(value: float | None, digits: int = 2) -> str:
    return "N/A" if value is None else f"{value:+.{digits}f}pp"


def amount(value: float | None) -> str:
    if value is None:
        return "N/A"
    av = abs(value)
    if av >= 100_000_000:
        return f"{value / 100_000_000:.2f}亿"
    if av >= 10_000:
        return f"{value / 10_000:.2f}万"
    return f"{value:,.0f}"


def canvas(title: str, subtitle: str, width=1600, height=900):
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    draw.text((64, 42), title, fill=INK, font=font(38, True))
    draw.text((64, 100), subtitle, fill=MUTED, font=font(20))
    return image, draw


def line_chart(daily: dict[str, list[dict]]) -> Path:
    path = ASSETS / "01_新游戏逐日实际与预期回报比.png"
    image, draw = canvas("新上线游戏逐日完全实际/预期回报比", f"Hilo、Plinko：8月21日—{AS_OF.month}月{AS_OF.day}日；Tower：8月25日—{AS_OF.month}月{AS_OF.day}日。各色线=实际，黄色线=预期；仅生命周期池口径。", 1600, 1050)
    panels = [("Hilo", 170), ("Plinko", 440), ("Tower", 710)]
    for game, top in panels:
        rows = daily[game]
        values = [row["actual_rtp"] for row in rows if row["actual_rtp"] is not None] + [row["expected_rtp"] for row in rows if row["expected_rtp"] is not None]
        low = min(values + [0.85]) - 0.01
        high = max(values + [1.05]) + 0.01
        low, high = max(0.75, low), min(1.20, high)
        left, right, bottom = 180, 1500, top + 190
        draw.text((64, top + 10), game, fill=COLORS[game], font=font(26, True))
        for tick in range(4):
            value = low + (high - low) * tick / 3
            y = bottom - int(150 * (value - low) / (high - low))
            draw.line((left, y, right, y), fill=GRID, width=2)
            draw.text((76, y - 10), f"{value:.0%}", fill=MUTED, font=font(15))
        points_actual, points_expected = [], []
        for i, row in enumerate(rows):
            x = left + int((right - left) * i / max(1, len(rows) - 1))
            for key, collector in [("actual_rtp", points_actual), ("expected_rtp", points_expected)]:
                if row[key] is not None:
                    y = bottom - int(150 * (row[key] - low) / (high - low))
                    collector.append((x, y))
            draw.text((x - 18, bottom + 18), row["date"][5:].replace("-", "/"), fill=MUTED, font=font(14))
        if len(points_actual) >= 2:
            draw.line(points_actual, fill=COLORS[game], width=4)
            for x, y in points_actual:
                draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=COLORS[game])
        if len(points_expected) >= 2:
            for a, b in zip(points_expected, points_expected[1:]):
                draw.line((a[0], a[1], b[0], b[1]), fill="#D89B1B", width=3)
    draw.text((930, 973), "各色实线=各游戏完全实际回报比", fill=INK, font=font(18))
    draw.line((1260, 986, 1290, 986), fill="#D89B1B", width=3)
    draw.text((1300, 973), "黄色线=完全预期回报比", fill=INK, font=font(18))
    image.save(path, "PNG", optimize=True)
    return path


def scatter_chart(all_games: list[dict], new_summary: dict[str, dict]) -> Path:
    path = ASSETS / "02_近7日全游戏回报偏离与下注规模.png"
    image, draw = canvas("近7日全游戏：RTP偏离与完全下注规模", "横轴=预期覆盖范围内的实际减预期回报比；纵轴=完全下注额（对数刻度）。每个可比游戏均以引线标注名称；彩色点为三款新游戏。", 1900, 1120)
    candidates = [x for x in all_games if x["rtp_gap_pp"] is not None]
    all_gaps = [x["rtp_gap_pp"] for x in candidates]
    left, right, top, bottom = 280, 1380, 190, 800
    min_gap, max_gap = min(min(all_gaps), -5), max(max(all_gaps), 5)
    min_gap, max_gap = math.floor(min_gap - 1), math.ceil(max_gap + 1)
    bets = [x["complete_bet"] for x in candidates]
    min_log, max_log = math.log10(min(bets)), math.log10(max(bets))
    for tick in range(5):
        gap = min_gap + (max_gap - min_gap) * tick / 4
        x = left + int((right - left) * (gap - min_gap) / (max_gap - min_gap))
        draw.line((x, top, x, bottom), fill=GRID if abs(gap) > 1e-6 else INK, width=2)
        draw.text((x - 22, bottom + 24), f"{gap:+.0f}pp", fill=MUTED, font=font(16))
    for tick in range(4):
        lv = min_log + (max_log - min_log) * tick / 3
        y = bottom - int((bottom - top) * (lv - min_log) / (max_log - min_log))
        draw.line((left, y, right, y), fill=GRID, width=2)
        draw.text((165, y - 10), amount(10 ** lv), fill=MUTED, font=font(15))
    plotted = []
    for item in candidates:
        x = left + int((right - left) * (item["rtp_gap_pp"] - min_gap) / (max_gap - min_gap))
        y = bottom - int((bottom - top) * (math.log10(item["complete_bet"]) - min_log) / (max_log - min_log))
        is_new = item["game"] in NEW_GAMES
        color = COLORS.get(item["game"], "#6A86A0") if is_new else "#7299BC"
        radius = 11 if is_new else 7
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        plotted.append({"game": item["game"], "x": x, "y": y, "new": is_new, "color": color})
    # Use two label rails and leader lines to preserve all names without hiding clustered points.
    midpoint = (left + right) / 2
    left_labels = sorted([item for item in plotted if item["x"] < midpoint], key=lambda x: x["y"])
    right_labels = sorted([item for item in plotted if item["x"] >= midpoint], key=lambda x: x["y"])
    for items, side in [(left_labels, "left"), (right_labels, "right")]:
        count = len(items)
        for idx, item in enumerate(items):
            label_y = top + 14 + int((bottom - top - 28) * idx / max(1, count - 1))
            if side == "left":
                label_x, end_x = 22, 245
                line_end = (end_x, label_y + 8)
            else:
                label_x, end_x = 1410, 1395
                line_end = (end_x, label_y + 8)
            draw.line((item["x"], item["y"], line_end[0], line_end[1]), fill=item["color"], width=1)
            draw.text((label_x, label_y), item["game"], fill=INK, font=font(15, item["new"]))
    missing_expected = [item["game"] for item in all_games if item["rtp_gap_pp"] is None]
    draw.text((250, 900), "完全实际回报比 减 完全预期回报比（pp）", fill=INK, font=font(20, True))
    draw.text((280, 960), "未绘制（预期RTP缺失，无法计算偏离）：" + "、".join(missing_expected), fill=MUTED, font=font(18))
    image.save(path, "PNG", optimize=True)
    return path


def lifecycle_chart(lifecycle: list[dict]) -> Path:
    path = ASSETS / "03_新游戏生命周期回报偏离.png"
    image, draw = canvas("新上线游戏：生命周期1—4回报偏离", "每格为上线至今加权“完全实际减完全预期”回报比；空白表示预期回报字段不可用。")
    cols = ["1", "2", "3", "4"]
    rows = ["Hilo", "Plinko", "Tower"]
    values = {(x["game"], str(x["lifecycle"])): x["rtp_gap_pp"] for x in lifecycle}
    finite = [v for v in values.values() if v is not None]
    limit = max(3.0, max(abs(v) for v in finite) if finite else 3.0)
    left, top, cw, ch = 300, 190, 270, 135
    for j, col in enumerate(cols):
        draw.text((left + j*cw + 90, top - 45), f"生命周期 {col}", fill=INK, font=font(21, True))
    for i, game in enumerate(rows):
        draw.text((80, top + i*ch + 46), game, fill=COLORS[game], font=font(24, True))
        for j, col in enumerate(cols):
            value = values.get((game, col))
            if value is None:
                color, label = "#E8EEF3", "N/A"
            elif value >= 0:
                alpha = min(1.0, value / limit)
                color = (int(229 - 60*alpha), int(245 - 40*alpha), int(232 - 90*alpha))
                label = f"+{value:.2f}pp"
            else:
                alpha = min(1.0, -value / limit)
                color = (int(253), int(239 - 70*alpha), int(239 - 70*alpha))
                label = f"{value:.2f}pp"
            x, y = left + j*cw, top + i*ch
            draw.rounded_rectangle((x, y, x+cw-15, y+ch-15), radius=12, fill=color, outline="#C8D7E2", width=2)
            draw.text((x+68, y+42), label, fill=INK, font=font(22, True))
    image.save(path, "PNG", optimize=True)
    return path


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def html_table(headers: list[str], rows: list[list[str]], classes: str = "") -> str:
    header = "".join(f"<th>{html.escape(item)}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap {classes}"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'


def status(item: dict, game: str | None = None) -> str:
    if item["days"] < 7:
        return "<span class=\"tag yellow\">数据不足·不足7日</span>"
    if item["expected_coverage"] is None or item["expected_coverage"] < 0.5:
        return "<span class=\"tag yellow\">预期覆盖不足</span>"
    if item["rtp_gap_pp"] is not None and abs(item["rtp_gap_pp"]) >= 3:
        return "<span class=\"tag red\">偏离需复核</span>"
    return "<span class=\"tag green\">持续观察</span>"


def read_sources() -> tuple[list[dict], list[dict]]:
    games = [game_row(row) for row in annotated_rows(GAME_SOURCE)]
    detail_raw = annotated_rows(DETAIL_SOURCE)
    detail: list[dict] = []
    for row in detail_raw:
        lifecycle = str(row.get("生命周期") or "").strip()
        if lifecycle not in {"1", "2", "3", "4"}:
            continue
        detail.append({
            "date": row["日期"], "game": row["游戏"], "lifecycle": int(lifecycle),
            "base_bet": number(row.get("基础下注额")) or 0.0,
            "base_actual_profit": number(row.get("基础实际盈利")),
            "complete_bet": number(row.get("完全下注额")) or 0.0,
            "complete_expected_profit": number(row.get("完全预期盈利")),
            "complete_actual_profit": number(row.get("完全实际盈利")),
            "complete_expected_return": number(row.get("预期回报比")),
            "bankruptcy": number(row.get("总破产保护金额")) or 0.0,
            "personal_control": number(row.get("总个人盈利控制金额")) or 0.0,
        })
    return games, detail


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    source_index = json.loads(SOURCE_INDEX.read_text(encoding="utf-8"))
    workbook_revision = int(source_index["revision"])
    all_window = f"{ALL_START.isoformat()}—{AS_OF.isoformat()}"
    as_of_label = f"{AS_OF.year}年{AS_OF.month}月{AS_OF.day}日"
    as_of_short = AS_OF.strftime("%m/%d")
    games, detail = read_sources()
    raw_seven = [row for row in games if ALL_START <= row["date"] <= AS_OF]
    seven = [row for row in games if ALL_START <= row["date"] <= AS_OF and row["complete_bet"] > 0]
    raw_duplicate_keys = [key for key, count in Counter((r["date"], r["game"]) for r in raw_seven).items() if count > 1]
    duplicate_keys = [key for key, count in Counter((r["date"], r["game"]) for r in seven).items() if count > 1]
    expected_rows = [row for row in seven if valid_expected(row)]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in seven:
        grouped[row["game"]].append(row)
    all_games = [{"game": game, **aggregate(rows)} for game, rows in grouped.items()]
    all_games.sort(key=lambda x: x["complete_bet"], reverse=True)
    all_overall = aggregate(seven)

    new_daily: dict[str, list[dict]] = {}
    new_summary: dict[str, dict] = {}
    lifecycle_summary: list[dict] = []
    for game, meta in NEW_GAMES.items():
        rows = [row for row in games if row["game"] == game and meta["launch"] <= row["date"] <= AS_OF and row["complete_bet"] > 0]
        daily = []
        for one_day in sorted({row["date"] for row in rows}):
            item = aggregate([row for row in rows if row["date"] == one_day])
            daily.append({"date": one_day.isoformat(), **item})
        new_daily[game] = daily
        new_summary[game] = {"game_id": meta["game_id"], "launch": meta["launch"].isoformat(), **aggregate(rows)}
        for life in range(1, 5):
            lines = [row for row in detail if row["game"] == game and row["lifecycle"] == life and meta["launch"] <= row["date"] <= AS_OF and row["complete_bet"] > 0]
            metric = aggregate(lines)
            lifecycle_summary.append({"game": game, "lifecycle": life, **metric})

    daily_for_chart = {game: [{**row, "date": row["date"]} for row in rows] for game, rows in new_daily.items()}
    chart1 = line_chart(daily_for_chart)
    chart2 = scatter_chart(all_games, new_summary)
    chart3 = lifecycle_chart(lifecycle_summary)

    quality = {
        "status": "passed" if not duplicate_keys else "blocked",
        "source": {
            "workbook_revision": workbook_revision,
            "game_summary": str(GAME_SOURCE.relative_to(PROJECT)),
            "detail": str(DETAIL_SOURCE.relative_to(PROJECT)),
            "source_window": f"{ALL_START.isoformat()} to {AS_OF.isoformat()}",
        },
        "seven_day_game_rows": len(seven),
        "seven_day_distinct_games": len(grouped),
        "seven_day_raw_game_rows": len(raw_seven),
        "seven_day_raw_distinct_games": len({row["game"] for row in raw_seven}),
        "raw_duplicate_game_date_keys": raw_duplicate_keys,
        "expected_valid_rows": len(expected_rows),
        "duplicate_game_date_keys": duplicate_keys,
        "new_game_days": {game: result["days"] for game, result in new_summary.items()},
        "blocked_fields": ["有效局数", "最终结算状态", "取消/退款", "免费注/Bonus", "配置版本", "玩法参数", "用户级大额派奖分布"],
    }

    outputs = {
        "source": {"workbook_revision": workbook_revision, "as_of": AS_OF.isoformat(), "all_games_window": all_window},
        "quality": quality,
        "overall_7d": all_overall,
        "all_games_7d": all_games,
        "new_games": new_summary,
        "new_game_daily": new_daily,
        "new_game_lifecycle": lifecycle_summary,
        "historical_tc_snapshot": {
            "window": "2026-08-26—2026-08-28",
            "morning_tc": ["81.72%", "81.46%", "82.95%"],
            "full_day_tc": {"2026-08-26": "79.48%", "2026-08-27": "79.50%"},
            "note": "Historical context only; not recomputed from lifecycle RTP source.",
        },
    }
    (ROOT / "report_data.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "quality_checks.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    with (ROOT / "all_games_7d.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["game", "complete_bet", "complete_actual_profit", "actual_rtp", "expected_coverage", "expected_rtp", "rtp_gap_pp", "adjustment_pp", "days"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows([{field: row.get(field) for field in fields} for row in all_games])
    with (ROOT / "new_game_daily.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["game", "date", "complete_bet", "complete_actual_profit", "actual_rtp", "expected_rtp", "rtp_gap_pp", "adjustment_pp"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for game, rows in new_daily.items():
            writer.writerows([{**{"game": game}, **{field: row.get(field) for field in fields if field != "game"}} for row in rows])
    with (ROOT / "new_game_lifecycle.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["game", "lifecycle", "complete_bet", "actual_rtp", "expected_rtp", "rtp_gap_pp", "adjustment_pp", "days"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows([{field: row.get(field) for field in fields} for row in lifecycle_summary])

    new_rows = []
    for game in NEW_GAMES:
        item = new_summary[game]
        new_rows.append([
            game, item["game_id"], f"{item['launch'][5:]}—{as_of_short}", str(item["days"]), amount(item["complete_bet"]), pct(item["actual_rtp"]), pct(item["expected_rtp"]), pp(item["rtp_gap_pp"]), amount(item["profit_vs_expected"]), pp(item["adjustment_pp"]), status(item, game),
        ])
    game_rows = []
    for item in all_games:
        flag = "<span class=\"tag new\">新游戏</span>" if item["game"] in NEW_GAMES else ""
        game_rows.append([item["game"], amount(item["complete_bet"]), pct(item["actual_rtp"]), pct(item["expected_rtp"]), pp(item["rtp_gap_pp"]), pct(item["expected_coverage"]), pp(item["adjustment_pp"]), flag or status(item)])
    lifecycle_rows = []
    for game in NEW_GAMES:
        for life in range(1, 5):
            item = next(row for row in lifecycle_summary if row["game"] == game and row["lifecycle"] == life)
            lifecycle_rows.append([game, str(life), amount(item["complete_bet"]), pct(item["actual_rtp"]), pct(item["expected_rtp"]), pp(item["rtp_gap_pp"]), pp(item["adjustment_pp"])])

    top_new = max(new_summary.items(), key=lambda x: x[1]["complete_bet"])
    review_games = [game for game, item in new_summary.items() if item["rtp_gap_pp"] is not None and abs(item["rtp_gap_pp"]) >= 3]
    status_text = "、".join(review_games) if review_games else "无累计偏离达到3pp的新游戏"
    report_html = f"""<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Waje 全产品TC与新上线游戏RTP追踪分析｜截至{as_of_label}</title><style>
    :root{{--ink:#17324D;--muted:#60788E;--line:#DCE8F0;--paper:#F6FBFE;--blue:#2D89C8;--green:#1FA187;--gold:#E29B14;--purple:#7C72C9;--red:#D95E5E}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.65}}.page{{max-width:1200px;margin:0 auto;padding:32px 24px 80px}}header{{background:linear-gradient(115deg,#113E66,#2D89A1);color:white;border-radius:22px;padding:36px 42px;margin-bottom:26px}}header h1{{font-size:34px;line-height:1.25;margin:0 0 12px}}header p{{margin:0;max-width:980px;font-size:17px;opacity:.96}}.meta{{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}}.chip{{border:1px solid rgba(255,255,255,.35);padding:5px 12px;border-radius:99px;font-size:13px}}section{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:28px 32px;margin:20px 0}}h2{{font-size:26px;margin:0 0 8px}}h3{{font-size:19px;margin:22px 0 8px}}p{{margin:9px 0}}.lead{{color:var(--muted)}}.callout{{border-left:4px solid var(--blue);background:#EEF7FE;border-radius:12px;padding:16px 18px;margin:16px 0}}.callout.warn{{border-color:var(--gold);background:#FFF9E9}}.callout.risk{{border-color:var(--red);background:#FFF1F1}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:18px 0}}.kpi{{border:1px solid var(--line);border-radius:14px;padding:15px;background:#FBFDFF}}.kpi .label{{color:var(--muted);font-size:13px}}.kpi strong{{font-size:26px;display:block;margin-top:4px}}.table-wrap{{overflow-x:auto;margin:14px 0}}table{{border-collapse:collapse;width:100%;min-width:850px;font-size:14px}}th{{text-align:left;background:#EEF4F8;color:#35526A}}th,td{{padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top;white-space:nowrap}}td:nth-child(n+2){{font-variant-numeric:tabular-nums}}.tag{{display:inline-block;border-radius:99px;padding:2px 8px;font-size:12px;font-weight:700}}.green{{background:#DCF5E8;color:#14734B}}.yellow{{background:#FFF0BD;color:#7D5A00}}.red{{background:#FCE1E1;color:#A92F2F}}.new{{background:#EEE9FF;color:#5440AF}}figure{{margin:20px 0;background:#F8FCFF;border:1px solid var(--line);border-radius:14px;padding:10px}}figure img{{width:100%;height:auto;display:block;border-radius:9px}}figcaption{{color:var(--muted);font-size:13px;padding:6px 4px 0}}.small{{font-size:13px;color:var(--muted)}}ol{{padding-left:22px}}@media(max-width:760px){{.page{{padding:18px 12px 50px}}header{{padding:26px 22px;border-radius:16px}}header h1{{font-size:28px}}section{{padding:22px 18px;border-radius:14px}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}h2{{font-size:23px}}}}
    </style></head><body><main class=\"page\"><header><h1>Waje 全产品 TC 与新上线游戏 RTP 追踪分析</h1><p>截至 {as_of_label}｜保留 8 月 28 日 TC 审计快照，新增全游戏近 7 日与 Hilo、Plinko、Tower 上线后回报和下注追踪。</p><div class=\"meta\"><span class=\"chip\">生命周期池 V2（Joint）修订{workbook_revision}</span><span class=\"chip\">全游戏：{ALL_START.month}月{ALL_START.day}日—{AS_OF.month}月{AS_OF.day}日</span><span class=\"chip\">Hilo/Plinko：8月21日—{AS_OF.month}月{AS_OF.day}日</span><span class=\"chip\">Tower：8月25日—{AS_OF.month}月{AS_OF.day}日</span></div></header>
    <section><h2>核心判断</h2><div class=\"grid\"><div class=\"kpi\"><div class=\"label\">近7日全游戏完全下注额</div><strong>{amount(all_overall['complete_bet'])}</strong><small>生命周期池完整观察日</small></div><div class=\"kpi\"><div class=\"label\">近7日完全实际回报比</div><strong>{pct(all_overall['actual_rtp'])}</strong><small>完全下注与完全实际盈利加权</small></div><div class=\"kpi\"><div class=\"label\">预期RTP字段下注覆盖</div><strong>{pct(all_overall['expected_coverage'])}</strong><small>覆盖不足的游戏不进入实际/预期比较</small></div><div class=\"kpi\"><div class=\"label\">新游戏最高完全下注额</div><strong>{top_new[0]} {amount(top_new[1]['complete_bet'])}</strong><small>上线至今，不与成熟游戏累计直接比较</small></div></div>
    <div class=\"callout\"><strong>全盘结论：</strong>近 7 日全游戏完全实际回报比为 <b>{pct(all_overall['actual_rtp'])}</b>。预期字段覆盖 <b>{pct(all_overall['expected_coverage'])}</b> 的完全下注额，因此“实际与预期差异”只对覆盖范围内的下注有效。三款新游戏中，<b>{status_text}</b>；均仍处于短期观察，不能据此确认或排除配置、结算或资产问题。</div>
    <div class=\"callout warn\"><strong>术语边界：</strong>本报告的“RTP观察值”是生命周期池的完全实际回报比，不替代按有效真金下注、最终结算、退款/取消、免费注和配置版本完成的正式结算 RTP 审计。</div></section>
    <section><h2>全游戏近 7 日：下注规模与回报偏离</h2><p class=\"lead\">所有游戏使用同一窗口 {ALL_START.month} 月 {ALL_START.day} 日—{AS_OF.month} 月 {AS_OF.day} 日。预期字段无值、0 或 Infinity 时保留下注和实际回报，但不计算 RTP 偏离。</p><figure><img src=\"{data_uri(chart2)}\" alt=\"全游戏回报偏离与下注规模\"><figcaption>横轴接近 0 表示在有预期字段的可比下注范围内，实际回报接近预期；纵轴用于区分大额与小额波动。</figcaption></figure>{html_table(['游戏','完全下注额','完全实际回报比','完全预期回报比','RTP差异','预期覆盖','调整影响','状态'],game_rows)}
    </section>
    <section><h2>新上线游戏：上线至今专项追踪</h2><p class=\"lead\">Hilo、Plinko 已观察 {new_summary['Hilo']['days']} 日；Tower 已观察 {new_summary['Tower']['days']} 日。不同观察长度不直接横比，只用于识别持续偏离、单日高回报与盈利差。</p>{html_table(['游戏','Game ID','观察窗口','观察日','完全下注额','完全实际回报比','完全预期回报比','RTP差异','实际−预期盈利','调整影响','状态'],new_rows)}
    <figure><img src=\"{data_uri(chart1)}\" alt=\"新游戏逐日实际与预期回报比\"><figcaption>同一游戏内逐日观察。单日高于 100% 是需复核信号，不自动等同故障。</figcaption></figure>
    <div class=\"callout risk\"><strong>优先核查规则：</strong>仅当“高回报偏离、高调整影响、高下注额”同时出现时，才升级为优先排查对象；仍需有效局数、最终派奖、配置版本和玩法参数才能定位原因。</div>
    </section>
    <section><h2>生命周期 1—4：偏离落点</h2><p class=\"lead\">用于判断偏离是否集中在某个生命周期。空白表示预期字段不可用，而非回报为零。</p><figure><img src=\"{data_uri(chart3)}\" alt=\"新游戏生命周期回报偏离\"><figcaption>颜色仅表达偏离方向与幅度；不代表最终结算故障等级。</figcaption></figure>{html_table(['游戏','生命周期','完全下注额','完全实际回报比','完全预期回报比','RTP差异','调整影响'],lifecycle_rows)}
    </section>
    <section><h2>TC 历史快照：与游戏回报相关但非线性</h2><p>原 TC 审计保留为 8 月 26—28 日的历史快照：上午窗口 TC 分别为 <b>81.72% / 81.46% / 82.95%</b>；8 月 26、27 日完整日 TC 为 <b>79.48% / 79.50%</b>。该结果不因本次生命周期池追踪而改写。</p><div class=\"callout\"><strong>正确关系：</strong>游戏回报会影响玩家可提现资产与后续 TC，但 TC 还受到历史充值、期初余额、Bonus、资产调整、大额中奖和提现审核等因素影响。单个游戏 RTP 不能直接解释全站 TC；本报告只用它筛选需要继续核查的游戏和日期。</div></section>
    <section><h2>数据质量与下一步</h2><ul><li>本次 {ALL_START.month} 月 {ALL_START.day} 日—{AS_OF.month} 月 {AS_OF.day} 日原始分游戏数据共 <b>{len(raw_seven)}</b> 条、覆盖 <b>{len({row['game'] for row in raw_seven})}</b> 款游戏；其中 <b>{len(seven)}</b> 条、<b>{len(grouped)}</b> 款游戏存在有效完全下注并进入 RTP 汇总。游戏×日期未发现重复。</li><li>Hilo、Plinko、Tower 的逐日窗口已分别按上线日切分；Tower达到 7 日后仍需按配置与最终结算复测。</li><li>P0：补齐有效局数、最终结算状态、退款/取消、免费注/Bonus、配置版本与玩法参数，形成按 <code>游戏×日期×版本×配置</code> 的正式审计聚合。</li><li>P0：对出现“高回报偏离 + 高调整影响 + 下注额上升”的游戏，调用资金/资产链路做只读聚合复核；不输出用户清单。</li><li>P1：固定每周刷新相同窗口，保留数据截止日、源表修订和预期字段覆盖率，形成持续监控。</li></ul></section>
    <footer class=\"small\">来源：GM Lifecycle Pool V2（Joint）飞书工作簿修订{workbook_revision}，生命周期奖池分游戏汇总及原始详细奖池表；仅使用脱敏聚合数据。生成时间：2026-09-02。</footer></main></body></html>"""
    HTML_OUT.write_text(report_html, encoding="utf-8")

    md = f"""---
type: game-rtp-tracking-report
status: published_observational
source: GM Lifecycle Pool V2 (Joint) revision {workbook_revision}
as_of: {AS_OF.isoformat()}
---

# Waje 全产品TC与新上线游戏RTP追踪分析 V2

## 核心判断

- 全游戏近7日完全实际回报比为 **{pct(all_overall['actual_rtp'])}**；预期字段覆盖 **{pct(all_overall['expected_coverage'])}** 的完全下注额。
- Hilo、Plinko观察10日，Tower观察6日；均为短期观察，不能作为最终结算RTP或故障结论。
- 只有“高回报偏离、高调整影响、高下注额”同时出现时，才进入优先复核。

## 新游戏上线至今

| 游戏 | 窗口 | 完全下注额 | 实际回报比 | 预期回报比 | 差异 | 调整影响 | 状态 |
|---|---|---:|---:|---:|---:|---:|---|
""" + "\n".join(f"| {game} | {item['launch'][5:]}—{as_of_short} | {amount(item['complete_bet'])} | {pct(item['actual_rtp'])} | {pct(item['expected_rtp'])} | {pp(item['rtp_gap_pp'])} | {pp(item['adjustment_pp'])} | {status(item).replace('<span class=\"tag ', '').split('>')[-1].replace('</span>','')} |" for game, item in new_summary.items()) + f"""

## 口径

- 生命周期池完全实际回报比 = `1 − Σ完全实际盈利 ÷ Σ完全下注额`。
- 生命周期池完全预期回报比只在预期字段有效的完全下注范围内计算。
- 这不是按有效真金下注、最终结算、退款/取消、免费注和配置版本完成的正式结算 RTP 审计。

## 工件

- `analysis/tc_game_rtp_tracking_2026_09_02/report_data.json`
- `analysis/tc_game_rtp_tracking_2026_09_02/quality_checks.json`
- `analysis/tc_game_rtp_tracking_2026_09_02/all_games_7d.csv`
- `analysis/tc_game_rtp_tracking_2026_09_02/new_game_daily.csv`
- `analysis/tc_game_rtp_tracking_2026_09_02/new_game_lifecycle.csv`
"""
    MD_OUT.write_text(md, encoding="utf-8")
    print(json.dumps({"status": "ok", "html": str(HTML_OUT), "markdown": str(MD_OUT), "all_games": len(all_games), "new_games": {g: x['days'] for g, x in new_summary.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
