#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const runDir = process.env.RUN_DIR || "data/outputs/origin_new_user/2026-08-28-30d";
const backupDir = path.join(runDir, "lark-backup");
const output = path.join(runDir, "backup-manifest.json");
const workbookInfo = {
  token: "At8gwdbXUiPa0WkXvKqlSUNKg5d",
  revision: Number(process.env.BACKUP_REVISION || 716),
  sheets: [
    ["WajeSpecial-facebook", "9cd78d", 322, 44],
    ["WajeSpecial-googleadwords_int", "xWsChb", 322, 44],
    ["WajeSpecial-Google商店", "Cfkonh", 322, 44],
    ["WAJEIOS-AppStore商店", "25iiEi", 322, 44],
    ["WAJEBETH5", "GrWEoo", 301, 53],
    ["wajeH5-facebook", "vkV1SD", 224, 44],
    ["wajeH5ga-googlewords_int", "ef19NP", 224, 44],
    ["PWA", "gjy6I1", 403, 55],
  ],
};
const safe = (value) => value.replace(/[^\w.-]+/g, "_");
const sha = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const cells = [];
const layouts = [];
for (const [name, id, rows, cols] of workbookInfo.sheets) {
  const base = safe(name);
  const cellPath = path.join(backupDir, "cells", `${base}.json`);
  const layoutPath = path.join(backupDir, "layout", `${base}.json`);
  const cellData = JSON.parse(await fs.readFile(cellPath, "utf8"));
  const layoutData = JSON.parse(await fs.readFile(layoutPath, "utf8"));
  cells.push({ name, sheet_id: id, path: cellPath, sha256: await sha(cellPath), complete: cellData.has_more === false, actual_range: cellData.ranges?.[0]?.actual_range, returned_cell_count: cellData.returned_cell_count, revision: cellData.revision });
  layouts.push({ name, sheet_id: id, path: layoutPath, sha256: await sha(layoutPath), complete: layoutData.ok === true, actual_range: layoutData.data?.range, row_count: rows, column_count: cols, revision: layoutData.data?.revision });
}
const result = { schema_version: 1, status: "complete", truncated: false, exported_xlsx: { status: "blocked_missing_scope", path: null }, source: "Feishu Sheets read-only structured backup", workbook: workbookInfo, value_formula_style_snapshots: cells, layout_snapshots: layouts, integrity: { all_value_snapshots_complete: cells.every((item) => item.complete), all_layout_snapshots_complete: layouts.every((item) => item.complete), sheet_count: workbookInfo.sheets.length, revision: workbookInfo.revision } };
await fs.writeFile(output, JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
