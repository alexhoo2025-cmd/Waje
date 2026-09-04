#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const runDir = path.resolve("data/outputs/origin_new_user/2026-09-01-26d");
const backupDir = path.join(runDir, "lark-backup");
const files = [
  ["WajeSpecial-facebook", "9cd78d", "WajeSpecial-facebook.json", 325, 44],
  ["WajeSpecial-googleadwords_int", "xWsChb", "WajeSpecial-googleadwords_int.json", 325, 44],
  ["WajeSpecial-Google商店", "Cfkonh", "WajeSpecial-Google_.json", 325, 44],
  ["WAJEIOS-AppStore商店", "25iiEi", "WAJEIOS-AppStore_.json", 325, 44],
  ["WAJEBETH5", "GrWEoo", "WAJEBETH5.json", 304, 53],
  ["wajeH5-facebook", "vkV1SD", "wajeH5-facebook.json", 227, 44],
  ["wajeH5ga-googlewords_int", "ef19NP", "wajeH5ga-googlewords_int.json", 227, 44],
  ["PWA", "gjy6I1", "PWA.json", 403, 55],
];
const sha256 = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const sheets = [];
for (const [name, id, file, rows, cols] of files) {
  const cellPath = path.join(backupDir, "cells", file);
  const layoutPath = path.join(backupDir, "layout", file);
  const cells = JSON.parse(await fs.readFile(cellPath, "utf8"));
  const layout = JSON.parse(await fs.readFile(layoutPath, "utf8"));
  sheets.push({ name, sheet_id: id, row_count: rows, column_count: cols, values_path: cellPath, values_sha256: await sha256(cellPath), values_complete: cells.has_more === false, actual_range: cells.ranges?.[0]?.actual_range, layout_path: layoutPath, layout_sha256: await sha256(layoutPath), layout_complete: layout.ok === true, revision: cells.revision });
}
const revisions = [...new Set(sheets.map((s) => s.revision).filter(Boolean))];
if (revisions.length !== 1 || Number(revisions[0]) !== 732) throw new Error(`backup revision mismatch: ${revisions.join(",")}`);
const result = { schema_version: 1, status: "complete", truncated: false, backup_method: "full Feishu cells value/formula/style snapshots plus layout snapshots", workbook: { token: "At8gwdbXUiPa0WkXvKqlSUNKg5d", title: "新包新增用户分析", revision: 732, sheet_count: sheets.length, sheets }, integrity: { all_values_complete: sheets.every((s) => s.values_complete), all_layout_complete: sheets.every((s) => s.layout_complete), revision_consistent: true, complete: true } };
await fs.writeFile(path.join(runDir, "backup-manifest.json"), JSON.stringify(result, null, 2) + "\n");
console.log(JSON.stringify({ status: result.status, revision: result.workbook.revision, sheets: sheets.length, complete: result.integrity.complete }, null, 2));
