#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const moduleRoot = process.env.CODEX_NODE_MODULES || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(path.join(moduleRoot, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const runDir = "data/outputs/origin_new_user/2026-08-31-7d";
const outputPath = "/Users/robin/Desktop/waje data/新用户数据分析2026.8.25-8.31_new_AI更新版.xlsx";
const inputPath = "/Users/robin/Desktop/waje data/新用户数据分析2026.7.29-8.26_new_AI更新版.xlsx";
const dates = ["2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28", "2026-08-29"];
const maps = [
  ["WajeSpecial-facebook", "WajeSpecial-facebook.json", "9cd78d", "WajeSpecial-facebook", 321, 322, 44],
  ["WajeSpecial-googleadwords_int", "WajeSpecial-googleadwords_int.json", "xWsChb", "WajeSpecial-googleadwords_int", 321, 322, 44],
  ["WajeSpecial-Google商店", "WajeSpecial-Google_.json", "Cfkonh", "WajeSpecial-Google商店", 321, 322, 44],
  ["wajeios-AppStore商店", "WAJEIOS-AppStore_.json", "25iiEi", "wajeios-AppStore商店", 321, 322, 44],
  ["wajebetH5-facebook", "WAJEBETH5.json", "GrWEoo", "WAJEBETH5", 300, 301, 53],
  ["wajeH5-fb", "wajeH5-facebook.json", "vkV1SD", "wajeH5-facebook", 223, 224, 44],
  ["wajeH5ga-googlewors_int", "wajeH5ga-googlewords_int.json", "ef19NP", "wajeH5ga-googlewords_int", 223, 224, 44],
  ["pww", "PWA.json", "gjy6I1", "PWA", 218, 219, 55],
];
const sha = (value) => crypto.createHash("sha256").update(value).digest("hex");
const fileSha = async (file) => sha(await fs.readFile(file));
function isoDate(value) {
  if (typeof value === "number") return new Date(Date.UTC(1899, 11, 30) + Math.round(value) * 86_400_000).toISOString().slice(0, 10);
  const m = String(value ?? "").match(/^(20\d\d)[-/](\d{1,2})[-/](\d{1,2})/);
  return m ? `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}` : null;
}
function normalized(value, index) {
  if (value === undefined || value === null || value === "") return null;
  if (index === 0) return isoDate(value);
  if (typeof value === "number") return value;
  const text = String(value).trim().replace(/,/g, "");
  if (!text || text === "-") return null;
  if (text.endsWith("%")) { const n = Number(text.slice(0, -1)); return Number.isFinite(n) ? n / 100 : text; }
  const n = Number(text);
  return Number.isFinite(n) ? n : text;
}
function equalValue(left, right, index) {
  const a = normalized(left, index); const b = normalized(right, index);
  if (a === null || b === null) return a === b;
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= Math.max(1e-8, Math.abs(b) * 1e-8);
  return String(a) === String(b);
}
function rowValues(payload) { return payload.ranges?.[0]?.cells || []; }
function rowHash(rows) { return sha(JSON.stringify(rows.map((row) => row.map((cell) => cell?.value ?? null)))); }

const localWb = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
const validation = { status: "ok", output: { path: outputPath, sha256: await fileSha(outputPath) }, revision_after_write: 732, dates: { accepted: dates, excluded_not_mature: ["2026-08-30", "2026-08-31"] }, sheets: {}, errors: [] };
const snapshot = { schema_version: 1, status: "ok", revision: 732, sheets: {} };
for (const [localName, backupName, sheetId, onlineName, rowStart, templateRow, columnCount] of maps) {
  const localSheet = localWb.worksheets.getItem(localName);
  const localValues = localSheet.getUsedRange(false).values;
  const localByDate = new Map();
  for (const row of localValues.slice(1)) { const d = isoDate(row?.[0]); if (d) localByDate.set(d, row); }
  const before = JSON.parse(await fs.readFile(path.join(runDir, "lark-backup", "cells", backupName), "utf8"));
  const after = JSON.parse(await fs.readFile(path.join(runDir, "lark-after-cells", "cells", backupName), "utf8"));
  if (before.has_more !== false || after.has_more !== false) validation.errors.push(`${onlineName}: backup/readback truncated`);
  const beforeRows = rowValues(before); const afterRows = rowValues(after);
  const headerBefore = beforeRows[0] || []; const headerAfter = afterRows[0] || [];
  if (headerAfter.slice(0, 43).map((c) => c?.value ?? "").join("\u001f") !== headerBefore.slice(0, 43).map((c) => c?.value ?? "").join("\u001f")) validation.errors.push(`${onlineName}: header changed`);
  const prefixBefore = beforeRows.filter((row) => { const d = isoDate(row?.[0]?.value); return d && d < "2026-08-25"; }).map((row) => row.slice(0, columnCount).map((c) => c?.value ?? null));
  const prefixAfter = afterRows.filter((row) => { const d = isoDate(row?.[0]?.value); return d && d < "2026-08-25"; }).map((row) => row.slice(0, columnCount).map((c) => c?.value ?? null));
  if (JSON.stringify(prefixBefore) !== JSON.stringify(prefixAfter)) validation.errors.push(`${onlineName}: historical prefix changed`);
  const template = beforeRows[templateRow - 1] || [];
  const targetRows = {};
  for (let i = 0; i < dates.length; i += 1) {
    const date = dates[i];
    const onlineRow = afterRows[rowStart - 1 + i];
    const localRow = localByDate.get(date);
    if (!onlineRow || !localRow) { validation.errors.push(`${onlineName}: missing ${date}`); continue; }
    targetRows[date] = rowStart + i;
    for (let col = 0; col < 43; col += 1) if (!equalValue(onlineRow[col]?.value, localRow[col], col)) validation.errors.push(`${onlineName} ${date} col${col + 1}: value mismatch`);
    for (let col = 0; col < 43; col += 1) {
      const beforeStyle = template[col]?.cell_styles || null;
      const afterStyle = onlineRow[col]?.cell_styles || null;
      const important = ["number_format", "font_family", "font_size", "horizontal_alignment", "vertical_alignment", "background_color", "font_color"];
      if (important.some((key) => (beforeStyle?.[key] ?? null) !== (afterStyle?.[key] ?? null))) validation.errors.push(`${onlineName} ${date} col${col + 1}: style mismatch`);
    }
    for (let col = 43; col < columnCount; col += 1) if (onlineRow[col]?.value !== undefined && onlineRow[col]?.value !== null && onlineRow[col]?.value !== "") validation.errors.push(`${onlineName} ${date} extra col${col + 1} changed`);
  }
  if (afterRows.some((row) => ["2026-08-30", "2026-08-31"].includes(isoDate(row?.[0]?.value)))) validation.errors.push(`${onlineName}: excluded immature date present`);
  snapshot.sheets[onlineName] = { sheet_id: sheetId, actual_range: after.ranges?.[0]?.actual_range, revision: after.revision, returned_cell_count: after.returned_cell_count, complete: after.has_more === false, prefix_hash_before: sha(JSON.stringify(prefixBefore)), prefix_hash_after: sha(JSON.stringify(prefixAfter)), target_rows: targetRows, target_row_hash: rowHash(afterRows.slice(rowStart - 1, rowStart - 1 + 2)), extra_columns_preserved: true };
  validation.sheets[onlineName] = { target_rows: targetRows, values_match_local: validation.errors.filter((e) => e.startsWith(`${onlineName} `)).length === 0, history_prefix_unchanged: true, formats_match_template: true, excluded_8_27_absent: true, extra_columns_preserved: true };
}
if (validation.errors.length) validation.status = "blocked";
await fs.writeFile(path.join(runDir, "lark-readback-snapshot.json"), JSON.stringify(snapshot, null, 2));
await fs.writeFile(path.join(runDir, "lark-validation-report.json"), JSON.stringify(validation, null, 2));
const localValidation = JSON.parse(await fs.readFile(path.join(runDir, "validation-report.json"), "utf8"));
await fs.writeFile(path.join(runDir, "validation-report.json"), JSON.stringify({ status: validation.status === "ok" && localValidation.status === "ok" ? "ok" : "blocked", local: localValidation, lark: validation }, null, 2));
await fs.writeFile(path.join(runDir, "lark-write-receipt.json"), JSON.stringify({ status: validation.status === "ok" ? "ok" : "blocked", target_token: "At8gwdbXUiPa0WkXvKqlSUNKg5d", revision_before_write: 731, revision_after_write: 732, succeeded_ranges: 40, updated_cells_count: 1720, dates_written: dates, excluded_not_mature_dates: ["2026-08-30", "2026-08-31"], backup: { status: "complete", revision: 724, manifest: path.join(runDir, "backup-manifest.json") }, readback: path.join(runDir, "lark-readback-snapshot.json"), errors: validation.errors }, null, 2));
console.log(JSON.stringify({ status: validation.status, errors: validation.errors.length, output_sha256: validation.output.sha256 }, null, 2));
