#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";

const args = Object.fromEntries(process.argv.slice(2).reduce((pairs, token, index, all) => {
  if (!token.startsWith("--")) return pairs;
  const next = all[index + 1];
  pairs.push([token.slice(2), next && !next.startsWith("--") ? next : true]);
  return pairs;
}, []));
const inputDir = args["input-dir"];
const outputDir = args["output-dir"];
if (!inputDir || !outputDir) throw new Error("Require --input-dir and --output-dir");

const columnLetter = (index) => {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
};
const normalizeHeader = (value) => String(value ?? "").replace(/[\s\n\r]+/g, "").trim();
const dateLike = (value) => {
  if (typeof value === "number") return Number.isFinite(value) && value >= 20_000;
  const text = String(value ?? "").trim();
  if (/^\d{4}[/-]\d{1,2}[/-]\d{1,2}/.test(text)) return true;
  return /^\d{5}$/.test(text) && Number(text) >= 20_000;
};
const numericZero = (value) => {
  if (typeof value === "number") return Number.isFinite(value) && value === 0;
  if (typeof value !== "string") return false;
  return /^[-+]?0+(?:\.0+)?%?$/.test(value.trim());
};
const numericValue = (value) => {
  if (typeof value === "number") return Number.isFinite(value);
  if (typeof value !== "string") return false;
  const text = value.trim();
  return /^[-+]?(?:\d+|\d*\.\d+)%?$/.test(text);
};
const dimensionHeaders = new Set(["日期", "区服", "游戏类型", "生命周期", "生命周期"]);

const readTable = async (file) => JSON.parse(await fs.readFile(path.join(inputDir, file), "utf8"));
const withRows = (table, startRow) => {
  const sheet = table.sheets[0];
  return {
    name: sheet.name,
    columns: sheet.columns,
    dtypes: sheet.dtypes || {},
    rows: sheet.data.map((values, index) => ({ row: startRow + index, values })),
  };
};

const newUser = await readTable("newuser-table.json");
const lifecycleSummary = withRows(await readTable("lifecycle-summary-table.json"), 2);
const lifecycleActive = withRows(await readTable("lifecycle-active-table.json"), 2);

const lifecycleDetailFirst = withRows(await readTable("lifecycle-detail-1.json"), 2);
const lifecycleDetailSecond = withRows(await readTable("lifecycle-detail-2.json"), 1501);
const lifecycleDetail = {
  name: "原始详细奖池",
  columns: lifecycleDetailFirst.columns,
  dtypes: lifecycleDetailFirst.dtypes,
  rows: [...lifecycleDetailFirst.rows, ...lifecycleDetailSecond.rows],
};

const lifecycleGameFirst = withRows(await readTable("lifecycle-game-1.json"), 2);
const lifecycleGameSecond = withRows(await readTable("lifecycle-game-2.json"), 2501);
const lifecycleGame = {
  name: "生命周期奖池分游戏汇总",
  columns: lifecycleGameFirst.columns,
  dtypes: lifecycleGameFirst.dtypes,
  rows: [...lifecycleGameFirst.rows, ...lifecycleGameSecond.rows],
};

const normalizedSheets = [
  ...newUser.sheets.map((sheet) => ({
    name: sheet.name,
    columns: sheet.columns,
    dtypes: sheet.dtypes || {},
    rows: sheet.data.map((values, index) => ({ row: index + 2, values })),
    workbook: "new_user",
  })),
  { ...lifecycleSummary, workbook: "lifecycle" },
  { ...lifecycleDetail, workbook: "lifecycle" },
  { ...lifecycleGame, workbook: "lifecycle" },
  { ...lifecycleActive, workbook: "lifecycle" },
];

const batches = { new_user: [], lifecycle: [] };
const ledger = [];
const summaries = [];
for (const sheet of normalizedSheets) {
  const dataRows = sheet.rows.filter((item) => dateLike(item.values[0]));
  if (!dataRows.length) throw new Error(`${sheet.name}: no date-bearing data rows found`);
  const firstRow = Math.min(...dataRows.map((item) => item.row));
  const lastRow = Math.max(...dataRows.map((item) => item.row));
  const metrics = [];
  for (let index = 0; index < sheet.columns.length; index += 1) {
    const header = normalizeHeader(sheet.columns[index]);
    if (dimensionHeaders.has(header) || /^col\d+$/i.test(header)) continue;
    const observed = dataRows.map((item) => item.values[index]).filter((value) => value !== null && value !== undefined && value !== "");
    const numericCount = observed.filter(numericValue).length;
    const dtype = String(sheet.dtypes?.[sheet.columns[index]] ?? "");
    const isMetric = /^(float|int|number)/i.test(dtype) || (observed.length > 0 && numericCount / observed.length >= 0.9);
    if (!isMetric) continue;
    const column = columnLetter(index);
    const zeroRows = dataRows.filter((item) => numericZero(item.values[index])).map((item) => item.row);
    metrics.push({ column, header: sheet.columns[index], zero_rows: zeroRows, data_range: `${column}${firstRow}:${column}${lastRow}` });
    for (const row of zeroRows) ledger.push({ workbook: sheet.workbook, sheet: sheet.name, cell: `${column}${row}`, header: sheet.columns[index], original_value: 0 });
  }

  const clearRanges = [];
  for (const metric of metrics) {
    const rows = metric.zero_rows;
    for (let start = 0; start < rows.length;) {
      let end = start;
      while (end + 1 < rows.length && rows[end + 1] === rows[end] + 1) end += 1;
      const first = rows[start];
      const last = rows[end];
      clearRanges.push(`${sheet.name}!${metric.column}${first}:${metric.column}${last}`);
      start = end + 1;
    }
  }
  // Keep each request modest. Large range lists on the lifecycle sheets can
  // remain pending for several minutes; 20 ranges is fast enough to resume
  // safely and still reduces the number of network calls substantially.
  for (let offset = 0; offset < clearRanges.length; offset += 20) batches[sheet.workbook].push(clearRanges.slice(offset, offset + 20));
  summaries.push({
    workbook: sheet.workbook,
    sheet: sheet.name,
    data_rows: { first: firstRow, last: lastRow, count: dataRows.length },
    metric_columns: metrics.map((item) => ({ column: item.column, header: item.header, data_range: item.data_range, zero_count: item.zero_rows.length })),
    zero_count: metrics.reduce((sum, item) => sum + item.zero_rows.length, 0),
    color_scale_rule_count: metrics.length,
    clear_range_count: clearRanges.length,
  });
}

await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(path.join(outputDir, "zero-ledger.json"), JSON.stringify({ generated_at: new Date().toISOString(), cells: ledger }, null, 2));
await fs.writeFile(path.join(outputDir, "clear-batches.json"), JSON.stringify({ generated_at: new Date().toISOString(), batches }, null, 2));
await fs.writeFile(path.join(outputDir, "dry-run-summary.json"), JSON.stringify({ generated_at: new Date().toISOString(), sheets: summaries, totals: {
  zero_cells: ledger.length,
  new_user_zero_cells: ledger.filter((item) => item.workbook === "new_user").length,
  lifecycle_zero_cells: ledger.filter((item) => item.workbook === "lifecycle").length,
  color_scale_rules: summaries.reduce((sum, item) => sum + item.color_scale_rule_count, 0),
  clear_range_batches: { new_user: batches.new_user.length, lifecycle: batches.lifecycle.length },
} }, null, 2));
console.log(JSON.stringify({ status: "ok", zero_cells: ledger.length, sheets: summaries.length, color_scale_rules: summaries.reduce((sum, item) => sum + item.color_scale_rule_count, 0) }));
