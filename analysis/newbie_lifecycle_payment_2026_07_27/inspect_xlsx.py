#!/usr/bin/env python3
"""Read-only XLSX inspector using only the Python standard library.

The workspace runtime did not expose third-party spreadsheet readers, so this
script parses the OOXML package directly. It preserves cached formula values
when present and emits a compact, auditable workbook inventory plus previews.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
CELL_REF_RE = re.compile(r"([A-Z]+)(\d+)$")


def text_of(node: ET.Element) -> str:
    return "".join(part.text or "" for part in node.iter(f"{{{NS['main']}}}t"))


def col_index(ref: str) -> int:
    match = CELL_REF_RE.match(ref)
    if not match:
        return 0
    result = 0
    for char in match.group(1):
        result = result * 26 + ord(char) - 64
    return result


def excel_serial_to_iso(value: float) -> str:
    # Excel's 1900 leap-year bug is intentionally mirrored for serial values.
    epoch = dt.datetime(1899, 12, 30)
    parsed = epoch + dt.timedelta(days=value)
    if parsed.time() == dt.time(0, 0):
        return parsed.date().isoformat()
    return parsed.isoformat(sep=" ", timespec="seconds")


def parse_date_styles(archive: zipfile.ZipFile) -> set[int]:
    if "xl/styles.xml" not in archive.namelist():
        return set()
    root = ET.fromstring(archive.read("xl/styles.xml"))
    custom = {
        int(item.attrib["numFmtId"]): item.attrib.get("formatCode", "")
        for item in root.findall("main:numFmts/main:numFmt", NS)
    }
    builtin_dates = set(range(14, 23)) | {45, 46, 47}
    styles: set[int] = set()
    for index, xf in enumerate(root.findall("main:cellXfs/main:xf", NS)):
        num_fmt = int(xf.attrib.get("numFmtId", "0"))
        fmt = custom.get(num_fmt, "").lower()
        is_date = num_fmt in builtin_dates or bool(re.search(r"[dmyhs]", fmt))
        if is_date:
            styles.add(index)
    return styles


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [text_of(item) for item in root.findall("main:si", NS)]


def sheet_locations(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in rels.findall("pkgrel:Relationship", NS)
    }
    locations = []
    for sheet in workbook.findall("main:sheets/main:sheet", NS):
        relation = sheet.attrib[f"{{{NS['rel']}}}id"]
        target = rel_map[relation]
        if target.startswith("/"):
            location = target.lstrip("/")
        else:
            location = str(Path("xl") / target)
        locations.append((sheet.attrib["name"], location))
    return locations


def numeric(value: str) -> Any:
    try:
        float_value = float(value)
    except ValueError:
        return value
    return int(float_value) if float_value.is_integer() else float_value


def read_sheet(
    archive: zipfile.ZipFile,
    location: str,
    shared_strings: list[str],
    date_styles: set[int],
) -> tuple[list[list[Any]], int]:
    root = ET.fromstring(archive.read(location))
    rows: list[list[Any]] = []
    formulas = 0
    for row in root.findall("main:sheetData/main:row", NS):
        cells: dict[int, Any] = {}
        for cell in row.findall("main:c", NS):
            address = cell.attrib.get("r", "")
            column = col_index(address)
            if not column:
                continue
            cell_type = cell.attrib.get("t")
            style = int(cell.attrib.get("s", "0"))
            formula = cell.find("main:f", NS)
            if formula is not None:
                formulas += 1
            value_node = cell.find("main:v", NS)
            raw = value_node.text if value_node is not None and value_node.text is not None else ""
            if cell_type == "s" and raw:
                value: Any = shared_strings[int(raw)]
            elif cell_type == "inlineStr":
                inline = cell.find("main:is", NS)
                value = text_of(inline) if inline is not None else ""
            elif cell_type == "b":
                value = raw == "1"
            elif raw:
                value = numeric(raw)
                # Some summary workbooks reuse date-formatted cell styles for
                # large numeric measures. Guard the Excel serial range so an
                # accidental style assignment cannot corrupt the inspection.
                if style in date_styles and isinstance(value, (int, float)) and 0 < value < 100000:
                    value = excel_serial_to_iso(float(value))
            elif formula is not None:
                value = f"FORMULA:{formula.text or ''}"
            else:
                value = ""
            cells[column] = value
        if cells:
            line = ["" for _ in range(max(cells))]
            for column, value in cells.items():
                line[column - 1] = value
            rows.append(line)
        else:
            rows.append([])
    return rows, formulas


def preview(rows: list[list[Any]], limit: int) -> list[list[Any]]:
    max_cols = max((len(row) for row in rows), default=0)
    return [row + [""] * (max_cols - len(row)) for row in rows[:limit]]


def inspect_workbook(path: Path, preview_rows: int) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        shared_strings = read_shared_strings(archive)
        date_styles = parse_date_styles(archive)
        sheets = []
        for name, location in sheet_locations(archive):
            rows, formulas = read_sheet(archive, location, shared_strings, date_styles)
            non_empty = sum(1 for row in rows if any(value != "" for value in row))
            sheets.append(
                {
                    "name": name,
                    "row_count": len(rows),
                    "non_empty_rows": non_empty,
                    "max_columns": max((len(row) for row in rows), default=0),
                    "formula_cells": formulas,
                    "preview": preview(rows, preview_rows),
                }
            )
    return {"file": path.name, "bytes": path.stat().st_size, "sheets": sheets}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--preview-rows", type=int, default=15)
    parser.add_argument("--list", action="store_true", help="Print compact sheet inventory only.")
    parser.add_argument("--sheet", action="append", default=[], help="Limit JSON output to an exact sheet name; repeatable.")
    args = parser.parse_args()
    reports = [inspect_workbook(path, args.preview_rows) for path in args.files]
    if args.sheet:
        requested = set(args.sheet)
        for report in reports:
            report["sheets"] = [sheet for sheet in report["sheets"] if sheet["name"] in requested]
    if args.list:
        print("file\tsheet\trows\tnon_empty_rows\tmax_columns\tformula_cells")
        for report in reports:
            for sheet in report["sheets"]:
                print(
                    "\t".join(
                        str(value)
                        for value in (
                            report["file"],
                            sheet["name"],
                            sheet["row_count"],
                            sheet["non_empty_rows"],
                            sheet["max_columns"],
                            sheet["formula_cells"],
                        )
                    )
                )
        return
    json.dump(reports, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
