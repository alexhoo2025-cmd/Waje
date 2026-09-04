#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
DATA = json.loads((ROOT / "game_code_name_mapping.json").read_text("utf-8"))
KNOWLEDGE = PROJECT / "knowledge/02-数据/Waje-游戏代码与名称统一映射表-2026-08-31.md"
README = PROJECT / "knowledge/README.md"
ASSET_MAP = PROJECT / "knowledge/00-索引/资产地图.md"

checks = []


def check(name: str, ok: bool, evidence) -> None:
    checks.append({"name": name, "ok": bool(ok), "evidence": evidence})


summary = DATA["summary"]
check("source_revision", DATA["source"]["revision"] == 609, DATA["source"]["revision"])
check("record_count", summary["valid_records"] == 596, summary["valid_records"])
check("unique_ids", summary["unique_game_ids"] == 593, summary["unique_game_ids"])
check("no_missing_ids_names", summary["missing_name_or_id_rows"] == 0, summary["missing_name_or_id_rows"])
check("provider_reconciliation", sum(summary["provider_counts"].values()) == 596, summary["provider_counts"])
check("lightweight_cross_sheet", all(row["status"] == "matched" for row in DATA["lightweight_cross_sheet_check"]), DATA["lightweight_cross_sheet_check"])
check("limbo_keno_technical_mapping", DATA["known_analysis_conflict"]["canonical_for_analysis"] == {"Limbo": "9008", "Keno": "9010"}, DATA["known_analysis_conflict"])
check("duplicate_name_conflicts", set(DATA["mapping_conflicts"]["duplicate_names"]) == {"Gold Rush", "Limbo", "Keno"}, DATA["mapping_conflicts"]["duplicate_names"])

with (ROOT / "game_code_name_mapping.csv").open(encoding="utf-8") as fh:
    csv_rows = list(csv.DictReader(fh))
check("csv_rows", len(csv_rows) == 596, len(csv_rows))

text = KNOWLEDGE.read_text("utf-8")
check("knowledge_terms", all(x in text for x in ["PP和Tada均为联运厂商缩写", "Limbo | 9008", "Keno | 9010"]), "terminology and technical mapping")
check("knowledge_links", KNOWLEDGE.name in README.read_text("utf-8") and KNOWLEDGE.stem in ASSET_MAP.read_text("utf-8"), "README and asset map")

payload = {"status": "passed" if all(row["ok"] for row in checks) else "failed", "checks": checks}
(ROOT / "validation_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "checks": len(checks), "failed": [r["name"] for r in checks if not r["ok"]]}, ensure_ascii=False))
raise SystemExit(0 if payload["status"] == "passed" else 1)
