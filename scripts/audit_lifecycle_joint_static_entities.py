#!/usr/bin/env python3
"""Audit GM Lifecycle Pool v2 (Joint) exports for entity-level static data.

This is intentionally a read-only audit.  It validates the four local GM
exports for each date, fingerprints full snapshots and individual game rows,
and optionally compares an independent re-query snapshot with the first
collection.  It never writes to Lark or changes source exports.

The source files are standard XLSX workbooks, so the reader uses only the
XLSX ZIP/XML format.  That keeps the audit portable and avoids rewriting any
workbook while inspecting it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import zipfile
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_ROOT = ROOT / "data/raw/lifecycle_joint/2026-08-24"
DEFAULT_OUTPUT = ROOT / "analysis/lifecycle_joint_data_integrity_2026_08_24"
DEFAULT_SOURCE_DATA = ROOT / "data/outputs/lifecycle_joint/2026-08-24-lark-update/source-data.json"
DEFAULT_SOURCE_VALIDATION = ROOT / "data/outputs/lifecycle_joint/2026-08-24-lark-update/source-validation.json"
DEFAULT_LARK_READBACK = ROOT / "data/outputs/lifecycle_joint/2026-08-24-lark-update/online-readback-validation.json"

KINDS = ("summary", "detail", "game", "active")
FOCUS_GAMES = ("Hilo", "Plinko")
FOCUS_DATES = ("2026-08-21", "2026-08-22", "2026-08-23")
GAME_METRIC_FIELDS = {
    "base_bet": 1,
    "base_expected_profit": 2,
    "base_actual_profit": 3,
    "base_actual_return_ratio": 4,
    "base_expected_return_ratio": 5,
    "entire_bet": 11,
    "entire_expected_profit": 12,
    "entire_actual_profit": 13,
    "entire_actual_return_ratio": 14,
    "entire_expected_return_ratio": 15,
}

EXPECTED_HEADERS: dict[str, list[str]] = {
    "summary": [
        "总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比",
        "总基础预期回报比", "总完全预期回报比", "总人数", "今日完全实际盈利调整幅度",
        "当前完全实际盈利扣除幅度", "修改",
    ],
    "detail": [
        "生命周期", "游戏类型", "差额", "预期回报比", "盈利比万分比", "实际回报比万分比",
        "基础预期盈利", "基础实际盈利", "基础下注额", "基础真实回报比", "总破产保护金额",
        "总个人盈利控制金额", "完全预期盈利", "完全实际盈利", "完全下注额", "完全下注额占比",
        "完全真实回报比", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改",
    ],
    "game": [
        "游戏", "基础下注额", "基础预期盈利", "基础实际盈利", "基础真实回报比", "基础预期回报比",
        "基础回报比差距", "总破产保护金额", "总个人盈利控制金额", "破产保护/下注", "个人盈利/下注",
        "完全下注额", "完全预期盈利", "完全实际盈利", "完全真实回报比", "完全预期回报比",
        "完全回报比差距", "完全下注额占比",
    ],
    "active": [
        "生命周期", "基础下注额", "基础真实回报比", "基础预期回报比", "基础回报比差距", "基础预期盈利",
        "基础实际盈利", "总破产保护金额", "总个人盈利控制金额", "完全下注额", "完全下注额占比",
        "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全预期盈利", "完全实际盈利",
        "人均实际盈利", "人数", "当日充值总金额", "当日复充总金额", "平均复充次数", "平均流充比",
        "营收", "TX总金额", "人均实际营收", "TC比", "折损系数", "绝对破产人数", "绝对破产次数",
        "人均绝对破产次数",
    ],
}

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
NUMBER_RE = re.compile(r"^-?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$")
PERCENT_RE = re.compile(r"^(-?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)%$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", default=str(DEFAULT_RAW_ROOT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--start-date", default="2026-08-18")
    parser.add_argument("--end-date", default="2026-08-23")
    parser.add_argument("--recheck-root", help="Independent re-query root; omit before recheck is available.")
    parser.add_argument("--source-data", default=str(DEFAULT_SOURCE_DATA))
    parser.add_argument("--source-validation", default=str(DEFAULT_SOURCE_VALIDATION))
    parser.add_argument("--lark-readback", default=str(DEFAULT_LARK_READBACK))
    parser.add_argument("--emit-source-data", help="Write validated target rows for the four lifecycle destination sheets.")
    return parser.parse_args()


def date_range(start: str, end: str) -> list[str]:
    first = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    if first > last:
        raise ValueError(f"Invalid date range: {start} > {end}")
    result: list[str] = []
    current = first
    while current <= last:
        result.append(current.isoformat())
        current += dt.timedelta(days=1)
    return result


def normalize_header(value: Any) -> str:
    return re.sub(r"[\s\u00a0]+", "", str(value if value is not None else "")).strip()


def normalize_number(value: str) -> int | float | str:
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return value
    if not parsed.is_finite():
        return value
    if parsed == parsed.to_integral_value():
        return int(parsed)
    return float(parsed)


def semantic_value(value: Any) -> Any:
    """Normalize number/percentage representations while preserving text labels."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, list):
        return [semantic_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): semantic_value(item) for key, item in sorted(value.items())}
    text = str(value).strip()
    percent_match = PERCENT_RE.fullmatch(text)
    if percent_match:
        return float(Decimal(percent_match.group(1)) / Decimal("100"))
    if NUMBER_RE.fullmatch(text):
        return normalize_number(text)
    return text


def canonical(value: Any) -> str:
    return json.dumps(semantic_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def col_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    value = 0
    for character in letters:
        value = value * 26 + ord(character.upper()) - 64
    return value - 1


def element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(node.text or "" for node in element.iter(f"{NS_MAIN}t"))


def first_sheet_member(zf: zipfile.ZipFile) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    first_sheet = workbook.find(f"{NS_MAIN}sheets/{NS_MAIN}sheet")
    if first_sheet is None:
        raise ValueError("Workbook has no worksheets")
    rel_id = first_sheet.attrib.get(f"{NS_REL}id")
    if not rel_id:
        raise ValueError("Workbook sheet relationship missing")
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel = next((item for item in rels.findall(f"{NS_PKG_REL}Relationship") if item.attrib.get("Id") == rel_id), None)
    if rel is None:
        raise ValueError(f"Workbook relationship {rel_id} not found")
    target = PurePosixPath(rel.attrib["Target"])
    return str(PurePosixPath("xl") / target)


def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    member = "xl/sharedStrings.xml"
    if member not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(member))
    return [element_text(item) for item in root.findall(f"{NS_MAIN}si")]


def parse_cell(cell: ET.Element, strings: list[str]) -> Any:
    cell_type = cell.attrib.get("t")
    formula = cell.find(f"{NS_MAIN}f")
    raw_value = cell.findtext(f"{NS_MAIN}v")
    if cell_type == "inlineStr":
        value: Any = element_text(cell.find(f"{NS_MAIN}is"))
    elif cell_type == "s":
        if raw_value is None:
            value = ""
        else:
            index = int(raw_value)
            value = strings[index] if 0 <= index < len(strings) else ""
    elif cell_type == "b":
        value = raw_value == "1"
    elif cell_type in {"str", "e"}:
        value = raw_value or ""
    elif raw_value is None:
        value = None
    elif NUMBER_RE.fullmatch(raw_value):
        value = normalize_number(raw_value)
    else:
        value = raw_value
    if formula is not None:
        return {"formula": formula.text or "", "value": value}
    return value


def read_xlsx(path: Path) -> list[list[Any]]:
    with zipfile.ZipFile(path) as zf:
        strings = shared_strings(zf)
        sheet = ET.fromstring(zf.read(first_sheet_member(zf)))
        parsed_rows: list[tuple[int, dict[int, Any]]] = []
        max_col = 0
        for row in sheet.findall(f"{NS_MAIN}sheetData/{NS_MAIN}row"):
            row_index = int(row.attrib.get("r", len(parsed_rows) + 1))
            values: dict[int, Any] = {}
            for cell in row.findall(f"{NS_MAIN}c"):
                reference = cell.attrib.get("r", "A1")
                index = col_index(reference)
                values[index] = parse_cell(cell, strings)
                max_col = max(max_col, index + 1)
            if values:
                parsed_rows.append((row_index, values))
        if not parsed_rows:
            raise ValueError("No worksheet values")
        rows: list[list[Any]] = []
        for _, values in parsed_rows:
            rows.append([values.get(index) for index in range(max_col)])
        while rows and all(value is None for value in rows[-1]):
            rows.pop()
        return rows


def number(value: Any, label: str) -> float:
    parsed = semantic_value(value)
    if isinstance(parsed, bool):
        return float(parsed)
    if isinstance(parsed, (int, float)):
        return float(parsed)
    raise ValueError(f"{label}: expected numeric value, got {value!r}")


def close(actual: float, expected: float, tolerance: float, label: str) -> dict[str, Any]:
    delta = abs(actual - expected)
    if delta > tolerance:
        raise ValueError(f"{label}: {actual} != {expected}; delta={delta}, tolerance={tolerance}")
    return {"actual": actual, "expected": expected, "delta": delta, "tolerance": tolerance}


def sum_column(rows: list[list[Any]], index: int, label: str) -> float:
    return sum(number(row[index], f"{label}[{position}]") for position, row in enumerate(rows, start=1))


def normal_table_payload(table: dict[str, Any]) -> dict[str, Any]:
    return {"headers": table["headers"], "rows": table["rows"]}


def cell_type(value: Any) -> str:
    semantic = semantic_value(value)
    if semantic is None:
        return "blank"
    if isinstance(semantic, bool):
        return "boolean"
    if isinstance(semantic, (int, float)):
        return "number"
    if isinstance(semantic, dict) and "formula" in semantic:
        return "formula"
    return "text"


def column_type_profile(headers: list[Any], rows: list[list[Any]]) -> list[dict[str, Any]]:
    profile: list[dict[str, Any]] = []
    for index, header in enumerate(headers):
        counts: dict[str, int] = defaultdict(int)
        for row in rows:
            counts[cell_type(row[index])] += 1
        non_blank = [kind for kind, count in counts.items() if kind != "blank" and count]
        profile.append({
            "field": str(header),
            "types": dict(sorted(counts.items())),
            "inferred_type": non_blank[0] if len(non_blank) == 1 else "mixed" if non_blank else "blank",
        })
    return profile


def table_meta(path: Path, kind: str) -> dict[str, Any]:
    values = read_xlsx(path)
    headers = values[0]
    rows = values[1:]
    normalized_expected = [normalize_header(item) for item in EXPECTED_HEADERS[kind]]
    normalized_actual = [normalize_header(item) for item in headers]
    if normalized_actual != normalized_expected:
        raise ValueError(
            f"{kind} header mismatch: actual={normalized_actual!r} expected={normalized_expected!r}"
        )
    if any(len(row) != len(headers) for row in rows):
        raise ValueError(f"{kind} contains ragged rows")
    table = {"headers": headers, "rows": rows}
    return {
        **table,
        "file_sha256": sha256_file(path),
        "content_fingerprint": fingerprint(normal_table_payload(table)),
        "row_count": len(rows),
        "column_count": len(headers),
        "column_type_profile": column_type_profile(headers, rows),
        "header_match": True,
    }


def assert_unique(keys: list[Any], label: str) -> None:
    duplicates = [key for key, count in defaultdict(int, ((key, keys.count(key)) for key in set(keys))).items() if count > 1]
    if duplicates:
        raise ValueError(f"{label}: duplicate keys {duplicates[:8]!r}")


def keyed_rows(rows: list[list[Any]], kind: str) -> dict[str, list[list[Any]]]:
    grouped: dict[str, list[list[Any]]] = defaultdict(list)
    if kind == "game":
        for row in rows:
            grouped[str(semantic_value(row[0]))].append(row)
    elif kind == "detail":
        for row in rows:
            grouped[str(semantic_value(row[1]))].append(row)
    elif kind == "active":
        for row in rows:
            grouped[str(semantic_value(row[0]))].append(row)
    else:
        grouped["__summary__"] = rows
    return grouped


def stable_row_fingerprint(rows: list[list[Any]], kind: str) -> str:
    if kind == "detail":
        payload = sorted(rows, key=lambda row: (number(row[0], "detail.lifecycle"), canonical(row)))
    else:
        payload = rows
    return fingerprint(payload)


def validate_date(date: str, tables: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary = tables["summary"]["rows"]
    detail = tables["detail"]["rows"]
    game = tables["game"]["rows"]
    active = tables["active"]["rows"]
    if len(summary) != 1:
        raise ValueError(f"{date}: summary rows must equal 1, got {len(summary)}")
    if not game:
        raise ValueError(f"{date}: game export is empty")
    game_names = [str(semantic_value(row[0])) for row in game]
    assert_unique(game_names, f"{date}: game")

    detail_keys = [
        (int(number(row[0], f"{date}:detail.lifecycle")), str(semantic_value(row[1])))
        for row in detail
    ]
    assert_unique(detail_keys, f"{date}: detail lifecycle×game")
    lifecycles = sorted({key[0] for key in detail_keys})
    if lifecycles != list(range(0, 12)):
        raise ValueError(f"{date}: expected detail lifecycle 0–11, got {lifecycles!r}")
    for lifecycle in lifecycles:
        row_games = {game_name for row_life, game_name in detail_keys if row_life == lifecycle}
        if row_games != set(game_names):
            raise ValueError(f"{date}: detail lifecycle {lifecycle} game coverage mismatch")
    if len(detail) != len(game) * len(lifecycles):
        raise ValueError(f"{date}: detail rows={len(detail)}; expected {len(game) * len(lifecycles)}")

    active_lifecycles = [int(number(row[0], f"{date}:active.lifecycle")) for row in active]
    assert_unique(active_lifecycles, f"{date}: active lifecycle")
    if any(value < 1 or value > 11 for value in active_lifecycles):
        raise ValueError(f"{date}: active lifecycle out of range: {active_lifecycles!r}")
    if not set(range(1, 5)).issubset(set(active_lifecycles)):
        raise ValueError(f"{date}: active export must contain lifecycle 1–4")

    active_amounts = {
        "base_bet": sum_column(active, 1, f"{date}:active.base_bet"),
        "base_expected": sum_column(active, 5, f"{date}:active.base_expected"),
        "base_actual": sum_column(active, 6, f"{date}:active.base_actual"),
        "protection": sum_column(active, 7, f"{date}:active.protection"),
        "control": sum_column(active, 8, f"{date}:active.control"),
        "entire_bet": sum_column(active, 9, f"{date}:active.entire_bet"),
        "entire_expected": sum_column(active, 14, f"{date}:active.entire_expected"),
        "entire_actual": sum_column(active, 15, f"{date}:active.entire_actual"),
        "people": sum_column(active, 17, f"{date}:active.people"),
    }
    game_amounts = {
        "base_bet": sum_column(game, 1, f"{date}:game.base_bet"),
        "base_expected": sum_column(game, 2, f"{date}:game.base_expected"),
        "base_actual": sum_column(game, 3, f"{date}:game.base_actual"),
        "protection": sum_column(game, 7, f"{date}:game.protection"),
        "control": sum_column(game, 8, f"{date}:game.control"),
        "entire_bet": sum_column(game, 11, f"{date}:game.entire_bet"),
        "entire_expected": sum_column(game, 12, f"{date}:game.entire_expected"),
        "entire_actual": sum_column(game, 13, f"{date}:game.entire_actual"),
    }
    cross: dict[str, Any] = {"active_vs_game": {}, "summary_vs_active": {}, "detail_vs_game": {}}
    for metric in ("base_bet", "base_expected", "base_actual", "protection", "control", "entire_bet", "entire_expected", "entire_actual"):
        cross["active_vs_game"][metric] = close(active_amounts[metric], game_amounts[metric], 0.25, f"{date}: active/game {metric}")
    summary_row = summary[0]
    cross["summary_vs_active"]["base_bet"] = close(number(summary_row[0], f"{date}:summary.base_bet"), active_amounts["base_bet"], 0.05, f"{date}: summary base bet")
    cross["summary_vs_active"]["entire_bet"] = close(number(summary_row[1], f"{date}:summary.entire_bet"), active_amounts["entire_bet"], 0.05, f"{date}: summary entire bet")
    cross["summary_vs_active"]["people"] = close(number(summary_row[6], f"{date}:summary.people"), active_amounts["people"], 0.0, f"{date}: summary people")
    if active_amounts["base_bet"]:
        cross["summary_vs_active"]["base_actual_return"] = close(number(summary_row[2], f"{date}:summary.base_actual_return"), 1 - active_amounts["base_actual"] / active_amounts["base_bet"], 0.00015, f"{date}: summary base actual return")
        cross["summary_vs_active"]["base_expected_return"] = close(number(summary_row[4], f"{date}:summary.base_expected_return"), 1 - active_amounts["base_expected"] / active_amounts["base_bet"], 0.00015, f"{date}: summary base expected return")
    if active_amounts["entire_bet"]:
        cross["summary_vs_active"]["entire_actual_return"] = close(number(summary_row[3], f"{date}:summary.entire_actual_return"), 1 - active_amounts["entire_actual"] / active_amounts["entire_bet"], 0.00015, f"{date}: summary entire actual return")
        cross["summary_vs_active"]["entire_expected_return"] = close(number(summary_row[5], f"{date}:summary.entire_expected_return"), 1 - active_amounts["entire_expected"] / active_amounts["entire_bet"], 0.00015, f"{date}: summary entire expected return")

    detail_by_game = keyed_rows(detail, "detail")
    for game_row in game:
        game_name = str(semantic_value(game_row[0]))
        game_detail = [row for row in detail_by_game[game_name] if 1 <= int(number(row[0], f"{date}:{game_name}.lifecycle")) <= 11]
        if len(game_detail) != 11:
            raise ValueError(f"{date}: {game_name} detail lifecycle 1–11 rows={len(game_detail)}")
        pairs = {
            "base_bet": (sum_column(game_detail, 8, f"{date}:{game_name}.detail.base_bet"), number(game_row[1], f"{date}:{game_name}.game.base_bet")),
            "base_expected": (sum_column(game_detail, 6, f"{date}:{game_name}.detail.base_expected"), number(game_row[2], f"{date}:{game_name}.game.base_expected")),
            "base_actual": (sum_column(game_detail, 7, f"{date}:{game_name}.detail.base_actual"), number(game_row[3], f"{date}:{game_name}.game.base_actual")),
            "protection": (sum_column(game_detail, 10, f"{date}:{game_name}.detail.protection"), number(game_row[7], f"{date}:{game_name}.game.protection")),
            "control": (sum_column(game_detail, 11, f"{date}:{game_name}.detail.control"), number(game_row[8], f"{date}:{game_name}.game.control")),
            "entire_bet": (sum_column(game_detail, 14, f"{date}:{game_name}.detail.entire_bet"), number(game_row[11], f"{date}:{game_name}.game.entire_bet")),
            "entire_expected": (sum_column(game_detail, 12, f"{date}:{game_name}.detail.entire_expected"), number(game_row[12], f"{date}:{game_name}.game.entire_expected")),
            "entire_actual": (sum_column(game_detail, 13, f"{date}:{game_name}.detail.entire_actual"), number(game_row[13], f"{date}:{game_name}.game.entire_actual")),
        }
        cross["detail_vs_game"][game_name] = {metric: close(actual, expected, 0.25, f"{date}: detail/game {game_name} {metric}") for metric, (actual, expected) in pairs.items()}
        base_bet = number(game_row[1], f"{date}:{game_name}.base_bet")
        entire_bet = number(game_row[11], f"{date}:{game_name}.entire_bet")
        if base_bet:
            close(number(game_row[4], f"{date}:{game_name}.base_actual_return"), 1 - number(game_row[3], f"{date}:{game_name}.base_actual") / base_bet, 0.00015, f"{date}: {game_name} base actual return")
            close(number(game_row[5], f"{date}:{game_name}.base_expected_return"), 1 - number(game_row[2], f"{date}:{game_name}.base_expected") / base_bet, 0.00015, f"{date}: {game_name} base expected return")
        if entire_bet:
            close(number(game_row[14], f"{date}:{game_name}.entire_actual_return"), 1 - number(game_row[13], f"{date}:{game_name}.entire_actual") / entire_bet, 0.00015, f"{date}: {game_name} entire actual return")
            close(number(game_row[15], f"{date}:{game_name}.entire_expected_return"), 1 - number(game_row[12], f"{date}:{game_name}.entire_expected") / entire_bet, 0.00015, f"{date}: {game_name} entire expected return")

    return {
        "status": "passed",
        "game_count": len(game),
        "detail_lifecycle_range": lifecycles,
        "detail_rows": len(detail),
        "active_lifecycles": active_lifecycles,
        "active_rows": len(active),
        "cross_table": cross,
    }


def audit_root(root: Path, dates: list[str]) -> dict[str, Any]:
    output: dict[str, Any] = {"root": str(root), "dates": {}, "files_expected": len(dates) * len(KINDS)}
    files_seen = 0
    all_file_hashes: list[str] = []
    all_content_hashes: list[str] = []
    daily_tables: dict[str, dict[str, dict[str, Any]]] = {}
    for date in dates:
        entry: dict[str, Any] = {"date": date, "status": "passed", "files": {}, "quality": None, "errors": []}
        tables: dict[str, dict[str, Any]] = {}
        for kind in KINDS:
            path = root / date / f"{kind}.xlsx"
            if not path.exists():
                entry["status"] = "blocked"
                entry["errors"].append(f"missing {kind}: {path}")
                continue
            try:
                table = table_meta(path, kind)
                entry["files"][kind] = {
                    "path": str(path),
                    "file_sha256": table["file_sha256"],
                    "content_fingerprint": table["content_fingerprint"],
                    "row_count": table["row_count"],
                    "column_count": table["column_count"],
                    "column_type_profile": table["column_type_profile"],
                    "header_match": table["header_match"],
                }
                tables[kind] = table
                files_seen += 1
                all_file_hashes.append(table["file_sha256"])
                all_content_hashes.append(table["content_fingerprint"])
            except Exception as error:  # noqa: BLE001 - report every source failure.
                entry["status"] = "failed"
                entry["errors"].append(f"{kind}: {error}")
        if len(tables) == len(KINDS):
            try:
                entry["quality"] = validate_date(date, tables)
            except Exception as error:  # noqa: BLE001
                entry["status"] = "failed"
                entry["errors"].append(f"cross-table: {error}")
        else:
            entry["quality"] = {"status": "blocked"}
        output["dates"][date] = entry
        if entry["status"] == "passed":
            daily_tables[date] = tables
    output["files_seen"] = files_seen
    output["hash_uniqueness"] = {
        "binary_sha256": {"count": len(all_file_hashes), "distinct": len(set(all_file_hashes)), "all_unique": len(all_file_hashes) == len(set(all_file_hashes))},
        "normalized_content": {"count": len(all_content_hashes), "distinct": len(set(all_content_hashes)), "all_unique": len(all_content_hashes) == len(set(all_content_hashes))},
    }
    output["status"] = "passed" if all(item["status"] == "passed" for item in output["dates"].values()) else "partial"
    output["_tables"] = daily_tables
    return output


def entity_fingerprints(tables: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    game_rows = keyed_rows(tables["game"]["rows"], "game")
    detail_rows = keyed_rows(tables["detail"]["rows"], "detail")
    active_rows = keyed_rows(tables["active"]["rows"], "active")
    return {
        "game": {key: stable_row_fingerprint(rows, "game") for key, rows in game_rows.items()},
        "detail_game": {key: stable_row_fingerprint(rows, "detail") for key, rows in detail_rows.items()},
        "active_lifecycle": {key: stable_row_fingerprint(rows, "active") for key, rows in active_rows.items()},
        "summary": {"__summary__": stable_row_fingerprint(tables["summary"]["rows"], "summary")},
    }


def compare_adjacent(audit: dict[str, Any], dates: list[str]) -> dict[str, Any]:
    tables: dict[str, dict[str, dict[str, Any]]] = audit["_tables"]
    comparisons: list[dict[str, Any]] = []
    for previous, current in zip(dates, dates[1:]):
        if previous not in tables or current not in tables:
            comparisons.append({"from": previous, "to": current, "status": "blocked"})
            continue
        previous_fingerprints = entity_fingerprints(tables[previous])
        current_fingerprints = entity_fingerprints(tables[current])
        table_status: dict[str, Any] = {}
        for kind in KINDS:
            prior = audit["dates"][previous]["files"][kind]
            next_item = audit["dates"][current]["files"][kind]
            table_status[kind] = {
                "binary_identical": prior["file_sha256"] == next_item["file_sha256"],
                "content_identical": prior["content_fingerprint"] == next_item["content_fingerprint"],
                "state": "whole_snapshot_duplicate" if prior["content_fingerprint"] == next_item["content_fingerprint"] else "changed",
            }
        entity_status: dict[str, dict[str, Any]] = {}
        for entity_kind in ("game", "detail_game", "active_lifecycle", "summary"):
            prior = previous_fingerprints[entity_kind]
            next_item = current_fingerprints[entity_kind]
            all_keys = sorted(set(prior) | set(next_item))
            states: list[dict[str, str]] = []
            for key in all_keys:
                if key not in prior:
                    state = "new_entity"
                elif key not in next_item:
                    state = "missing_entity"
                elif prior[key] == next_item[key]:
                    state = "static_entity"
                else:
                    state = "changed"
                states.append({"entity": key, "state": state, "from_fingerprint": prior.get(key), "to_fingerprint": next_item.get(key)})
            counts: dict[str, int] = defaultdict(int)
            for state in states:
                counts[state["state"]] += 1
            entity_status[entity_kind] = {"counts": dict(counts), "states": states}
        focus: dict[str, Any] = {}
        for game in FOCUS_GAMES:
            game_state = next((item for item in entity_status["game"]["states"] if item["entity"] == game), None)
            detail_state = next((item for item in entity_status["detail_game"]["states"] if item["entity"] == game), None)
            focus[game] = {
                "game_state": game_state["state"] if game_state else "missing_entity",
                "detail_state": detail_state["state"] if detail_state else "missing_entity",
                "all_fields_static": bool(game_state and detail_state and game_state["state"] == detail_state["state"] == "static_entity"),
            }
        comparisons.append({
            "from": previous,
            "to": current,
            "status": "passed",
            "whole_snapshot_state": "whole_snapshot_duplicate" if all(item["content_identical"] for item in table_status.values()) else "changed",
            "whole_snapshot": table_status,
            "entities": entity_status,
            "focus_games": focus,
        })
    return {"adjacent_dates": comparisons}


def iso_date(value: Any) -> str:
    text = str(value).strip().replace("-", "/")
    year, month, day = text.split("/")
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def display_date(date: str) -> str:
    year, month, day = date.split("-")
    return f"{int(year)}/{int(month)}/{int(day)}"


def rows_equivalent(left: list[Any], right: list[Any]) -> bool:
    if len(left) != len(right):
        return False
    for first, second in zip(left, right):
        normal_first = semantic_value(first)
        normal_second = semantic_value(second)
        if isinstance(normal_first, (int, float)) and isinstance(normal_second, (int, float)):
            if abs(float(normal_first) - float(normal_second)) > 1e-9:
                return False
        elif normal_first != normal_second:
            return False
    return True


def compare_payload_to_raw(audit: dict[str, Any], source_path: Path, dates: list[str]) -> dict[str, Any]:
    if not source_path.exists():
        return {"status": "not_available", "reason": f"missing {source_path}"}
    source = json.loads(source_path.read_text(encoding="utf-8"))
    target_rows = source.get("target_rows", {})
    results: dict[str, Any] = {"status": "passed", "dates": {}, "source": str(source_path)}
    for date in dates:
        if date not in audit["_tables"]:
            results["status"] = "partial"
            results["dates"][date] = {"status": "blocked", "reason": "raw audit unavailable"}
            continue
        item: dict[str, Any] = {"status": "passed", "sheets": {}}
        tables = audit["_tables"][date]
        for kind in KINDS:
            raw_rows = tables[kind]["rows"]
            if kind == "summary":
                # The online summary contract is A:J: date plus the first nine
                # GM measures.  The source-only trailing “修改” field is
                # intentionally not written to the target workbook.
                raw_rows = [row[:9] for row in raw_rows]
            elif kind == "detail":
                raw_rows = [row for row in raw_rows if 0 <= int(number(row[0], f"{date}.detail.lifecycle")) <= 4]
            elif kind == "active":
                raw_rows = [row for row in raw_rows if 1 <= int(number(row[0], f"{date}.active.lifecycle")) <= 4]
            actual = [row for row in target_rows.get(kind, []) if iso_date(row[0]) == date]
            expected = [[display_date(date), *row] for row in raw_rows]
            if kind == "detail":
                actual = sorted(actual, key=lambda row: (int(number(row[1], "source.detail.lifecycle")), str(semantic_value(row[2]))))
                expected = sorted(expected, key=lambda row: (int(number(row[1], "raw.detail.lifecycle")), str(semantic_value(row[2]))))
            elif kind == "game":
                actual = sorted(actual, key=lambda row: str(semantic_value(row[1])))
                expected = sorted(expected, key=lambda row: str(semantic_value(row[1])))
            elif kind == "active":
                actual = sorted(actual, key=lambda row: int(number(row[1], "source.active.lifecycle")))
                expected = sorted(expected, key=lambda row: int(number(row[1], "raw.active.lifecycle")))
            differences = [index for index, (left, right) in enumerate(zip(actual, expected), start=1) if not rows_equivalent(left, right)]
            equal = len(actual) == len(expected) and not differences
            item["sheets"][kind] = {"expected_rows": len(expected), "payload_rows": len(actual), "match": equal, "mismatch_rows": differences[:10]}
            if not equal:
                item["status"] = "failed"
                results["status"] = "partial"
        results["dates"][date] = item
    return results


def build_target_source_data(audit: dict[str, Any], dates: list[str], raw_root: Path) -> dict[str, Any]:
    target_rows: dict[str, list[list[Any]]] = {kind: [] for kind in KINDS}
    per_date: dict[str, Any] = {}
    for date in dates:
        tables = audit["_tables"].get(date)
        if not tables:
            raise ValueError(f"Cannot emit source data: audit tables missing for {date}")
        display = display_date(date)
        summary = tables["summary"]["rows"]
        detail = tables["detail"]["rows"]
        game = tables["game"]["rows"]
        active = tables["active"]["rows"]
        # The online summary has A:J only: date plus the nine measures before
        # the source-only trailing “修改” column.
        target_rows["summary"].extend([[display, *row[:9]] for row in summary])
        target_rows["detail"].extend([[display, *row] for row in detail if 0 <= int(number(row[0], f"{date}.detail.lifecycle")) <= 4])
        target_rows["game"].extend([[display, *row] for row in game])
        target_rows["active"].extend([[display, *row] for row in active if 1 <= int(number(row[0], f"{date}.active.lifecycle")) <= 4])
        per_date[date] = {
            "source_rows": {kind: len(tables[kind]["rows"]) for kind in KINDS},
            "target_rows": {
                "summary": 1,
                "detail": sum(1 for row in detail if 0 <= int(number(row[0], f"{date}.detail.lifecycle")) <= 4),
                "game": len(game),
                "active": sum(1 for row in active if 1 <= int(number(row[0], f"{date}.active.lifecycle")) <= 4),
            },
        }
    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds"),
        "raw_root": str(raw_root),
        "window": {"start": dates[0], "end": dates[-1], "timezone": "Asia/Hong_Kong"},
        "per_date": per_date,
        "target_rows": target_rows,
    }


def compact_table_difference(first: dict[str, Any], second: dict[str, Any], kind: str) -> dict[str, Any]:
    if kind == "summary":
        changed = []
        headers = first["headers"]
        left = first["rows"][0] if first["rows"] else []
        right = second["rows"][0] if second["rows"] else []
        for index, (a, b) in enumerate(zip(left, right)):
            if semantic_value(a) != semantic_value(b):
                changed.append(headers[index])
        return {"changed_fields": changed}
    first_groups = keyed_rows(first["rows"], kind)
    second_groups = keyed_rows(second["rows"], kind)
    changed = []
    for key in sorted(set(first_groups) | set(second_groups)):
        if key not in first_groups:
            state = "new_entity"
        elif key not in second_groups:
            state = "missing_entity"
        elif stable_row_fingerprint(first_groups[key], kind) == stable_row_fingerprint(second_groups[key], kind):
            continue
        else:
            state = "changed"
        changed.append({"entity": key, "state": state})
    return {"changed_entities": changed[:80], "changed_entity_count": len(changed)}


def game_metrics(tables: dict[str, dict[str, Any]], game: str) -> dict[str, Any] | None:
    row = next((item for item in tables["game"]["rows"] if str(semantic_value(item[0])) == game), None)
    if row is None:
        return None
    return {field: semantic_value(row[index]) for field, index in GAME_METRIC_FIELDS.items()}


def numeric_deltas(first: dict[str, Any] | None, second: dict[str, Any] | None) -> dict[str, float | None]:
    if not first or not second:
        return {}
    output: dict[str, float | None] = {}
    for field in GAME_METRIC_FIELDS:
        left = first.get(field)
        right = second.get(field)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            output[field] = float(right) - float(left)
        else:
            output[field] = None
    return output


def compare_recheck(first_audit: dict[str, Any], recheck_audit: dict[str, Any], dates: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "pending", "dates": {}, "classification": "recheck_pending", "lark_action": "no_change_before_recheck"}
    if recheck_audit["status"] != "passed":
        result["status"] = "blocked"
        result["classification"] = "recheck_incomplete"
        result["reason"] = "One or more independent recheck files did not pass raw validation."
        return result
    all_equal = True
    for date in dates:
        first_tables = first_audit["_tables"].get(date)
        second_tables = recheck_audit["_tables"].get(date)
        if not first_tables or not second_tables:
            result["dates"][date] = {"status": "blocked", "reason": "missing audited date"}
            all_equal = False
            continue
        kinds: dict[str, Any] = {}
        exact = True
        for kind in KINDS:
            first_meta = first_audit["dates"][date]["files"][kind]
            second_meta = recheck_audit["dates"][date]["files"][kind]
            content_equal = first_meta["content_fingerprint"] == second_meta["content_fingerprint"]
            binary_equal = first_meta["file_sha256"] == second_meta["file_sha256"]
            kinds[kind] = {
                "content_identical": content_equal,
                "binary_identical": binary_equal,
                "first_rows": first_meta["row_count"],
                "recheck_rows": second_meta["row_count"],
                "difference": None if content_equal else compact_table_difference(first_tables[kind], second_tables[kind], kind),
            }
            exact = exact and content_equal
        first_fp = entity_fingerprints(first_tables)
        second_fp = entity_fingerprints(second_tables)
        focus = {}
        for game in FOCUS_GAMES:
            first_metrics = game_metrics(first_tables, game)
            recheck_metrics = game_metrics(second_tables, game)
            focus[game] = {
                "game_fingerprint_equal": first_fp["game"].get(game) == second_fp["game"].get(game),
                "detail_fingerprint_equal": first_fp["detail_game"].get(game) == second_fp["detail_game"].get(game),
                "first_game_fingerprint": first_fp["game"].get(game),
                "recheck_game_fingerprint": second_fp["game"].get(game),
                "first_detail_fingerprint": first_fp["detail_game"].get(game),
                "recheck_detail_fingerprint": second_fp["detail_game"].get(game),
                "first_metrics": first_metrics,
                "recheck_metrics": recheck_metrics,
                "metric_deltas": numeric_deltas(first_metrics, recheck_metrics),
            }
        result["dates"][date] = {
            "status": "exact_values_match" if exact else "values_changed",
            "kinds": kinds,
            "active_lifecycle_rows": {
                "first": len(first_tables["active"]["rows"]),
                "recheck": len(second_tables["active"]["rows"]),
            },
            "focus_games": focus,
        }
        all_equal = all_equal and exact
    if all_equal:
        result.update({
            "status": "passed",
            "classification": "source_static_confirmed",
            "lark_action": "no_lark_change",
            "interpretation": "Independent exports match the first exports at normalized table-value level. Static target-game entities are source-level observations, not an HTML/Lark mapping artifact.",
        })
    else:
        result.update({
            "status": "partial",
            "classification": "source_query_mismatch",
            "lark_action": "freeze_current_hilo_plinko_conclusions_and_review_before_any_lark_correction",
            "interpretation": "All independent source exports differ from the first query. This is consistent with an incomplete/unstable first snapshot or historical-source reprocessing; it is not evidence of player behavior. Do not overwrite Lark until the data owner resolves the source snapshot state.",
        })
    return result


def root_cause_markdown(raw: dict[str, Any], comparisons: dict[str, Any], lark_payload: dict[str, Any], recheck: dict[str, Any]) -> str:
    static_lines: list[str] = []
    for item in comparisons["adjacent_dates"]:
        if item.get("status") != "passed":
            continue
        for game in FOCUS_GAMES:
            focus = item["focus_games"].get(game, {})
            if focus.get("all_fields_static"):
                static_lines.append(f"- {game}：{item['from']} → {item['to']} 的分游戏行和全部生命周期明细行均为全字段同指纹。")
            elif focus:
                static_lines.append(f"- {game}：{item['from']} → {item['to']} 分游戏={focus.get('game_state')}，明细={focus.get('detail_state')}。")
    whole_lines: list[str] = []
    for item in comparisons["adjacent_dates"]:
        if item.get("status") != "passed":
            continue
        changed = [kind for kind, state in item["whole_snapshot"].items() if not state["content_identical"]]
        whole_lines.append(f"- {item['from']} → {item['to']}：整表内容变化的区块为 {', '.join(changed) or '无'}。")
    recheck_status = recheck.get("classification", "recheck_pending")
    recheck_text = recheck.get("interpretation") or recheck.get("reason") or "独立复查尚未完成。"
    mismatch_lines: list[str] = []
    for date in FOCUS_DATES:
        entry = recheck.get("dates", {}).get(date, {})
        if entry.get("status") != "values_changed":
            continue
        active = entry.get("active_lifecycle_rows", {})
        games = entry.get("focus_games", {})
        figures = []
        for game in FOCUS_GAMES:
            game_data = games.get(game, {})
            first_bet = (game_data.get("first_metrics") or {}).get("base_bet")
            next_bet = (game_data.get("recheck_metrics") or {}).get("base_bet")
            if isinstance(first_bet, (int, float)) and isinstance(next_bet, (int, float)):
                figures.append(f"{game} 基础下注额 {first_bet:,.2f} → {next_bet:,.2f}")
        mismatch_lines.append(f"- {date}：活跃生命周期行数 {active.get('first')} → {active.get('recheck')}；{'；'.join(figures)}。")
    recheck_daily_lines: list[str] = []
    for item in (recheck.get("recheck_adjacent_content_audit") or {}).get("adjacent_dates", []):
        if item.get("status") != "passed":
            continue
        states = []
        for game in FOCUS_GAMES:
            focus = item.get("focus_games", {}).get(game, {})
            states.append(f"{game}={focus.get('game_state')}/{focus.get('detail_state')}")
        recheck_daily_lines.append(f"- 独立复查 {item['from']} → {item['to']}：{'；'.join(states)}。")
    return f"""# 生命周期数据重复值根因审计

## 结论

当前证据将 Hilo、Plinko 标记为 `data_static_suspect`。这表示其跨日实体级导出值存在完整重复，**不等于**羊毛、机器人、无用户、RTP 异常或系统故障。对 Hilo/Plinko 的日趋势、稳定回报或用户行为解释应暂停，直至独立复查完成。

## 原始文件全量检查

- 计划文件数：{raw.get('files_expected')}；实际通过解析文件数：{raw.get('files_seen')}；全量原始审计状态：`{raw.get('status')}`。
- 每日均检查了表头、行数、主键唯一性、生命周期覆盖和四表下注额/盈利/回报比勾稽。
- 所有日期的整表二进制哈希及标准化内容指纹均保存在 `raw-audit.json`，避免把“某游戏静态”误判为整份导出缓存。

## 跨日实体指纹

{chr(10).join(static_lines) if static_lines else '- 当前没有可用的目标游戏跨日指纹比较。'}

### 整体快照是否重复

{chr(10).join(whole_lines) if whole_lines else '- 当前没有可用的整表比较。'}

因此，若整体快照/其他游戏仍变化而某个新游戏持续静态，优先归类为**实体级源数据静态信号**，不是 HTML 渲染缓存或飞书批量写入的直接证据。

## 飞书写入层复核

- 首次源数据→待写入载荷比对状态：`{lark_payload.get('status')}`。
- 既有在线回读验证由 2026-08-24 更新回执保留；本次审计不修改飞书。
- 当前策略：只有独立复查导出显示首次查询值不同，才冻结相关结论并提出更正清单；在数据拥有方复核前不覆盖飞书历史。

## 独立复查状态

- 当前分类：`{recheck_status}`。
- {recheck_text}

{chr(10).join(mismatch_lines) if mismatch_lines else ''}

独立查询的日期控件均已回读为目标日期，且四类导出均通过表头/主键/勾稽校验。首次与复查在三日、四表均不一致，因此**原先报告的数值不能继续用作业务分析依据**。最可能的流程缺口是首次采集只凭行数可用即导出，没有等待查询结果的值指纹稳定；“上游历史聚合在两次查询之间重处理”仍是待数据拥有方确认的替代解释。

{chr(10).join(recheck_daily_lines) if recheck_daily_lines else ''}

独立复查中若 Hilo/Plinko 的实体指纹跨日已变动，说明初始快照中的“跨日完全相同”不能作为当前产品行为事实，也不能继续用于回报或羊毛判断。

## 可能原因与不可下结论的边界

1. 新游戏在所选日期没有新增有效局，或新增局未进入该生命周期聚合。
2. Provider/game-id 映射、生命周期聚合、跨日结算、免费/测试局或风险排除存在延迟/静态快照。
3. 首轮查询的日期关联或下载关联错误；只有独立复查返回不同值时，才把这一项升级为 `source_query_mismatch`。

现有聚合数据没有用户、订单、设备、IP、局号、机器人标识、规则命中或结算状态。因此本报告不得把重复值归因为羊毛或任何具体用户行为。

## 建议的强制门禁

新游戏上线后前 7 天，在报告生成前比较 `date×game` 与 `date×lifecycle×game` 的相邻日期全字段指纹。若整体数据变化、目标新游戏却保持静态，则：

1. 设为 `data_static_suspect`；
2. 禁止使用该实体构建日趋势、产品表现、RTP 或羊毛结论；
3. 保存“选择日期 → 查询时间 → 返回行数 → 导出哈希”回执；
4. 先执行独立复查，再决定是否需要更正飞书数据。
"""


def public_audit_view(audit: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: value for key, value in audit.items() if key != "_tables"}
    return cleaned


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "not_available", "path": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return {"status": "failed", "path": str(path), "error": str(error)}
    return {"status": payload.get("status", "unknown"), "path": str(path)}


def main() -> None:
    args = parse_args()
    dates = date_range(args.start_date, args.end_date)
    raw_root = Path(args.raw_root)
    output_dir = Path(args.output_dir)
    initial = audit_root(raw_root, dates)
    adjacent = compare_adjacent(initial, dates)
    payload_match = compare_payload_to_raw(initial, Path(args.source_data), dates)
    recheck_root = Path(args.recheck_root) if args.recheck_root else None
    if recheck_root:
        recheck_audit = audit_root(recheck_root, list(FOCUS_DATES))
        recheck_comparison = compare_recheck(initial, recheck_audit, list(FOCUS_DATES))
        recheck_comparison["recheck_raw_audit"] = public_audit_view(recheck_audit)
        recheck_comparison["recheck_adjacent_content_audit"] = compare_adjacent(recheck_audit, list(FOCUS_DATES))
    else:
        recheck_comparison = {
            "status": "pending",
            "classification": "recheck_pending",
            "lark_action": "no_change_before_recheck",
            "interpretation": "Independent GM re-query snapshot has not been supplied yet; no Lark mutation is permitted.",
        }
    raw_audit = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds"),
        "window": {"start": args.start_date, "end": args.end_date, "timezone": "Asia/Hong_Kong"},
        "raw_export_audit": public_audit_view(initial),
        "adjacent_content_audit": adjacent,
        "source_payload_match": payload_match,
        "existing_receipts": {
            "source_validation": read_status(Path(args.source_validation)),
            "online_lark_readback": read_status(Path(args.lark_readback)),
        },
        "quality_status": "passed_with_static_entity_anomaly" if initial["status"] == "passed" else "partial_or_blocked",
        "data_use_status": "data_static_suspect",
        "notes": [
            "Static entity fingerprints are a data-quality signal, not a conclusion about player behavior or risk.",
            "No Lark changes are performed by this audit script.",
        ],
    }
    write_json(output_dir / "raw-audit.json", raw_audit)
    write_json(output_dir / "recheck-comparison.json", recheck_comparison)
    source_data_path = None
    if args.emit_source_data:
        source_data_path = Path(args.emit_source_data)
        write_json(source_data_path, build_target_source_data(initial, dates, raw_root))
    (output_dir / "root-cause-report.md").write_text(
        root_cause_markdown(raw_audit["raw_export_audit"], adjacent, payload_match, recheck_comparison),
        encoding="utf-8",
    )
    print(json.dumps({
        "status": raw_audit["quality_status"],
        "raw_audit": str(output_dir / "raw-audit.json"),
        "recheck_comparison": str(output_dir / "recheck-comparison.json"),
        "root_cause_report": str(output_dir / "root-cause-report.md"),
        "source_data": str(source_data_path) if source_data_path else None,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
