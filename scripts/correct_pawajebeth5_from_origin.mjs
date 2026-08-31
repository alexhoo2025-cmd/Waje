#!/usr/bin/env node
/*
 * Correct the locally exported PAWAJEBETH5 data from a user-confirmed Origin
 * filter without touching any other worksheet or protected history.
 *
 * The input workbook is a prior generated copy whose target tab is named
 * `wajebetH5-facebook`; this program writes a new copy and renames only that
 * tab to `wajebetH5` so the tab name matches its confirmed source filter.
 */
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import JSZip from "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/jszip/lib/index.js";

const MODULE_ROOT = process.env.CODEX_NODE_MODULES
  || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(
  pathToFileURL(path.join(MODULE_ROOT, "@oai/artifact-tool/dist/artifact_tool.mjs")).href,
);

const SOURCE_COLUMNS = 43;
const WORKBOOK_COLUMNS = 44;
const PROTECTED_CUTOFF = "2026-07-13";
const SAMPLE_DATES = ["2026-07-12", "2026-07-13"];
const REQUIRED_SAMPLE_COLUMNS = [
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
  21, 22, 23, 24, 25, 29, 30, 31, 32, 33, 40, 41, 42,
];

function parseArgs(argv) {
  const result = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) {
      result[key] = next;
      i += 1;
    } else result[key] = true;
  }
  return result;
}

function assert(value, message) {
  if (!value) throw new Error(message);
}

function isoDate(value) {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Date(Date.UTC(1899, 11, 30) + Math.round(value) * 86_400_000).toISOString().slice(0, 10);
  }
  const match = String(value).trim().match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (!match) return null;
  return `${match[1]}-${match[2].padStart(2, "0")}-${match[3].padStart(2, "0")}`;
}

function dateRange(start, end) {
  const values = [];
  for (let at = Date.parse(`${start}T00:00:00Z`); at <= Date.parse(`${end}T00:00:00Z`); at += 86_400_000) {
    values.push(new Date(at).toISOString().slice(0, 10));
  }
  return values;
}

function excelSerial(date) {
  return (Date.parse(`${date}T00:00:00Z`) - Date.UTC(1899, 11, 30)) / 86_400_000;
}

function normalizeHeader(value) {
  return String(value ?? "").replace(/[\s\u00a0]+/g, "").trim();
}

function sourceValue(value, index) {
  if (index === 0) {
    const date = isoDate(value);
    assert(date, `Invalid source date: ${value}`);
    return excelSerial(date);
  }
  if (value === null || value === undefined || value === "" || value === "-") return null;
  if (typeof value !== "string") return value;
  const text = value.trim();
  if (text === "" || text === "-") return null;
  if (/^-?[\d,]+(?:\.\d+)?%$/.test(text)) return Number(text.replace(/,/g, "").slice(0, -1)) / 100;
  if (/^-?[\d,]+(?:\.\d+)?$/.test(text)) return Number(text.replace(/,/g, ""));
  return text;
}

function normalizedCell(value, index) {
  if (index === 0) return isoDate(value);
  return sourceValue(value, index);
}

function sameCell(actual, expected, index) {
  const a = normalizedCell(actual, index);
  const b = normalizedCell(expected, index);
  if (a === null || b === null) return a === b;
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= Math.max(1e-8, Math.abs(b) * 1e-8);
  return String(a) === String(b);
}

function sha(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

async function fileSha(filePath) {
  return sha(await fs.readFile(filePath));
}

function dateMap(values, label) {
  const map = new Map();
  for (let index = 1; index < values.length; index += 1) {
    const date = isoDate(values[index]?.[0]);
    if (!date) continue;
    assert(!map.has(date), `${label}: duplicate date ${date}`);
    map.set(date, index);
  }
  return map;
}

function sourceMap(rows, label) {
  const map = new Map();
  for (const row of rows) {
    assert(Array.isArray(row) && row.length === SOURCE_COLUMNS, `${label}: expected ${SOURCE_COLUMNS} columns per row`);
    const date = isoDate(row[0]);
    assert(date, `${label}: invalid date ${row[0]}`);
    assert(!map.has(date), `${label}: duplicate date ${date}`);
    map.set(date, row);
  }
  return map;
}

function protectedHash(values) {
  let last = 0;
  for (let index = 1; index < values.length; index += 1) {
    const date = isoDate(values[index]?.[0]);
    if (date && date <= PROTECTED_CUTOFF) last = index;
  }
  return sha(Buffer.from(JSON.stringify(values.slice(0, last + 1))));
}

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

function rowBlocks(xml) {
  return [...xml.matchAll(/<(?:x:)?row\b[^>]*\br="(\d+)"[^>]*>[\s\S]*?<\/(?:x:)?row>/g)]
    .map((match) => ({ rowNumber: Number(match[1]), xml: match[0] }));
}

function cellPattern(ref) {
  return new RegExp(`<c\\b[^>]*\\br="${ref}"[^>]*(?:\\/>|>[\\s\\S]*?<\\/c>)`);
}

function styleFromCell(cellXml) {
  return cellXml?.match(/\ss="(\d+)"/)?.[1] ?? null;
}

function styleMap(rowXml) {
  return Object.fromEntries((rowXml.match(/<(?:x:)?c\b[^>]*>/g) || []).map((tag) => {
    const column = tag.match(/\br="([A-Z]+)\d+"/)?.[1];
    return [column, styleFromCell(tag)];
  }).filter(([column]) => column));
}

function sameStyleMap(left, right) {
  const columns = [...new Set([...Object.keys(left), ...Object.keys(right)])].sort();
  return columns.every((column) => (left[column] ?? null) === (right[column] ?? null));
}

function isStyledBlankRow(rowXml) {
  return !/<(?:x:)?(?:v|f|is)\b/.test(rowXml);
}

function numericCellXml(ref, style, value) {
  const stylePart = style ? ` s="${style}"` : "";
  if (value === null || value === undefined || value === "") return `<c r="${ref}"${stylePart}/>`;
  const number = Number(value);
  assert(Number.isFinite(number), `${ref}: expected numeric source cell, got ${value}`);
  return `<c r="${ref}"${stylePart}><v>${number}</v></c>`;
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

function updateRow(rowXml, rowNumber, sourceRow, append, sourceStyles = null) {
  let updated = rowXml;
  for (let index = 0; index < SOURCE_COLUMNS; index += 1) {
    if (index === 1) continue; // retain the existing Waje Special string cell
    if (!append && index === 0) continue; // existing date is the row key and must not move
    const column = alpha(index);
    updated = replaceCell(updated, column, rowNumber, sourceValue(sourceRow[index], index), sourceStyles?.[column]);
  }
  return updated;
}

function sheetPaths(workbookXml, relsXml) {
  const relationships = Object.fromEntries([...relsXml.matchAll(/<(?:Relationship|x:Relationship)\b[^>]*\bId="([^"]+)"[^>]*\bTarget="([^"]+)"[^>]*\/>/g)]
    .map((match) => [match[1], `xl/${match[2].replace(/^\//, "")}`]));
  return Object.fromEntries([...workbookXml.matchAll(/<(?:sheet|x:sheet)\b[^>]*\bname="([^"]+)"[^>]*\br:id="([^"]+)"[^>]*\/>/g)]
    .map((match) => [match[1], relationships[match[2]]])
    .filter(([, filePath]) => filePath));
}

function renameSheet(workbookXml, before, after) {
  const escaped = before.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return workbookXml.replace(new RegExp(`(<(?:sheet|x:sheet)\\b[^>]*\\bname=")${escaped}("[^>]*\\/>)`, "g"), `$1${after}$2`);
}

function updateDimension(xml, lastRow) {
  return xml.replace(/<dimension\s+ref="([A-Z]+)(\d+):([A-Z]+)(\d+)"\s*\/>/, (_match, firstCol, firstRow, lastCol, previousLastRow) => (
    `<dimension ref="${firstCol}${firstRow}:${lastCol}${Math.max(Number(previousLastRow), lastRow)}"/>`
  ));
}

async function writePng(workbook, sheetName, range, filePath) {
  const image = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(filePath, new Uint8Array(await image.arrayBuffer()));
}

const args = parseArgs(process.argv.slice(2));
const inputPath = args.input;
const outputPath = args.output;
const formalPath = args.formal;
const samplePath = args.sample;
const formalReceiptPath = args["formal-receipt"];
const sampleReceiptPath = args["sample-receipt"];
const runDir = args["run-dir"];
const inputSheetName = args["input-sheet"] || "wajebetH5-facebook";
const outputSheetName = args["output-sheet"] || "wajebetH5";
const startDate = args["start-date"] || "2026-07-14";
const endDate = args["end-date"] || "2026-08-17";
const reuseOutput = args["reuse-output"] === true;
const skipRender = args["skip-render"] === true;

assert(inputPath && outputPath && formalPath && samplePath && formalReceiptPath && sampleReceiptPath && runDir,
  "Require --input, --output, --formal, --sample, --formal-receipt, --sample-receipt, and --run-dir");
assert(isoDate(startDate) === startDate && isoDate(endDate) === endDate && startDate <= endDate, "Invalid requested date range");
assert(path.resolve(inputPath) !== path.resolve(outputPath), "Input and output must be different files");
const outputAlreadyExists = await fs.stat(outputPath).then(() => true).catch(() => false);
assert(reuseOutput ? outputAlreadyExists : !outputAlreadyExists,
  reuseOutput ? `Expected existing output for --reuse-output: ${outputPath}` : `Refusing to overwrite existing output: ${outputPath}`);

await fs.mkdir(runDir, { recursive: true });
await fs.mkdir(path.join(runDir, "raw-snapshots"), { recursive: true });
await fs.mkdir(path.join(runDir, "qa-previews"), { recursive: true });

const [formalPayload, samplePayload, formalReceipt, sampleReceipt] = await Promise.all([
  fs.readFile(formalPath, "utf8").then(JSON.parse),
  fs.readFile(samplePath, "utf8").then(JSON.parse),
  fs.readFile(formalReceiptPath, "utf8").then(JSON.parse),
  fs.readFile(sampleReceiptPath, "utf8").then(JSON.parse),
]);
assert(Array.isArray(formalPayload.headers) && formalPayload.headers.length === SOURCE_COLUMNS, "Formal source headers are invalid");
assert(JSON.stringify(formalPayload.headers.map(normalizeHeader)) === JSON.stringify(samplePayload.headers.map(normalizeHeader)), "Sample/formal header mismatch");
assert(formalReceipt.report === "BQ-新增付费用户分析" && sampleReceipt.report === "BQ-新增付费用户分析", "Wrong report receipt");
for (const receipt of [formalReceipt, sampleReceipt]) {
  assert(receipt.filters?.product === "Waje Special", "Receipt product mismatch");
  assert(receipt.filters?.tc_logic === "累计利润(C-T)", "Receipt TC logic mismatch");
  assert(receipt.filters?.package_channel === "wajebetH5", "Receipt package channel must be wajebetH5");
  assert(receipt.filters?.attribution_media === null && receipt.filters?.attribution_channel === null,
    "Receipt attribution filters must remain empty");
}
assert(formalReceipt.filters.start_date === startDate && formalReceipt.filters.end_date === endDate, "Formal receipt range mismatch");
assert(sampleReceipt.filters.start_date === SAMPLE_DATES[0] && sampleReceipt.filters.end_date === SAMPLE_DATES[1], "Sample receipt range mismatch");

const formalRows = [...formalPayload.rows].sort((a, b) => isoDate(a[0]).localeCompare(isoDate(b[0])));
const sampleRows = [...samplePayload.rows].sort((a, b) => isoDate(a[0]).localeCompare(isoDate(b[0])));
const formalByDate = sourceMap(formalRows, "formal source");
const sampleByDate = sourceMap(sampleRows, "sample source");
const requestedDates = dateRange(startDate, endDate);
assert(formalByDate.size === requestedDates.length, `Formal source has ${formalByDate.size} dates; expected ${requestedDates.length}`);
for (const date of requestedDates) assert(formalByDate.has(date), `Formal source is missing ${date}`);
for (const date of SAMPLE_DATES) assert(sampleByDate.has(date), `Sample source is missing ${date}`);

const inputSha = await fileSha(inputPath);
const inputWorkbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const inputNames = inputWorkbook.worksheets.items.map((sheet) => sheet.name);
assert(inputNames.includes(inputSheetName), `Input sheet ${inputSheetName} is missing`);
assert(!inputNames.includes(outputSheetName), `Output sheet name ${outputSheetName} already exists`);
const inputSheet = inputWorkbook.worksheets.getItem(inputSheetName);
const inputValues = inputSheet.getUsedRange(false).values;
assert(inputValues[0]?.length >= WORKBOOK_COLUMNS, `${inputSheetName}: expected ${WORKBOOK_COLUMNS} columns`);
assert(JSON.stringify(inputValues[0].slice(0, SOURCE_COLUMNS).map(normalizeHeader)) === JSON.stringify(formalPayload.headers.map(normalizeHeader)),
  `${inputSheetName}: header order mismatches Origin report`);
assert(normalizeHeader(inputValues[0][WORKBOOK_COLUMNS - 1]) === "", `${inputSheetName}: trailing AR must remain blank`);
const inputDates = dateMap(inputValues, inputSheetName);
for (const date of SAMPLE_DATES) assert(inputDates.has(date), `${inputSheetName}: sample date ${date} missing`);
const sampleChecks = [];
const acceptedSampleRevisions = [];
for (const date of SAMPLE_DATES) {
  const workbookRow = inputValues[inputDates.get(date)].slice(0, SOURCE_COLUMNS);
  const sourceRow = sampleByDate.get(date);
  for (const column of REQUIRED_SAMPLE_COLUMNS) {
    if (sameCell(workbookRow[column], sourceRow[column], column)) continue;
    // Date, region, and new-user count are the mapping identity proof.  The
    // user-confirmed package-only filter must match them exactly.  Other
    // historical metrics can be re-stated by Origin; record those revisions
    // while preserving the protected workbook history unchanged.
    assert(column > 2,
      `Sample mapping mismatch: ${date} column ${column + 1}; workbook=${workbookRow[column]} source=${sourceRow[column]}`);
    acceptedSampleRevisions.push({
      date,
      column_index: column + 1,
      header: formalPayload.headers[column],
      baseline: workbookRow[column],
      source: sourceRow[column],
      reason: "User-confirmed wajebetH5 package-only filter; current Origin result re-states a protected historical metric."
    });
  }
  sampleChecks.push({
    date,
    status: "passed_with_source_revisions",
    columns_checked: REQUIRED_SAMPLE_COLUMNS.length,
    source_revision_count: acceptedSampleRevisions.filter((item) => item.date === date).length,
  });
}

const sourceManifest = {
  schema_version: 1,
  source: {
    report: "BQ-新增付费用户分析",
    captured_at: new Date().toISOString(),
    capture_method: "visible_report_table",
    filter_correction: "User confirmed PAWAJEBETH5 uses only package_channel=wajebetH5; attribution media and channel are empty.",
  },
  sheets: {
    [outputSheetName]: {
      input_sheet_name: inputSheetName,
      output_sheet_name: outputSheetName,
      mapping: { package_channel: "wajebetH5", attribution_media: null, attribution_channel: null },
      headers: formalPayload.headers,
      sample_rows: sampleRows,
      rows: formalRows,
      receipts: [sampleReceipt, formalReceipt],
      sample_validation: { dates: SAMPLE_DATES, passed: true, checks: sampleChecks },
      sample_revisions: acceptedSampleRevisions,
      protected_history_through: PROTECTED_CUTOFF,
    },
  },
};
const sourceManifestPath = path.join(runDir, "source-data.json");
await fs.writeFile(sourceManifestPath, JSON.stringify(sourceManifest, null, 2));
for (const rawPath of [formalPath, samplePath, formalReceiptPath, sampleReceiptPath, sourceManifestPath]) {
  await fs.copyFile(rawPath, path.join(runDir, "raw-snapshots", path.basename(rawPath)));
}

const inputZip = await JSZip.loadAsync(await fs.readFile(inputPath));
let workbookXml = await inputZip.file("xl/workbook.xml").async("string");
const relationshipsXml = await inputZip.file("xl/_rels/workbook.xml.rels").async("string");
const paths = sheetPaths(workbookXml, relationshipsXml);
const targetSheetPath = paths[inputSheetName];
assert(targetSheetPath && inputZip.file(targetSheetPath), `${inputSheetName}: worksheet XML is missing`);
const otherSheetHashes = {};
for (const [sheetName, sheetPath] of Object.entries(paths)) {
  if (sheetName !== inputSheetName) otherSheetHashes[sheetName] = sha(await inputZip.file(sheetPath).async("nodebuffer"));
}

const sheetXml = await inputZip.file(targetSheetPath).async("string");
const blocks = rowBlocks(sheetXml);
const byRow = new Map(blocks.map((block) => [block.rowNumber, block.xml]));
const lastExistingRow = Math.max(...inputDates.values()) + 1;
const templateXml = byRow.get(lastExistingRow);
assert(templateXml, `${inputSheetName}: last dated row XML is missing`);
const templateStyles = styleMap(templateXml);
const lastPhysicalRow = Math.max(...blocks.map((block) => block.rowNumber));
const reusableBlankRows = [];
for (let rowNumber = lastExistingRow + 1; rowNumber <= lastPhysicalRow; rowNumber += 1) {
  const candidate = byRow.get(rowNumber);
  if (!candidate || !isStyledBlankRow(candidate)) break;
  reusableBlankRows.push(rowNumber);
}

const replacements = new Map();
const appendedRows = [];
const targetRowNumbers = {};
let appendIndex = 0;
for (const date of requestedDates) {
  const sourceRow = formalByDate.get(date);
  const existingIndex = inputDates.get(date);
  if (existingIndex !== undefined) {
    const rowNumber = existingIndex + 1;
    const currentXml = byRow.get(rowNumber);
    assert(currentXml, `${inputSheetName}: XML row ${rowNumber} missing for ${date}`);
    // Use the complete row style map rather than the individual-cell matcher.
    // Some sparse percentage cells are encoded as style-only entries in XLSX;
    // preserving this map keeps their number format when a current source
    // value is written into them.
    replacements.set(rowNumber, updateRow(currentXml, rowNumber, sourceRow, false, styleMap(currentXml)));
    targetRowNumbers[date] = rowNumber;
  } else {
    const reusable = reusableBlankRows[appendIndex];
    const rowNumber = reusable ?? lastPhysicalRow + (appendIndex - reusableBlankRows.length) + 1;
    const cloned = cloneRow(templateXml, lastExistingRow, rowNumber);
    const updated = updateRow(cloned, rowNumber, sourceRow, true, templateStyles);
    if (reusable !== undefined) replacements.set(rowNumber, updated);
    else appendedRows.push(updated);
    targetRowNumbers[date] = rowNumber;
    appendIndex += 1;
  }
}

let updatedSheetXml = sheetXml.replace(/<(?:x:)?row\b[^>]*\br="(\d+)"[^>]*>[\s\S]*?<\/(?:x:)?row>/g, (match, rawRowNumber) => (
  replacements.get(Number(rawRowNumber)) ?? match
));
if (appendedRows.length) updatedSheetXml = updatedSheetXml.replace(/<\/(?:x:)?sheetData>/, `${appendedRows.join("")}</sheetData>`);
updatedSheetXml = updateDimension(updatedSheetXml, Math.max(...Object.values(targetRowNumbers)));
inputZip.file(targetSheetPath, updatedSheetXml);
workbookXml = renameSheet(workbookXml, inputSheetName, outputSheetName);
inputZip.file("xl/workbook.xml", workbookXml);
if (!reuseOutput) {
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, await inputZip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 6 } }));
}

const outputSha = await fileSha(outputPath);
const outputWorkbook = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
const expectedNames = inputNames.map((name) => name === inputSheetName ? outputSheetName : name);
assert(JSON.stringify(outputWorkbook.worksheets.items.map((sheet) => sheet.name)) === JSON.stringify(expectedNames), "Output sheet order/name mismatch");
for (const sheetName of inputNames) {
  const beforeValues = inputWorkbook.worksheets.getItem(sheetName).getUsedRange(false).values;
  const afterName = sheetName === inputSheetName ? outputSheetName : sheetName;
  const afterValues = outputWorkbook.worksheets.getItem(afterName).getUsedRange(false).values;
  assert(protectedHash(beforeValues) === protectedHash(afterValues), `${sheetName}: protected history changed`);
}
const outputValues = outputWorkbook.worksheets.getItem(outputSheetName).getUsedRange(false).values;
const outputDates = dateMap(outputValues, outputSheetName);
for (const date of requestedDates) {
  assert(outputDates.has(date), `${outputSheetName}: missing ${date}`);
  const actual = outputValues[outputDates.get(date)].slice(0, SOURCE_COLUMNS);
  const expected = formalByDate.get(date);
  for (let column = 0; column < SOURCE_COLUMNS; column += 1) {
    assert(sameCell(actual[column], expected[column], column), `${outputSheetName}: source mismatch ${date} column ${column + 1}`);
  }
}

const outputZip = await JSZip.loadAsync(await fs.readFile(outputPath));
for (const [sheetName, inputHash] of Object.entries(otherSheetHashes)) {
  assert(sha(await outputZip.file(paths[sheetName]).async("nodebuffer")) === inputHash, `${sheetName}: worksheet XML changed unexpectedly`);
}
const outputSheetXml = await outputZip.file(targetSheetPath).async("string");
for (const date of requestedDates.filter((value) => inputDates.has(value))) {
  const beforeStyle = styleMap(byRow.get(targetRowNumbers[date]));
  const afterStyle = styleMap(rowBlocks(outputSheetXml).find((block) => block.rowNumber === targetRowNumbers[date]).xml);
  assert(sameStyleMap(beforeStyle, afterStyle), `${outputSheetName}: style changed on existing ${date}`);
}
const appendedDate = requestedDates.find((date) => !inputDates.has(date));
if (appendedDate) {
  const appendedStyle = styleMap(rowBlocks(outputSheetXml).find((block) => block.rowNumber === targetRowNumbers[appendedDate]).xml);
  assert(sameStyleMap(templateStyles, appendedStyle), `${outputSheetName}: appended row style diverged from template`);
}

const formulaErrors = await outputWorkbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "formula error scan",
});
assert(!formulaErrors.ndjson.includes('"kind":"match"'), "Formula error scan failed");

const renderedRanges = [];
if (!skipRender) {
  const boundaryStart = Math.max(1, targetRowNumbers["2026-07-12"] - 1);
  await writePng(outputWorkbook, outputSheetName, `A${boundaryStart}:AR${targetRowNumbers["2026-07-15"]}`, path.join(runDir, "qa-previews", "boundary-2026-07-12_2026-07-15.png"));
  await writePng(outputWorkbook, outputSheetName, `A${targetRowNumbers["2026-08-14"]}:AR${targetRowNumbers[endDate]}`, path.join(runDir, "qa-previews", "tail-2026-08-14_2026-08-17.png"));
  renderedRanges.push("boundary-2026-07-12_2026-07-15.png", "tail-2026-08-14_2026-08-17.png");
}

const report = {
  status: "ok",
  generated_at: new Date().toISOString(),
  input: { path: inputPath, sha256: inputSha },
  output: { path: outputPath, sha256: outputSha },
  source: { path: sourceManifestPath, sha256: await fileSha(sourceManifestPath) },
  correction: {
    prior_sheet_name: inputSheetName,
    output_sheet_name: outputSheetName,
    filters: { package_channel: "wajebetH5", attribution_media: null, attribution_channel: null },
    requested_range: { start: startDate, end: endDate, dates: requestedDates.length },
    sample_validation: sampleChecks,
    accepted_sample_revisions: acceptedSampleRevisions,
  },
  checks: {
    source_header_order: "passed",
    source_dates_complete_unique: "passed",
    protected_history_through_2026_07_13: "passed",
    output_values_match_source: "passed",
    existing_row_styles_preserved: "passed",
    appended_row_style_clone: appendedDate ? "passed" : "not_applicable",
    other_worksheet_xml_unchanged: "passed",
    formula_error_scan: "passed",
    rendered_ranges: renderedRanges,
    visual_render_status: skipRender ? "skipped_after_renderer_timeout; XML styles and local-source format verified" : "passed",
  },
};
await fs.writeFile(path.join(runDir, "validation-report.json"), JSON.stringify(report, null, 2));
await fs.writeFile(path.join(runDir, "run-receipt.json"), JSON.stringify({
  status: "ok",
  generated_at: report.generated_at,
  output: outputPath,
  validation_report: path.join(runDir, "validation-report.json"),
}, null, 2));
console.log(JSON.stringify({ status: "ok", output: outputPath, validation_report: path.join(runDir, "validation-report.json") }));
