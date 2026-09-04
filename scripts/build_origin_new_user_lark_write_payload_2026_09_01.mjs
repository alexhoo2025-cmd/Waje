#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const MODULE_ROOT = "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(path.join(MODULE_ROOT, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const runDir = path.resolve(process.env.RUN_DIR || "data/outputs/origin_new_user/2026-09-01-26d");
const localPath = process.env.LOCAL_PATH || "/Users/robin/Desktop/waje data/新用户数据分析2026.8.6-8.31_new_AI更新版_Origin复核清零.xlsx";
const sourcePath = process.env.SOURCE_PATH || path.join(runDir, "source-data.json");
const backupDir = path.resolve(process.env.BACKUP_DIR || path.join(runDir, "lark-backup", "cells"));
const acceptedDates = String(process.env.ACCEPTED_DATES || Array.from({ length: 25 }, (_, i) => new Date(Date.parse("2026-08-06T00:00:00Z") + i * 86400000).toISOString().slice(0, 10)).join(",")).split(",").map((date) => date.trim()).filter(Boolean);
const excludedDates = String(process.env.EXCLUDED_DATES || "2026-08-31").split(",").map((date) => date.trim()).filter(Boolean);
const expectedRevision = Number(process.env.EXPECTED_REVISION || "732");
const sourceColumns = 43;
const headers = ["日期", "区服", "新增人数", "终身", "首日", "次日", "3日", "4日", "5日", "6日", "7日", "8日", "9日", "10日", "11日", "12日", "13日", "14日", "15日", "30日", "60日", "新增付费率", "新增付费人数", "次留", "3日留", "7日留", "15日留", "30日留", "60日留", "tc比", "tx率", "人均tx金额", "首充付费率", "首充付费人数", "首充次留", "首充3日留", "首充7日留", "首充15日留", "首充30日留", "首充60日留", "首充tc比", "首充tx率", "首充人均tx金额"];
const maps = [
  ["WajeSpecial-facebook", "WajeSpecial-facebook", "9cd78d", "WajeSpecial-facebook.json", 44],
  ["WajeSpecial-googleadwords_int", "WajeSpecial-googleadwords_int", "xWsChb", "WajeSpecial-googleadwords_int.json", 44],
  ["WajeSpecial-Google商店", "WajeSpecial-Google商店", "Cfkonh", "WajeSpecial-Google_.json", 44],
  ["wajeios-AppStore商店", "WAJEIOS-AppStore商店", "25iiEi", "WAJEIOS-AppStore_.json", 44],
  ["wajebetH5-facebook", "WAJEBETH5", "GrWEoo", "WAJEBETH5.json", 53],
  ["wajeH5-fb", "wajeH5-facebook", "vkV1SD", "wajeH5-facebook.json", 44],
  ["wajeH5ga-googlewors_int", "wajeH5ga-googlewords_int", "ef19NP", "wajeH5ga-googlewords_int.json", 44],
  ["pww", "PWA", "gjy6I1", "PWA.json", 55],
];
const sha = (v) => crypto.createHash("sha256").update(JSON.stringify(v)).digest("hex");
const iso = (value) => {
  if (typeof value === "number") return new Date(Date.UTC(1899, 11, 30) + Math.round(value) * 86400000).toISOString().slice(0, 10);
  const m = String(value ?? "").trim().replaceAll("/", "-").match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  return m ? `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}` : null;
};
const serial = (date) => (Date.parse(`${date}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 86400000;
const normalized = (value) => {
  if (value === null || value === undefined || String(value).trim() === "") return null;
  if (typeof value === "number") return value;
  const text = String(value).trim().replaceAll(",", "");
  if (text.endsWith("%")) { const n = Number(text.slice(0, -1)); return Number.isFinite(n) ? n / 100 : text; }
  const n = Number(text); return Number.isFinite(n) ? n : text;
};
const isZero = (value) => { const n = normalized(value); return typeof n === "number" && n === 0; };
const isBlank = (value) => value === null || value === undefined || String(value).trim() === "";
const alpha = (index) => { let n = index + 1; let out = ""; while (n > 0) { const r = (n - 1) % 26; out = String.fromCharCode(65 + r) + out; n = Math.floor((n - 1) / 26); } return out; };
function assert(condition, message) { if (!condition) throw new Error(message); }
function targetRowsFromBackup(payload) {
  const cells = payload.ranges?.[0]?.cells || [];
  const rows = [];
  for (let i = 1; i < cells.length; i += 1) {
    const d = iso(cells[i]?.[0]?.value);
    if (d) rows.push({ row: i + 1, values: cells[i].map((c) => c?.value ?? "") });
  }
  return rows;
}
function consecutiveGroups(items) {
  const sorted = [...items].sort((a, b) => a.row - b.row);
  const groups = [];
  for (const item of sorted) {
    const last = groups.at(-1);
    if (!last || item.row !== last.end + 1) groups.push({ start: item.row, end: item.row, items: [item] });
    else { last.end = item.row; last.items.push(item); }
  }
  return groups;
}
const source = JSON.parse(await fs.readFile(sourcePath, "utf8"));
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(localPath));
const writes = [];
const alias = {};
const zeroLedger = [];
for (const [localName, onlineName, sheetId, backupFile] of maps) {
  const localSheet = wb.worksheets.getItem(localName);
  const values = localSheet.getUsedRange(false).values;
  assert(values[0]?.length >= 44, `${localName}: local workbook is not 44 columns`);
  assert(JSON.stringify(values[0].slice(0, sourceColumns)) === JSON.stringify(headers), `${localName}: local header mismatch`);
  const localByDate = new Map();
  for (const row of values.slice(1)) { const d = iso(row?.[0]); if (d) { assert(!localByDate.has(d), `${localName}: duplicate local date ${d}`); localByDate.set(d, row); } }
  for (const d of acceptedDates) assert(localByDate.has(d), `${localName}: local output missing ${d}`);
  const backup = JSON.parse(await fs.readFile(path.join(backupDir, backupFile), "utf8"));
  assert(backup.has_more === false, `${onlineName}: backup truncated`);
  const targetRows = targetRowsFromBackup(backup);
  const targetByDate = new Map();
  for (const item of targetRows) { const d = iso(item.values[0]); if (targetByDate.has(d)) throw new Error(`${onlineName}: duplicate backup date ${d}`); targetByDate.set(d, item.row); }
  const existingAssignments = acceptedDates.filter((date) => targetByDate.has(date)).map((date) => ({ date, row: targetByDate.get(date), local: localByDate.get(date), existing: true }));
  const missingDates = acceptedDates.filter((date) => !targetByDate.has(date));
  for (const date of acceptedDates) assert(localByDate.has(date), `${localName}: local output missing ${date}`);
  const lastDataRow = Math.max(...targetRows.map((x) => x.row));
  const appendAssignments = missingDates.map((date, i) => ({ date, row: lastDataRow + i + 1, local: localByDate.get(date), existing: false }));
  const assignments = [...existingAssignments, ...appendAssignments];
  const dataGroups = consecutiveGroups(existingAssignments);
  for (const group of dataGroups) {
    const cells = group.items.map((item) => {
      const row = item.local;
      const startIndex = 1; // B onward
      const endIndex = sourceColumns;
      return row.slice(startIndex, endIndex).map((value) => ({ value: isBlank(value) ? "" : value }));
    });
    writes.push({ sheet_id: sheetId, range: `B${group.start}:AQ${group.end}`, cells });
  }
  for (const group of consecutiveGroups(appendAssignments)) {
    writes.push({ sheet_id: sheetId, range: `A${group.start}:AQ${group.end}`, cells: group.items.map((item) => [[{ value: serial(item.date) }, ...item.local.slice(1, sourceColumns).map((value) => ({ value: isBlank(value) ? "" : value }))]][0]) });
  }
  const rawRows = source.sheets[localName].rows;
  const rawByDate = new Map(rawRows.map((r) => [iso(r[0]), r]));
  for (const item of assignments) {
    const raw = rawByDate.get(item.date); const local = item.local;
    for (let col = 2; col < sourceColumns; col += 1) {
      if (isZero(raw[col]) && isBlank(local[col])) zeroLedger.push({ local_sheet: localName, online_sheet: onlineName, sheet_id: sheetId, date: item.date, cell: `${alpha(col)}${item.row}`, column_index: col + 1, header: headers[col], source_value: raw[col], output_value: "", action: "clear_numeric_zero_to_blank" });
    }
  }
  alias[localName] = { online_sheet: onlineName, online_sheet_id: sheetId, source_mapping: source.sheets[localName].mapping, accepted_dates: acceptedDates, target_rows: assignments.map((x) => ({ date: x.date, row: x.row, existing: x.existing })), source_columns: sourceColumns, online_total_columns: backup.ranges?.[0]?.cells?.[0]?.length, extra_columns_preserved: true };
}
await fs.writeFile(path.join(runDir, "lark-writes.json"), JSON.stringify(writes, null, 2) + "\n");
await fs.writeFile(path.join(runDir, "lark-alias-mapping.json"), JSON.stringify({ schema_version: 1, status: "validated_by_sheet_id_header_date_and_source_mapping", mappings: alias }, null, 2) + "\n");
await fs.writeFile(path.join(runDir, "zero-ledger.json"), JSON.stringify({ schema_version: 1, status: "ready_for_online_clear", scope: "accepted_dates_metric_columns_only", count: zeroLedger.length, entries: zeroLedger }, null, 2) + "\n");
await fs.writeFile(path.join(runDir, "lark-write-plan.json"), JSON.stringify({ schema_version: 1, status: "ready_for_execute", target_token: "At8gwdbXUiPa0WkXvKqlSUNKg5d", target_revision_before_write_expected: expectedRevision, source_workbook: localPath, source_json: sourcePath, accepted_dates: acceptedDates, excluded_not_mature_dates: excludedDates, insertions: maps.map(([localName, onlineName, id]) => ({ local_sheet: localName, online_sheet: onlineName, sheet_id: id, position: alias[localName].target_rows.filter((item) => !item.existing)[0]?.row || null, insert_count: alias[localName].target_rows.filter((item) => !item.existing).length })).filter((item) => item.insert_count > 0), write_regions: writes.map((w) => ({ sheet_id: w.sheet_id, range: w.range, rows: w.cells.length, columns: w.cells[0]?.length || 0 })), zero_ledger_count: zeroLedger.length, extra_columns_preserved: true }, null, 2) + "\n");
console.log(JSON.stringify({ status: "ok", writes: writes.length, cells: writes.reduce((n, w) => n + w.cells.reduce((x, row) => x + row.length, 0), 0), zero_ledger_count: zeroLedger.length, accepted_dates: acceptedDates.length }, null, 2));
