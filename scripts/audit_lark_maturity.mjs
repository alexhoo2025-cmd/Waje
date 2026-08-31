#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const runDir = path.resolve(root, "data/outputs/lark_quality/2026-08-19-wajeH5-fb-maturity-audit");
const dataFile = path.resolve(root, "data/outputs/lark_format/2026-08-19-zero-scale/newuser-table-after.json");
const logicalNames = ["WajeSpecial-facebook", "WajeSpecial-googleadwords_int", "WajeSpecial-Google商店", "PAWAJEIOS-AppStore商店", "PAWAJEBETH5", "wajeH5-fb", "wajeH5ga-googlewords_int", "PWA"];
const ids = { "WajeSpecial-facebook": "9cd78d", "WajeSpecial-googleadwords_int": "xWsChb", "WajeSpecial-Google商店": "Cfkonh", "PAWAJEIOS-AppStore商店": "25iiEi", PAWAJEBETH5: "GrWEoo", "wajeH5-fb": "vkV1SD", "wajeH5ga-googlewords_int": "ef19NP", PWA: "gjy6I1" };
const col = (letters) => { let value = 0; for (const c of letters) value = value * 26 + c.charCodeAt(0) - 64; return value - 1; };
const letters = (index) => { let value = index + 1; let out = ""; while (value > 0) { const rem = (value - 1) % 26; out = String.fromCharCode(65 + rem) + out; value = Math.floor((value - 1) / 26); } return out; };
const serialDate = (value) => new Date(Date.UTC(1899, 11, 30) + Number(value) * 86400000).toISOString().slice(0, 10);
const addDays = (date, days) => new Date(Date.parse(`${date}T00:00:00Z`) + days * 86400000).toISOString().slice(0, 10);
const isBlank = (value) => value === null || value === undefined || value === "";
const isDataDate = (value) => typeof value === "number" && Number.isFinite(value) && value >= 20000;
const normalize = (value) => String(value ?? "").replace(/[\s\n\r]+/g, "").trim();

const payload = JSON.parse(await fs.readFile(dataFile, "utf8"));
const issues = [];
const sheets = [];
const maturityFields = [
  ["F", "次日", 1], ["G", "3日", 3], ["H", "4日", 4], ["I", "5日", 5], ["J", "6日", 6], ["K", "7日", 7], ["L", "8日", 8], ["M", "9日", 9], ["N", "10日", 10], ["O", "11日", 11], ["P", "12日", 12], ["Q", "13日", 13], ["R", "14日", 14], ["S", "15日", 15], ["T", "30日", 30], ["U", "60日", 60],
  ["X", "次留", 1], ["Y", "3日留", 3], ["Z", "7日留", 7], ["AA", "15日留", 15], ["AB", "30日留", 30], ["AC", "60日留", 60],
  ["AI", "首充次留", 1], ["AJ", "首充3日留", 3], ["AK", "首充7日留", 7], ["AL", "首充15日留", 15], ["AM", "首充30日留", 30], ["AN", "首充60日留", 60],
];
for (let sheetIndex = 0; sheetIndex < logicalNames.length; sheetIndex += 1) {
  const logicalName = logicalNames[sheetIndex];
  const sourceSheet = payload.sheets[sheetIndex];
  const rows = sourceSheet.data;
  const dataRows = rows.map((values, offset) => ({ row: offset + 2, values, date: isDataDate(values[0]) ? serialDate(values[0]) : null })).filter((item) => item.date);
  const asOf = dataRows.map((item) => item.date).sort().at(-1);
  if (!asOf) throw new Error(`${logicalName}: no valid date rows`);
  const headers = sourceSheet.columns;
  const sheetIssues = [];
  for (const item of dataRows) {
    for (const [column, fallbackHeader, days] of maturityFields) {
      const index = col(column);
      const value = item.values[index];
      if (isBlank(value)) continue;
      const matureOn = addDays(item.date, days);
      if (matureOn <= asOf) continue;
      const issue = { sheet: logicalName, sheet_id: ids[logicalName], cell: `${column}${item.row}`, row: item.row, date: item.date, field: headers[index] || fallbackHeader, column, maturity_days: days, mature_on: matureOn, as_of: asOf, value, status: "immature_statistical_window", action: "clear_value" };
      issues.push(issue); sheetIssues.push(issue);
    }
  }
  sheets.push({ sheet: logicalName, sheet_id: ids[logicalName], source_sheet_name: sourceSheet.name, as_of: asOf, data_rows: { first: dataRows[0]?.row, last: dataRows.at(-1)?.row, count: dataRows.length }, issue_count: sheetIssues.length, affected_fields: [...new Set(sheetIssues.map((item) => item.field))] });
}

const ranges = [];
for (const sheet of logicalNames) {
  for (const field of maturityFields) {
    const column = field[0];
    const rows = issues.filter((item) => item.sheet === sheet && item.column === column).map((item) => item.row).sort((a, b) => a - b);
    for (let start = 0; start < rows.length;) {
      let end = start;
      while (end + 1 < rows.length && rows[end + 1] === rows[end] + 1) end += 1;
      ranges.push(`${sheet}!${column}${rows[start]}:${column}${rows[end]}`);
      start = end + 1;
    }
  }
}
await fs.mkdir(runDir, { recursive: true });
await fs.writeFile(path.join(runDir, "maturity-audit.json"), JSON.stringify({ generated_at: new Date().toISOString(), source_snapshot: dataFile, rule: "clear a maturity field when cohort_date + maturity_days > sheet_max_date", issue_count: issues.length, sheets, issues }, null, 2));
await fs.writeFile(path.join(runDir, "maturity-clear-ranges.json"), JSON.stringify({ generated_at: new Date().toISOString(), ranges }, null, 2));
await fs.writeFile(path.join(runDir, "maturity-dry-run.json"), JSON.stringify({ generated_at: new Date().toISOString(), issue_count: issues.length, clear_range_count: ranges.length, sheets }, null, 2));
console.log(JSON.stringify({ status: "ok", issue_count: issues.length, clear_range_count: ranges.length, sheets }));
