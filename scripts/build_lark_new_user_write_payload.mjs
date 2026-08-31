#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const moduleRoot = process.env.CODEX_NODE_MODULES || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(path.join(moduleRoot, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const outputWorkbookPath = "/Users/robin/Desktop/waje data/新用户数据分析2026.7.29-8.26_new_AI更新版.xlsx";
const runDir = "data/outputs/origin_new_user/2026-08-28-30d";
const acceptedDates = ["2026-08-25", "2026-08-26"];
const sourceColumns = 43;
const localToOnline = {
  "WajeSpecial-facebook": { online: "WajeSpecial-facebook", id: "9cd78d", rowStart: 321, local: "WajeSpecial-facebook", templateRow: 320 },
  "WajeSpecial-googleadwords_int": { online: "WajeSpecial-googleadwords_int", id: "xWsChb", rowStart: 321, local: "WajeSpecial-googleadwords_int", templateRow: 320 },
  "WajeSpecial-Google商店": { online: "WajeSpecial-Google商店", id: "Cfkonh", rowStart: 321, local: "WajeSpecial-Google商店", templateRow: 320 },
  "wajeios-AppStore商店": { online: "WAJEIOS-AppStore商店", id: "25iiEi", rowStart: 321, local: "wajeios-AppStore商店", templateRow: 320 },
  "wajebetH5-facebook": { online: "WAJEBETH5", id: "GrWEoo", rowStart: 300, local: "wajebetH5-facebook", templateRow: 299 },
  "wajeH5-fb": { online: "wajeH5-facebook", id: "vkV1SD", rowStart: 223, local: "wajeH5-fb", templateRow: 222 },
  "wajeH5ga-googlewors_int": { online: "wajeH5ga-googlewords_int", id: "ef19NP", rowStart: 223, local: "wajeH5ga-googlewors_int", templateRow: 222 },
  "pww": { online: "PWA", id: "gjy6I1", rowStart: 218, local: "pww", templateRow: 217 },
};
const backupNames = {
  "WajeSpecial-facebook": "WajeSpecial-facebook.json",
  "WajeSpecial-googleadwords_int": "WajeSpecial-googleadwords_int.json",
  "WajeSpecial-Google商店": "WajeSpecial-Google_.json",
  "wajeios-AppStore商店": "WAJEIOS-AppStore_.json",
  "wajebetH5-facebook": "WAJEBETH5.json",
  "wajeH5-fb": "wajeH5-facebook.json",
  "wajeH5ga-googlewors_int": "wajeH5ga-googlewords_int.json",
  "pww": "PWA.json",
};
const headers = ["日期", "区服", "新增人数", "终身", "首日", "次日", "3日", "4日", "5日", "6日", "7日", "8日", "9日", "10日", "11日", "12日", "13日", "14日", "15日", "30日", "60日", "新增付费率", "新增付费人数", "次留", "3日留", "7日留", "15日留", "30日留", "60日留", "tc比", "tx率", "人均tx金额", "首充付费率", "首充付费人数", "首充次留", "首充3日留", "首充7日留", "首充15日留", "首充30日留", "首充60日留", "首充tc比", "首充tx率", "首充人均tx金额"];
function assert(condition, message) { if (!condition) throw new Error(message); }
function isoDate(value) {
  if (typeof value === "number") return new Date(Date.UTC(1899, 11, 30) + Math.round(value) * 86_400_000).toISOString().slice(0, 10);
  const m = String(value ?? "").match(/^(20\d\d)[-/](\d{1,2})[-/](\d{1,2})/);
  return m ? `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}` : null;
}
function alpha(index) { let n = index + 1; let s = ""; while (n) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); } return s; }
const localWb = await SpreadsheetFile.importXlsx(await FileBlob.load(outputWorkbookPath));
const writes = [];
const mappingReceipt = {};
for (const [localName, map] of Object.entries(localToOnline)) {
  const localSheet = localWb.worksheets.getItem(localName);
  const localValues = localSheet.getUsedRange(false).values;
  assert(JSON.stringify(localValues[0].slice(0, sourceColumns)) === JSON.stringify(headers), `${localName}: local header mismatch`);
  const localRows = new Map();
  for (let i = 1; i < localValues.length; i += 1) {
    const date = isoDate(localValues[i]?.[0]);
    if (date) localRows.set(date, localValues[i]);
  }
  const backup = JSON.parse(await fs.readFile(path.join(runDir, "lark-backup", "cells", backupNames[localName]), "utf8"));
  const onlineCells = backup.ranges[0].cells;
  const template = onlineCells[map.templateRow - 1];
  assert(template && template.length >= sourceColumns, `${map.online}: template row ${map.templateRow} missing`);
  const firstRowCells = [];
  for (const date of acceptedDates) {
    const row = localRows.get(date);
    assert(row, `${localName}: local output missing ${date}`);
    const cells = [];
    for (let col = 0; col < sourceColumns; col += 1) {
      const style = template[col]?.cell_styles;
      const border = template[col]?.border_styles;
      // `value: null` is not accepted by the Sheets API.  For a source blank
      // (all matured rows still contain future retention blanks after the
      // zero-clean step), omit the content field and only carry the template
      // style; the pre-inserted target row is already empty.
      const cell = {};
      if (row[col] !== undefined && row[col] !== null && row[col] !== "") cell.value = row[col];
      if (style) cell.cell_styles = style;
      if (border) cell.border_styles = border;
      cells.push(cell);
    }
    const rowNumber = map.rowStart + (date === acceptedDates[0] ? 0 : 1);
    writes.push({ sheet_id: map.id, range: `A${rowNumber}:AQ${rowNumber}`, cells: [cells] });
    firstRowCells.push({ date, row_number: rowNumber, source_row: row.slice(0, sourceColumns), style_template_row: map.templateRow });
  }
  mappingReceipt[localName] = { online_sheet: map.online, online_sheet_id: map.id, local_sheet: localName, local_header_count: sourceColumns, target_rows: firstRowCells.map((r) => r.row_number), dates: acceptedDates, source_rows: firstRowCells };
}
await fs.writeFile(path.join(runDir, "lark-writes.json"), JSON.stringify(writes, null, 2));
await fs.writeFile(path.join(runDir, "lark-alias-mapping.json"), JSON.stringify({ status: "validated_by_header_and_date_boundary", mappings: mappingReceipt }, null, 2));
await fs.writeFile(path.join(runDir, "lark-write-plan.json"), JSON.stringify({ status: "ready_for_execute", target_token: "At8gwdbXUiPa0WkXvKqlSUNKg5d", target_revision_before_write_expected: 723, dates: acceptedDates, source_columns: sourceColumns, range_end: "AQ", writes: writes.map((item) => ({ sheet_id: item.sheet_id, range: item.range, cell_count: item.cells[0].length })), excluded_not_mature_dates: ["2026-08-27"], extra_columns_preserved: true }, null, 2));
console.log(JSON.stringify({ status: "ok", writes: writes.length, cells: writes.reduce((n, w) => n + w.cells[0].length, 0), files: [path.join(runDir, "lark-writes.json"), path.join(runDir, "lark-alias-mapping.json"), path.join(runDir, "lark-write-plan.json")] }, null, 2));
