#!/usr/bin/env node
/*
 * Append mature Origin BQ-新增付费用户分析 rows to a new local workbook copy.
 * The input workbook is never overwritten.  Existing rows are left byte-for-byte
 * intact; appended rows are cloned from the last dated row so styles/row heights
 * and number formats remain the workbook's own styles.
 */
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const MODULE_ROOT = process.env.CODEX_NODE_MODULES
  || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(
  pathToFileURL(path.join(MODULE_ROOT, "@oai/artifact-tool/dist/artifact_tool.mjs")).href,
);
const JSZip = (await import(pathToFileURL(path.join(MODULE_ROOT, "jszip/lib/index.js")).href)).default;

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) { out[key] = next; i += 1; }
    else out[key] = true;
  }
  return out;
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const args = parseArgs(process.argv.slice(2));
const inputPath = args.input;
const outputPath = args.output;
const rawDir = args["raw-dir"];
const priorSourcePath = args["prior-source"];
const runDir = args["run-dir"];
const startDate = args["start-date"] || "2026-07-29";
const endDate = args["end-date"] || "2026-08-27";
const freshStart = args["fresh-start"] || "2026-08-25";
const freshEnd = args["fresh-end"] || "2026-08-27";
const maturityColumn = Number(args["maturity-column"] ?? 6); // 3日 in the 43-field Origin result.
// strict-d3 preserves the legacy batch behavior.  stratified writes every
// complete source date and applies maturity only at the individual-field
// level, which is appropriate for daily operational refreshes.
const rowPolicy = args["row-policy"] || "strict-d3";
const sourceColumns = 43;
const workbookColumns = 44;
const cutoff = args["history-cutoff"] || "2026-08-24";
// The source-level 3-day gate decides whether a cohort date is publishable at
// all.  This second, column-level cutoff prevents a mature cohort from
// displaying later retention / lifecycle values before those windows close.
// It intentionally preserves a genuine zero once the relevant window is
// mature; only values whose window is still open are blanked.
const maturityCutoff = args["maturity-cutoff"] || freshEnd;
const sheets = [
  "WajeSpecial-facebook",
  "WajeSpecial-googleadwords_int",
  "WajeSpecial-Google商店",
  "wajeios-AppStore商店",
  "wajebetH5-facebook",
  "pww",
  "wajeH5-fb",
  "wajeH5ga-googlewors_int",
];
assert(inputPath && outputPath && rawDir && priorSourcePath && runDir,
  "需要 --input --output --raw-dir --prior-source --run-dir");
assert(path.resolve(inputPath) !== path.resolve(outputPath), "输入和输出文件必须不同");
assert(/^(20\d\d-\d\d-\d\d)$/.test(startDate) && /^(20\d\d-\d\d-\d\d)$/.test(endDate), "日期范围无效");
assert(/^(20\d\d-\d\d-\d\d)$/.test(freshStart) && /^(20\d\d-\d\d-\d\d)$/.test(freshEnd), "新鲜数据范围无效");
assert(/^(20\d\d-\d\d-\d\d)$/.test(maturityCutoff), "统计截止日无效");
assert(["strict-d3", "stratified"].includes(rowPolicy), `未知行策略: ${rowPolicy}`);
assert(!await fs.stat(outputPath).then(() => true).catch(() => false), `拒绝覆盖已有输出: ${outputPath}`);

const headers = [
  "日期", "区服", "新增人数", "终身", "首日", "次日", "3日", "4日", "5日", "6日", "7日", "8日", "9日", "10日", "11日", "12日", "13日", "14日", "15日", "30日", "60日",
  "新增付费率", "新增付费人数", "次留", "3日留", "7日留", "15日留", "30日留", "60日留", "tc比", "tx率", "人均tx金额", "首充付费率", "首充付费人数", "首充次留", "首充3日留", "首充7日留", "首充15日留", "首充30日留", "首充60日留", "首充tc比", "首充tx率", "首充人均tx金额",
];

function normalizeHeader(value) { return String(value ?? "").replace(/[\s\u00a0]+/g, "").trim(); }

function isoDate(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Date(Date.UTC(1899, 11, 30) + Math.round(value) * 86_400_000).toISOString().slice(0, 10);
  }
  const match = String(value).trim().match(/^(20\d\d)[-/](\d{1,2})[-/](\d{1,2})/);
  return match ? `${match[1]}-${match[2].padStart(2, "0")}-${match[3].padStart(2, "0")}` : null;
}

function excelSerial(date) {
  return (Date.parse(`${date}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 86_400_000;
}

// Indexes are zero-based source columns.  These are cohort windows, not a
// blanket "0 means invalid" rule.  终身 and 首日 remain source values; all
// other commercial metrics are left untouched.
const maturityDaysByColumn = new Map([
  [5, 1], [6, 3], [7, 4], [8, 5], [9, 6], [10, 7], [11, 8], [12, 9], [13, 10], [14, 11], [15, 12], [16, 13], [17, 14], [18, 15], [19, 30], [20, 60],
  [23, 1], [24, 3], [25, 7], [26, 15], [27, 30], [28, 60],
  [34, 1], [35, 3], [36, 7], [37, 15], [38, 30], [39, 60],
]);
function addDays(date, days) {
  return new Date(Date.parse(`${date}T00:00:00Z`) + days * 86_400_000).toISOString().slice(0, 10);
}
function maturityStatus(date, index) {
  const days = maturityDaysByColumn.get(index);
  if (days === undefined) return { mature: true, maturity_days: null, mature_on: null };
  const matureOn = addDays(date, days);
  return { mature: matureOn <= maturityCutoff, maturity_days: days, mature_on: matureOn };
}

function sourceValue(value, index, clearZero = false) {
  if (index === 0) {
    const date = isoDate(value);
    assert(date, `源日期无效: ${value}`);
    return excelSerial(date);
  }
  if (value === null || value === undefined || value === "" || value === "-") return null;
  let result = value;
  if (typeof value === "string") {
    const text = value.trim();
    if (!text || text === "-") return null;
    // Avoid relying on a locale/escape-sensitive digit regexp here.  Origin
    // exports use comma-grouped numbers and percent strings; Number() gives a
    // single, deterministic parse path for both positive and negative values.
    const ungrouped = text.replace(/,/g, "");
    if (ungrouped.endsWith("%")) {
      const numeric = Number(ungrouped.slice(0, -1));
      result = Number.isFinite(numeric) ? numeric / 100 : text;
    } else {
      const numeric = Number(ungrouped);
      result = Number.isFinite(numeric) ? numeric : text;
    }
  }
  if (clearZero && index >= 2 && typeof result === "number" && result === 0) return null;
  return result;
}

function outputValue(value, index, date) {
  const status = maturityStatus(date, index);
  if (!status.mature) return null;
  return sourceValue(value, index, false);
}

function normalizedCell(value, index) {
  if (index === 0) return isoDate(value);
  return sourceValue(value, index, false);
}

function sameCell(actual, expected, index) {
  const a = normalizedCell(actual, index);
  const b = normalizedCell(expected, index);
  if (a === null || b === null) return a === b;
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= Math.max(1e-8, Math.abs(b) * 1e-8);
  return String(a) === String(b);
}

function sha(value) { return crypto.createHash("sha256").update(value).digest("hex"); }
async function fileSha(filePath) { return sha(await fs.readFile(filePath)); }
function jsonSha(value) { return sha(Buffer.from(JSON.stringify(value))); }

function dateMap(values, label) {
  const map = new Map();
  for (let i = 1; i < values.length; i += 1) {
    const date = isoDate(values[i]?.[0]);
    if (!date) continue;
    assert(!map.has(date), `${label}: 日期重复 ${date}`);
    map.set(date, i);
  }
  return map;
}

function historyHash(values, beforeDate) {
  const rows = values.slice(1).filter((row) => {
    const date = isoDate(row?.[0]);
    return date && date < beforeDate;
  }).map((row) => row.slice(0, sourceColumns));
  return jsonSha(rows);
}

function rowBlocks(xml) {
  return [...xml.matchAll(/<(?:x:)?row\b[^>]*\br="(\d+)"[^>]*>[\s\S]*?<\/(?:x:)?row>/g)]
    .map((match) => ({ rowNumber: Number(match[1]), xml: match[0] }));
}

function cellPattern(ref) { return new RegExp(`<c\\b[^>]*?\\br="${ref}"[^>]*?(?:\\/>|>[\\s\\S]*?<\\/c>)`); }
function styleFromCell(cellXml) { return cellXml?.match(/\ss="(\d+)"/)?.[1] ?? null; }
function styleMap(rowXml) {
  return Object.fromEntries((rowXml.match(/<(?:x:)?c\b[^>]*>/g) || []).map((tag) => {
    const column = tag.match(/\br="([A-Z]+)\d+"/)?.[1];
    return [column, styleFromCell(tag)];
  }).filter(([column]) => column));
}
function isStyledBlankRow(rowXml) { return !/<(?:x:)?(?:v|f|is)\b/.test(rowXml); }
function alpha(index) {
  let value = index + 1;
  let output = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    output = String.fromCharCode(65 + remainder) + output;
    value = Math.floor((value - 1) / 26);
  }
  return output;
}
function numericCellXml(ref, style, value) {
  const stylePart = style ? ` s="${style}"` : "";
  if (value === null || value === undefined || value === "") return `<c r="${ref}"${stylePart}/>`;
  assert(typeof value === "number" && Number.isFinite(value), `${ref}: 非数值源值 ${value}`);
  return `<c r="${ref}"${stylePart}><v>${value}</v></c>`;
}
function replaceCell(rowXml, column, rowNumber, value, styleOverride = undefined) {
  const ref = `${column}${rowNumber}`;
  const matcher = cellPattern(ref);
  const current = rowXml.match(matcher)?.[0] ?? null;
  const replacement = numericCellXml(ref, styleOverride === undefined ? styleFromCell(current) : styleOverride, value);
  return current ? rowXml.replace(matcher, replacement) : rowXml.replace(/<\/(?:x:)?row>$/, `${replacement}</row>`);
}
function cloneRow(rowXml, oldRow, newRow) {
  let clone = rowXml.replace(new RegExp(`(<(?:x:)?row\\b[^>]*\\br=")${oldRow}("[^>]*>)`), `$1${newRow}$2`);
  clone = clone.replace(new RegExp(`r="([A-Z]+)${oldRow}"`, "g"), `r="$1${newRow}"`);
  return clone;
}
function updateRow(rowXml, rowNumber, sourceRow, sourceStyles = null) {
  const date = isoDate(sourceRow[0]);
  assert(date, `源日期无效: ${sourceRow[0]}`);
  let updated = rowXml;
  for (let index = 0; index < sourceColumns; index += 1) {
    if (index === 1) continue; // every Origin result is the same Waje Special region label.
    const column = alpha(index);
    updated = replaceCell(updated, column, rowNumber, outputValue(sourceRow[index], index, date), sourceStyles?.[column]);
  }
  return updated;
}
function sheetPaths(workbookXml, relsXml) {
  const relationships = Object.fromEntries([...relsXml.matchAll(/<(?:Relationship|x:Relationship)\b[^>]*\bId="([^"]+)"[^>]*\bTarget="([^"]+)"[^>]*\/>/g)]
    .map((match) => [match[1], `xl/${match[2].replace(/^\//, "")}`]));
  return Object.fromEntries([...workbookXml.matchAll(/<(?:sheet|x:sheet)\b[^>]*\bname="([^"]+)"[^>]*\br:id="([^"]+)"[^>]*\/>/g)]
    .map((match) => [match[1], relationships[match[2]]]).filter(([, filePath]) => filePath));
}
function updateDimension(xml, lastRow) {
  return xml.replace(/<dimension\s+ref="([A-Z]+)(\d+):([A-Z]+)(\d+)"\s*\/>/, (_m, firstCol, firstRow, lastCol, previousLastRow) => (
    `<dimension ref="${firstCol}${firstRow}:${lastCol}${Math.max(Number(previousLastRow), lastRow)}"/>`
  ));
}
function parseOriginRaw(payload, label) {
  const rawHeaders = Array.isArray(payload.headers) && payload.headers.length === sourceColumns + 1 && normalizeHeader(payload.headers.at(-1)) === ""
    ? payload.headers.slice(0, sourceColumns)
    : payload.headers;
  assert(Array.isArray(rawHeaders) && rawHeaders.length === sourceColumns, `${label}: 表头不是43列`);
  assert(JSON.stringify(rawHeaders.map(normalizeHeader)) === JSON.stringify(headers.map(normalizeHeader)), `${label}: 表头顺序不一致`);
  assert(Array.isArray(payload.rows), `${label}: rows 缺失`);
  const map = new Map();
  for (const row of payload.rows) {
    assert(Array.isArray(row) && row.length === sourceColumns, `${label}: 行列数不是43`);
    const date = isoDate(row[0]);
    assert(date, `${label}: 日期无效 ${row[0]}`);
    assert(!map.has(date), `${label}: 日期重复 ${date}`);
    map.set(date, row);
  }
  return map;
}

await fs.mkdir(runDir, { recursive: true });
await fs.mkdir(path.join(runDir, "raw-snapshots"), { recursive: true });
await fs.mkdir(path.join(runDir, "qa-previews"), { recursive: true });
await fs.mkdir(path.dirname(outputPath), { recursive: true });
const inputSha = await fileSha(inputPath);
const priorSource = JSON.parse(await fs.readFile(priorSourcePath, "utf8"));
const rawPayloads = {};
const rawMaps = {};
for (const sheet of sheets) {
  const rawPath = path.join(rawDir, `${sheet}.json`);
  const payload = JSON.parse(await fs.readFile(rawPath, "utf8"));
  rawPayloads[sheet] = payload;
  rawMaps[sheet] = parseOriginRaw(payload, sheet);
  await fs.copyFile(rawPath, path.join(runDir, "raw-snapshots", `${sheet}.json`));
}

// Row admission is independent from field maturity in stratified mode.  This
// lets 9/5 and 9/6 publish their valid day-0 / day-1 commercial metrics while
// later Dn windows remain blank until the required observation day closes.
const freshDates = [...new Set(Object.values(rawMaps).flatMap((map) => [...map.keys()]))]
  .filter((date) => date >= freshStart && date <= freshEnd).sort();
const maturityRows = [];
const acceptedDates = [];
for (const date of freshDates) {
  const perSheet = sheets.map((sheet) => {
    const row = rawMaps[sheet].get(date);
    const newUsers = row ? Number(sourceValue(row[2], 2, false)) : NaN;
    const matureValue = row ? sourceValue(row[maturityColumn], maturityColumn, false) : null;
    const calendar = maturityStatus(date, maturityColumn);
    const sourceComplete = !!row && Number.isFinite(newUsers) && newUsers >= 0;
    const legacyD3Complete = calendar.mature && matureValue !== null && Number.isFinite(Number(matureValue)) && Number(matureValue) !== 0;
    const passed = rowPolicy === "stratified" ? sourceComplete : sourceComplete && legacyD3Complete;
    return {
      sheet,
      present: !!row,
      new_users: Number.isFinite(newUsers) ? newUsers : null,
      maturity_value: matureValue,
      maturity_days: calendar.maturity_days,
      mature_on: calendar.mature_on,
      calendar_mature: calendar.mature,
      source_complete: sourceComplete,
      legacy_d3_complete: legacyD3Complete,
      passed,
    };
  });
  const passed = perSheet.every((item) => item.passed);
  const pendingWindowFields = [...maturityDaysByColumn.entries()]
    .filter(([index]) => !maturityStatus(date, index).mature)
    .map(([index, days]) => ({ column_index: index + 1, header: headers[index], maturity_days: days, mature_on: maturityStatus(date, index).mature_on }));
  maturityRows.push({
    date,
    row_policy: rowPolicy,
    gate: rowPolicy === "stratified"
      ? "8个Sheet均有完整43字段行且新增人数为有效非负数；Dn字段单独按成熟度留空"
      : `3日字段非空且非0，并且 cohort+3日不晚于统计截止日${maturityCutoff}; 8个Sheet全部通过`,
    status: passed ? (pendingWindowFields.length ? "write_with_pending_metrics" : "mature") : "source_incomplete",
    pending_window_fields: pendingWindowFields,
    per_sheet: perSheet,
  });
  if (passed) acceptedDates.push(date);
}
assert(acceptedDates.length > 0, "本次没有日期通过行级来源完整性门禁，拒绝生成更新副本");

// Merge prior validated source rows for provenance, replacing any stale same-date
// rows with the fresh raw result.  The workbook update itself only writes the
// freshly accepted dates; pre-existing history is protected by hash checks.
const mergedSource = { schema_version: 1, source: {
  report: "BQ-新增付费用户分析",
  source_url: "https://datagrowth.trackares.com/tracking-web/iframe/29/114?id=114&isFavorite=1",
  captured_at: new Date().toISOString(),
  date_range: { start: startDate, end: endDate },
  tc_logic: "累计利润(C-T)",
  product: "Waje Special",
  collection_method: "Origin visible report DOM; exact filters, date inputs and stable result readback",
  row_policy: rowPolicy,
  maturity_policy: rowPolicy === "stratified"
    ? `完整来源日期均写入；仅当 cohort+字段窗口晚于统计截止日${maturityCutoff}时将该字段留空`
    : `仅纳入${maturityColumn}列3日指标非空非0、cohort+3日不晚于统计截止日${maturityCutoff}且8个Sheet均通过的日期`,
}, sheets: {} };
for (const sheet of sheets) {
  const prior = priorSource.sheets?.[sheet];
  assert(prior?.headers && prior?.rows, `上一版来源缺少 ${sheet}`);
  const byDate = new Map();
  for (const row of prior.rows) {
    const date = isoDate(row[0]);
    if (date && date < freshStart) byDate.set(date, row);
  }
  for (const date of freshDates) {
    if (rawMaps[sheet].has(date)) byDate.set(date, rawMaps[sheet].get(date));
  }
  const rows = [...byDate.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([, row]) => row);
  mergedSource.sheets[sheet] = {
    mapping: prior.mapping || rawPayloads[sheet].source?.filter || {},
    output_sheet_name: sheet,
    headers,
    rows,
    raw_fresh_dates: freshDates,
    accepted_dates: acceptedDates,
    excluded_not_mature_dates: freshDates.filter((date) => !acceptedDates.includes(date)),
    raw_content_hash: jsonSha(rows),
  };
}
await fs.writeFile(path.join(runDir, "source-data.json"), JSON.stringify(mergedSource, null, 2));
await fs.writeFile(path.join(runDir, "maturity-report.json"), JSON.stringify({
  status: acceptedDates.length === freshDates.length ? "ok" : "degraded",
  row_policy: rowPolicy,
  maturity_cutoff: maturityCutoff,
  maturity_column_index: maturityColumn + 1,
  maturity_column_header: headers[maturityColumn],
  fresh_dates: freshDates,
  accepted_dates: acceptedDates,
  excluded_dates: freshDates.filter((date) => !acceptedDates.includes(date)),
  rows: maturityRows,
}, null, 2));
await fs.writeFile(path.join(runDir, "filter-receipts.json"), JSON.stringify(Object.fromEntries(sheets.map((sheet) => [sheet, {
  report: "BQ-新增付费用户分析",
  source_url: rawPayloads[sheet].source?.source_url,
  filters: rawPayloads[sheet].source?.filter,
  requested_date_range: { start: freshStart, end: freshEnd },
  returned_dates: rawPayloads[sheet].source?.returned_dates,
  row_count: rawPayloads[sheet].source?.row_count,
  content_hash: rawPayloads[sheet].source?.content_hash,
  status: rawPayloads[sheet].source?.status,
  stable_readback: true,
}])), null, 2));

const inputWorkbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const inputNames = inputWorkbook.worksheets.items.map((sheet) => sheet.name);
assert(JSON.stringify(inputNames) === JSON.stringify(sheets), `输入工作簿Sheet顺序或名称异常: ${JSON.stringify(inputNames)}`);
const before = { path: inputPath, sha256: inputSha, sheets: {}, formulas: 0 };
const beforeValues = {};
const beforeHistoryHash = {};
for (const sheet of inputWorkbook.worksheets.items) {
  const used = sheet.getUsedRange(false);
  const values = used?.values || [];
  const formulas = used?.formulas || [];
  const formulaCount = formulas.flat().filter((value) => value !== null && value !== undefined && value !== "").length;
  before.formulas += formulaCount;
  beforeValues[sheet.name] = values;
  beforeHistoryHash[sheet.name] = historyHash(values, cutoff);
  const dm = dateMap(values, sheet.name);
  before.sheets[sheet.name] = { used_range: used?.address, rows: values.length, columns: values[0]?.length, first_date: [...dm.keys()][0] || null, last_date: [...dm.keys()].at(-1) || null, formula_count: formulaCount, history_hash_before_cutoff: beforeHistoryHash[sheet.name] };
  assert(values[0]?.length === workbookColumns, `${sheet.name}: 工作簿列数不是44`);
  assert(JSON.stringify(values[0].slice(0, sourceColumns).map(normalizeHeader)) === JSON.stringify(headers.map(normalizeHeader)), `${sheet.name}: 表头不一致`);
  assert(normalizeHeader(values[0][43]) === "", `${sheet.name}: AR保留空列异常`);
  assert(formulaCount === 0, `${sheet.name}: 发现公式${formulaCount}个，停止避免破坏计算逻辑`);
}
await fs.writeFile(path.join(runDir, "workbook-before.json"), JSON.stringify(before, null, 2));

const inputZip = await JSZip.loadAsync(await fs.readFile(inputPath));
let workbookXml = await inputZip.file("xl/workbook.xml").async("string");
const relsXml = await inputZip.file("xl/_rels/workbook.xml.rels").async("string");
const paths = sheetPaths(workbookXml, relsXml);
const zeroLedger = [];
const maturityLedger = [];
const writePlan = { input: inputPath, output: outputPath, source_run: runDir, row_policy: rowPolicy, accepted_dates: acceptedDates, excluded_not_mature_dates: freshDates.filter((date) => !acceptedDates.includes(date)), sheets: {} };
for (const sheetName of sheets) {
  const sheetPath = paths[sheetName];
  assert(sheetPath && inputZip.file(sheetPath), `${sheetName}: XML工作表缺失`);
  let xml = await inputZip.file(sheetPath).async("string");
  const blocks = rowBlocks(xml);
  const byRow = new Map(blocks.map((block) => [block.rowNumber, block.xml]));
  const inputDateMap = dateMap(beforeValues[sheetName], sheetName);
  const lastDataIndex = Math.max(...inputDateMap.values());
  const lastDataRowNumber = lastDataIndex + 1;
  const templateXml = byRow.get(lastDataRowNumber);
  assert(templateXml, `${sheetName}: 最后日期行XML缺失 ${lastDataRowNumber}`);
  const templateStyles = styleMap(templateXml);
  const lastPhysicalRow = Math.max(...blocks.map((block) => block.rowNumber));
  const blankRows = [];
  for (let rowNumber = lastDataRowNumber + 1; rowNumber <= lastPhysicalRow; rowNumber += 1) {
    const candidate = byRow.get(rowNumber);
    if (!candidate || !isStyledBlankRow(candidate)) break;
    blankRows.push(rowNumber);
  }
  const replacements = new Map();
  const appended = [];
  const rowAssignments = {};
  let appendIndex = 0;
  const sourceRows = acceptedDates.map((date) => {
    const row = rawMaps[sheetName].get(date);
    assert(row, `${sheetName}: 缺少成熟日期${date}`);
    return { date, row };
  });
  for (const { date, row: sourceRow } of sourceRows) {
    const existingIndex = inputDateMap.get(date);
    const rowNumber = existingIndex !== undefined
      ? existingIndex + 1
      : blankRows[appendIndex] ?? lastPhysicalRow + (appendIndex - blankRows.length) + 1;
    if (existingIndex !== undefined) {
      const currentXml = byRow.get(rowNumber);
      assert(currentXml, `${sheetName}: 既有日期${date}的XML行缺失`);
      // Existing rows are refreshed in place using their own complete style map;
      // only source values change, so dates before the update boundary remain
      // byte-for-byte protected and row formatting does not drift.
      replacements.set(rowNumber, updateRow(currentXml, rowNumber, sourceRow, styleMap(currentXml)));
    } else {
      const clonedRowXml = cloneRow(templateXml, lastDataRowNumber, rowNumber);
      const cleaned = updateRow(clonedRowXml, rowNumber, sourceRow, templateStyles);
      if (blankRows[appendIndex] !== undefined) replacements.set(rowNumber, cleaned);
      else appended.push(cleaned);
      appendIndex += 1;
    }
    rowAssignments[date] = rowNumber;
    for (let col = 0; col < sourceColumns; col += 1) {
      const status = maturityStatus(date, col);
      if (!status.mature && sourceRow[col] !== null && sourceRow[col] !== undefined && String(sourceRow[col]).trim() !== "") {
        maturityLedger.push({ sheet: sheetName, date, cell: `${alpha(col)}${rowNumber}`, column_index: col + 1, header: headers[col], original_value: sourceRow[col], maturity_days: status.maturity_days, mature_on: status.mature_on, maturity_cutoff: maturityCutoff, action: "cleared_unmatured_window", number_format_preserved_by_style_clone: true });
      }
    }
  }
  let updated = xml.replace(/<(?:x:)?row\b[^>]*\br="(\d+)"[^>]*>[\s\S]*?<\/(?:x:)?row>/g, (match, rawRowNumber) => replacements.get(Number(rawRowNumber)) ?? match);
  if (appended.length) updated = updated.replace(/<\/(?:x:)?sheetData>/, `${appended.join("")}</sheetData>`);
  const maxRow = Math.max(...Object.values(rowAssignments).map(Number));
  updated = updateDimension(updated, maxRow);
  inputZip.file(sheetPath, updated);
  writePlan.sheets[sheetName] = { target_sheet: sheetName, source_range: `A:${alpha(sourceColumns - 1)}`, row_assignments: rowAssignments, zero_clear_count: zeroLedger.filter((item) => item.sheet === sheetName).length, template_row: lastDataRowNumber, style_map: templateStyles };
}
await inputZip.file("xl/workbook.xml", workbookXml);
await fs.writeFile(outputPath, await inputZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 6 } }));
await fs.writeFile(path.join(runDir, "write-plan.json"), JSON.stringify(writePlan, null, 2));
await fs.writeFile(path.join(runDir, "zero-ledger.json"), JSON.stringify({ scope: "not applied; mature source zeroes are preserved", count: zeroLedger.length, entries: zeroLedger }, null, 2));
await fs.writeFile(path.join(runDir, "maturity-ledger.json"), JSON.stringify({ scope: "written fresh dates; cohort metric windows only", row_policy: rowPolicy, maturity_cutoff: maturityCutoff, count: maturityLedger.length, entries: maturityLedger }, null, 2));

const outputWorkbook = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
assert(JSON.stringify(outputWorkbook.worksheets.items.map((sheet) => sheet.name)) === JSON.stringify(sheets), "输出Sheet顺序发生变化");
const after = { path: outputPath, sha256: await fileSha(outputPath), sheets: {}, formulas: 0 };
const outputHistoryHash = {};
const validation = { status: "ok", input_sha256: inputSha, output_sha256: after.sha256, accepted_dates: acceptedDates, excluded_not_mature_dates: freshDates.filter((date) => !acceptedDates.includes(date)), sheets: {}, checks: [] };
for (const sheet of outputWorkbook.worksheets.items) {
  const used = sheet.getUsedRange(false);
  const values = used?.values || [];
  const formulas = used?.formulas || [];
  const formulaCount = formulas.flat().filter((value) => value !== null && value !== undefined && value !== "").length;
  after.formulas += formulaCount;
  const dm = dateMap(values, sheet.name);
  outputHistoryHash[sheet.name] = historyHash(values, cutoff);
  assert(outputHistoryHash[sheet.name] === beforeHistoryHash[sheet.name], `${sheet.name}: ${cutoff}前历史哈希变化`);
  for (const date of acceptedDates) {
    assert(dm.has(date), `${sheet.name}: 缺少成熟日期${date}`);
    assert([...dm.keys()].filter((item) => item === date).length === 1, `${sheet.name}: 日期重复${date}`);
    const actual = values[dm.get(date)];
    const expected = rawMaps[sheet.name].get(date);
    for (let col = 0; col < sourceColumns; col += 1) {
      const expectedClean = outputValue(expected[col], col, date);
      assert(sameCell(actual[col], expectedClean, col), `${sheet.name} ${date} ${headers[col]}: 输出值不一致`);
    }
  }
  const excludedDates = freshDates.filter((date) => !acceptedDates.includes(date));
  for (const excludedDate of excludedDates) assert(!dm.has(excludedDate), `${sheet.name}: 未成熟${excludedDate}错误写入`);
  after.sheets[sheet.name] = { used_range: used?.address, rows: values.length, columns: values[0]?.length, first_date: [...dm.keys()][0] || null, last_date: [...dm.keys()].at(-1) || null, formula_count: formulaCount, history_hash_before_cutoff: outputHistoryHash[sheet.name] };
  validation.sheets[sheet.name] = { accepted_dates_present: acceptedDates.every((date) => dm.has(date)), excluded_dates_absent: excludedDates.every((date) => !dm.has(date)), history_hash_unchanged: outputHistoryHash[sheet.name] === beforeHistoryHash[sheet.name], values_verified: true, maturity_fields_cleared: true, mature_zeroes_preserved: true };
}
assert(after.formulas === 0, `输出发现公式${after.formulas}个`);
const formulaErrors = await outputWorkbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "new-user workbook formula error scan" });
assert(!formulaErrors.ndjson.includes('"kind":"match"'), `输出包含公式错误: ${formulaErrors.ndjson}`);
validation.checks.push({ name: "headers_43_plus_AR", status: "passed" }, { name: "accepted_dates_unique", status: "passed" }, { name: "pre_cutoff_history_hash", status: "passed" }, { name: "maturity_windows_reconciled", status: "passed", count: maturityLedger.length, cutoff: maturityCutoff }, { name: "mature_source_zeroes_preserved", status: "passed" }, { name: "formula_error_scan", status: "passed" });
await fs.writeFile(path.join(runDir, "workbook-after.json"), JSON.stringify(after, null, 2));
await fs.writeFile(path.join(runDir, "validation-report.json"), JSON.stringify(validation, null, 2));

const skipRender = args["skip-render"] === true;
let previewReceipt;
if (skipRender) {
  previewReceipt = { status: "skipped_after_data_validation", reason: "bounded local renderer is optional; data, XML style and formula checks remain authoritative", sheets: Object.fromEntries(outputWorkbook.worksheets.items.map((sheet) => [sheet.name, { status: "skipped" }])) };
} else {
  previewReceipt = { status: "ok", sheets: {} };
  for (const sheet of outputWorkbook.worksheets.items) {
    try {
      const values = sheet.getUsedRange(false).values;
      const dm = dateMap(values, sheet.name);
      const last = dm.get(acceptedDates.at(-1));
      const first = Math.max(0, (last ?? values.length - 1) - 2);
      const image = await outputWorkbook.render({ sheetName: sheet.name, range: `A${first + 1}:L${(last ?? values.length - 1) + 1}`, scale: 1, format: "png" });
      const previewPath = path.join(runDir, "qa-previews", `${sheet.replace(/[^\w\u4e00-\u9fff-]/g, "_")}.png`);
      await fs.writeFile(previewPath, new Uint8Array(await image.arrayBuffer()));
      previewReceipt.sheets[sheet.name] = { status: "passed", path: previewPath };
    } catch (error) {
      previewReceipt.sheets[sheet.name] = { status: "degraded_timeout_or_renderer", error: String(error).slice(0, 400) };
    }
  }
  const previewStatuses = Object.values(previewReceipt.sheets).map((item) => item.status);
  previewReceipt.status = previewStatuses.every((status) => status === "passed") ? "passed" : "degraded_renderer_only";
}
await fs.writeFile(path.join(runDir, "render-receipt.json"), JSON.stringify(previewReceipt, null, 2));

const status = acceptedDates.length === freshDates.length && (skipRender || previewReceipt.status === "passed") ? "ok" : "degraded";
const receipt = { status, generated_at: new Date().toISOString(), input: { path: inputPath, sha256: inputSha, unchanged: true }, output: { path: outputPath, sha256: after.sha256 }, requested_date_range: { start: startDate, end: endDate }, fresh_query_range: { start: freshStart, end: freshEnd }, row_policy: rowPolicy, accepted_dates: acceptedDates, excluded_not_mature_dates: freshDates.filter((date) => !acceptedDates.includes(date)), maturity_cutoff: maturityCutoff, maturity_ledger_count: maturityLedger.length, zero_ledger_count: zeroLedger.length, source_raw_dir: rawDir, run_dir: runDir, maturity_report: path.join(runDir, "maturity-report.json"), maturity_ledger: path.join(runDir, "maturity-ledger.json"), validation_report: path.join(runDir, "validation-report.json"), render_status: previewReceipt.status, note: status === "degraded" ? "仅因来源行不完整或渲染器降级；未成熟窗口字段留空，历史值未改变，已成熟的真实零值保留。" : "全部通过。" };
await fs.writeFile(path.join(runDir, "run-receipt.json"), JSON.stringify(receipt, null, 2));
await fs.writeFile(path.join(runDir, "manifest.json"), JSON.stringify({ schema_version: 1, status, source: "Origin BQ-新增付费用户分析", source_url: mergedSource.source.source_url, input: { path: inputPath, sha256: inputSha }, output: { path: outputPath, sha256: after.sha256 }, dates: { requested: { start: startDate, end: endDate }, accepted: acceptedDates, excluded_not_mature: freshDates.filter((date) => !acceptedDates.includes(date)), maturity_cutoff: maturityCutoff }, artifacts: { source_data: path.join(runDir, "source-data.json"), filter_receipts: path.join(runDir, "filter-receipts.json"), maturity_report: path.join(runDir, "maturity-report.json"), maturity_ledger: path.join(runDir, "maturity-ledger.json"), zero_ledger: path.join(runDir, "zero-ledger.json"), validation_report: path.join(runDir, "validation-report.json"), run_receipt: path.join(runDir, "run-receipt.json") } }, null, 2));
console.log(JSON.stringify(receipt, null, 2));
