#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source_workbook.json"
SOURCE_URL = "https://ksg964l11fam.sg.larksuite.com/wiki/NgzMwaILDiFAYck89lrl0vOzgyg?sheet=q2QhIW"
REVISION = 609

payload = json.loads(SOURCE.read_text("utf-8"))
sheets = {sheet["name"]: sheet for sheet in payload["sheets"]}


def rows_with_header(sheet_name: str) -> tuple[list[str], list[list]]:
    data = sheets[sheet_name]["data"]
    return [str(x or "").strip() for x in data[0]], data[1:]


headers, source_rows = rows_with_header("游戏总表")
records = []
missing = []
for row_no, row in enumerate(source_rows, start=2):
    padded = list(row) + [None] * (len(headers) - len(row))
    item = {headers[i]: padded[i] for i in range(len(headers))}
    name = str(item.get("游戏名称") or "").strip()
    game_id = str(item.get("游戏ID") or "").strip()
    if not name or not game_id:
        missing.append({"row": row_no, "game_name": name, "game_id": game_id})
        continue
    records.append({
        "game_id": game_id,
        "game_name": name,
        "game_source": str(item.get("游戏来源") or "").strip(),
        "provider": str(item.get("游戏提供商") or "").strip(),
        "game_type": str(item.get("游戏类型") or "").strip(),
        "game_size_mb": item.get("游戏体量(m)"),
        "resource_size": str(item.get("资源大小") or "").strip(),
        "theme": str(item.get("游戏主题") or "").strip(),
        "link_type": str(item.get("连接方式") or "").strip(),
        "volatility": str(item.get("波动性") or "").strip(),
        "rtp": item.get("RTP"),
        "free_player_allowed": str(item.get("免费玩家可玩") or "").strip(),
        "in_package": str(item.get("是否包内游戏") or "").strip(),
        "source_row": row_no,
    })

id_groups: dict[str, list[dict]] = defaultdict(list)
name_groups: dict[str, list[dict]] = defaultdict(list)
for row in records:
    id_groups[row["game_id"]].append(row)
    name_groups[row["game_name"].casefold()].append(row)

duplicate_ids = {
    game_id: sorted({f"{r['game_name']}|{r['provider']}" for r in rows})
    for game_id, rows in id_groups.items()
    if len({(r["game_name"], r["provider"]) for r in rows}) > 1
}
duplicate_names = {
    rows[0]["game_name"]: sorted({r["game_id"] for r in rows})
    for rows in name_groups.values()
    if len({r["game_id"] for r in rows}) > 1
}

light_headers, light_rows = rows_with_header("轻量化游戏")
light_mapping = []
for row in light_rows:
    if not row or not row[0] or not row[1]:
        continue
    light_mapping.append({
        "game_name": str(row[0]).strip(),
        "game_id": str(row[1]).strip(),
        "game_size": row[2] if len(row) > 2 else None,
        "link_type": row[3] if len(row) > 3 else None,
    })

cross_sheet = []
for item in light_mapping:
    matched = id_groups.get(item["game_id"], [])
    cross_sheet.append({
        **item,
        "game_total_names": sorted({r["game_name"] for r in matched}),
        "status": "matched" if any(r["game_name"].casefold() == item["game_name"].casefold() for r in matched) else "mismatch",
    })

provider_counts = Counter(row["provider"] or "未标注" for row in records)
source_counts = Counter(row["game_source"] or "未标注" for row in records)

fieldnames = [
    "game_id", "game_name", "game_source", "provider", "game_type",
    "game_size_mb", "resource_size", "theme", "link_type", "volatility",
    "rtp", "free_player_allowed", "in_package", "source_row",
]
with (ROOT / "game_code_name_mapping.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

result = {
    "schema_version": 1,
    "source": {
        "url": SOURCE_URL,
        "revision": REVISION,
        "workbook_sheets": [sheet["name"] for sheet in payload["sheets"]],
        "control_sheet": "游戏总表",
    },
    "terminology": {
        "PP": "联运厂商缩写",
        "Tada": "联运厂商缩写",
        "自研": "Waje自研游戏",
    },
    "summary": {
        "valid_records": len(records),
        "unique_game_ids": len(id_groups),
        "unique_game_names": len(name_groups),
        "missing_name_or_id_rows": len(missing),
        "duplicate_id_conflicts": len(duplicate_ids),
        "duplicate_name_conflicts": len(duplicate_names),
        "provider_counts": dict(provider_counts.most_common()),
        "source_counts": dict(source_counts.most_common()),
    },
    "lightweight_games": light_mapping,
    "lightweight_cross_sheet_check": cross_sheet,
    "mapping_conflicts": {
        "duplicate_ids": duplicate_ids,
        "duplicate_names": duplicate_names,
        "missing_rows": missing,
    },
    "technical_source": {
        "url": "https://ksg964l11fam.sg.larksuite.com/wiki/ZTvowT9HOiajFHkpwFbl3RjPgub",
        "revision": 790,
        "owner": "技术部",
        "rule": "自研轻量化游戏ID范围(9000,9200)，Ares玩法ID=9110000+gameId",
    },
    "technical_mapping": {
        "CoinFlip": "9001",
        "ColorDice": "9003",
        "Whot-h5": "9006",
        "Limbo": "9008",
        "Cash": "9009",
        "Keno": "9010",
        "Hilo": "9011",
        "Tower": "9013",
        "FiveCard": "9015",
        "Plinko": "9016",
        "Classic Dice": "9017",
        "Mines": "9018",
    },
    "known_analysis_conflict": {
        "product_sheet_mapping": {"Limbo": "9010", "Keno": "9008"},
        "technical_mapping": {"Limbo": "9008", "Keno": "9010"},
        "canonical_for_analysis": {"Limbo": "9008", "Keno": "9010"},
        "status": "technical_mapping_confirmed_product_sheet_needs_correction",
    },
    "top_games": [
        {"game_name": "Whot", "game_id": "6001", "status": "certified_game_total"},
        {"game_name": "Limbo", "game_id": "9008", "status": "certified_technical_mapping"},
        {"game_name": "CoinFlip", "game_id": "9001", "status": "certified_game_total"},
        {"game_name": "Keno", "game_id": "9010", "status": "certified_technical_mapping"},
        {"game_name": "ColorDice", "game_id": "9003", "status": "certified_game_total"},
        {"game_name": "Hilo", "game_id": "9011", "status": "certified_technical_mapping"},
        {"game_name": "Plinko", "game_id": "9016", "status": "certified_technical_mapping"},
        {"game_name": "Tower", "game_id": "9013", "status": "certified_technical_mapping"},
        {"game_name": "Bottle spin", "game_id": "2003", "status": "certified_as_转瓶子"},
    ],
    "top_games_evidence": [
        "top_games_reference_1.png",
        "top_games_reference_2.png",
    ],
}
(ROOT / "game_code_name_mapping.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
(ROOT / "ingestion_receipt.json").write_text(json.dumps({
    "status": "ok",
    "source_revision": REVISION,
    "records": len(records),
    "csv": "game_code_name_mapping.csv",
    "json": "game_code_name_mapping.json",
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(result["summary"], ensure_ascii=False))
