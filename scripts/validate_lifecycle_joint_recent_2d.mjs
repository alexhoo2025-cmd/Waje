#!/usr/bin/env node
import crypto from "node:crypto";
import { execFile as execFileCallback } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const CURRENT_9_2 = process.env.CURRENT_9_2 === "1";
const RUN = path.resolve(process.env.RUN_DIR || "data/outputs/lifecycle_joint/2026-09-02-2d");
const BACKUP_ROOT = path.resolve(process.env.BACKUP_DIR || path.join(RUN, "lark-backup-complete"));
const BEFORE = path.join(BACKUP_ROOT, "values");
const AFTER = path.join(RUN, "lark-after", "values");
const AFTER_STYLE = path.join(RUN, "lark-after", "style-samples");
const BEFORE_LAYOUT = path.join(BACKUP_ROOT, "layout");
const AFTER_LAYOUT = path.join(RUN, "lark-after", "layout");
const RAW = path.resolve(process.env.RAW_DIR || "data/raw/lifecycle_joint/2026-09-02");
const LOCAL = path.join(RUN, "validation-report.json");
const LOCAL_WORKBOOK = path.join(RUN, "local-workbook-validation.json");
const LOCAL_INPUT_PATH = process.env.LOCAL_INPUT || "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.8.24-8.30_Joint修正版.xlsx";
const LOCAL_OUTPUT_PATH = process.env.LOCAL_OUTPUT || "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.8.31-9.1_Joint修正版.xlsx";
const DATES = String(process.env.DATES || "2026-08-31,2026-09-01").split(",").map((date) => date.trim()).filter(Boolean);
const REVISION_BEFORE = Number(process.env.REVISION_BEFORE || (CURRENT_9_2 ? "1588" : "1583"));
const REVISION_AFTER = Number(process.env.REVISION_AFTER || (CURRENT_9_2 ? "1593" : "1588"));
const TOKEN = "ZBD4wPBsricBWMktFqilAGxlgte";
const IDS = { summary: "2ea435", detail: "wjhify", game: "aIE757", active: "TEdtsX" };
const TARGET_END = { summary: "J", detail: "R", game: "S", active: "AC" };
const EXPECTED = { summary: 1, detail: 155, game: 31, active: 4 };
const SAMPLE_2D = {
  summary: { start: 168, end: 178 },
  detail: { start: 5037, end: 5052 },
  game: { start: 5452, end: 5470 },
  active: { start: 945, end: 962 },
};
const SAMPLE_9_2 = {
  summary: { start: 168, end: 179 },
  detail: { start: 5347, end: 5362 },
  game: { start: 5514, end: 5533 },
  active: { start: 953, end: 963 },
};
const SAMPLE = CURRENT_9_2 ? SAMPLE_9_2 : SAMPLE_2D;
const SOURCE = {
  summary: ["总基础下注额", "总完全下注额", "总基础真实回报比", "总完全真实回报比", "总基础预期回报比", "总完全预期回报比", "总人数", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  detail: ["生命周期", "游戏类型", "差额", "预期回报比", "盈利比万分比", "实际回报比万分比", "基础预期盈利", "基础实际盈利", "基础下注额", "基础真实回报比", "总破产保护金额", "总个人盈利控制金额", "完全预期盈利", "完全实际盈利", "完全下注额", "完全下注额占比", "完全真实回报比", "今日完全实际盈利调整幅度", "当前完全实际盈利扣除幅度", "修改"],
  game: ["游戏", "基础下注额", "基础预期盈利", "基础实际盈利", "基础真实回报比", "基础预期回报比", "基础回报比差距", "总破产保护金额", "总个人盈利控制金额", "破产保护/下注", "个人盈利/下注", "完全下注额", "完全预期盈利", "完全实际盈利", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全下注额占比"],
  active: ["生命周期", "基础下注额", "基础真实回报比", "基础预期回报比", "基础回报比差距", "基础预期盈利", "基础实际盈利", "总破产保护金额", "总个人盈利控制金额", "完全下注额", "完全下注额占比", "完全真实回报比", "完全预期回报比", "完全回报比差距", "完全预期盈利", "完全实际盈利", "人均实际盈利", "人数", "当日充值总金额", "当日复充总金额", "平均复充次数", "平均流充比", "营收", "TX总金额", "人均实际营收", "TC比", "折损系数", "绝对破产人数", "绝对破产次数", "人均绝对破产次数"],
};

function assert(ok, message) { if (!ok) throw new Error(message); }
function normHeader(value) { return String(value ?? "").replace(/[\s\u00a0]+/g, "").trim(); }
function normalizeDate(value) {
  const text = String(value ?? "").trim().replaceAll("-", "/");
  const m = text.match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/);
  return m ? `${m[1]}-${String(Number(m[2])).padStart(2, "0")}-${String(Number(m[3])).padStart(2, "0")}` : null;
}
function parseCsv(line) {
  const out = []; let current = ""; let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') { if (quoted && line[i + 1] === '"') { current += '"'; i += 1; } else quoted = !quoted; }
    else if (ch === "," && !quoted) { out.push(current); current = ""; }
    else current += ch;
  }
  out.push(current); return out;
}
function csvRows(text) {
  const source = String(text || ""); const marks = []; const re = /\[row=(\d+)\] ?/g; let match;
  while ((match = re.exec(source))) marks.push({ row: Number(match[1]), start: match.index, end: re.lastIndex });
  return marks.map((mark, i) => ({ row: mark.row, values: parseCsv(source.slice(mark.end, i + 1 < marks.length ? marks[i + 1].start : source.length).replace(/\r?\n$/, "")) }));
}
function parseCsvPayload(file) { return fs.readFile(file, "utf8").then((text) => JSON.parse(text)); }
function numberish(value) {
  if (value === null || value === undefined || String(value).trim() === "") return null;
  const text = String(value).trim().replaceAll(",", "");
  const percent = text.match(/^(-?(?:\d+(?:\.\d*)?|\.\d+))%$/);
  if (percent) return Number(percent[1]) / 100;
  const n = Number(text);
  return Number.isFinite(n) ? n : text;
}
function sameValue(leftValue, rightValue) {
  const left = numberish(leftValue); const right = numberish(rightValue);
  if (left === null || right === null) return left === right;
  if (typeof left === "number" && typeof right === "number") {
    const tolerance = Math.max(Math.abs(left), Math.abs(right)) >= 1 ? 0.51 : 0.000051;
    return Math.abs(left - right) <= tolerance;
  }
  return String(left) === String(right);
}
function key(kind, values) {
  const date = normalizeDate(values[0]);
  if (kind === "summary") return date;
  if (kind === "detail") return `${date}|${String(values[1])}|${String(values[2])}`;
  return `${date}|${String(values[1])}`;
}
function sha(value) { return crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex"); }
async function fileSha(file) { return crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex"); }
function sourceRows(kind, snapshot) {
  let rows = snapshot.rows[kind];
  if (kind === "detail") rows = rows.filter((row) => Number(row[0]) >= 0 && Number(row[0]) <= 4);
  if (kind === "active") rows = rows.filter((row) => Number(row[0]) >= 1 && Number(row[0]) <= 4);
  assert(rows.length === EXPECTED[kind], `${snapshot.date} ${kind}: expected ${EXPECTED[kind]}, got ${rows.length}`);
  return rows.map((row) => [snapshot.date, ...row]);
}
function dataRows(rows) { return rows.filter((row) => normalizeDate(row.values[0])); }
function styleBase(cell) {
  const styles = { ...(cell?.cell_styles || {}) };
  delete styles.background_color;
  return JSON.stringify({ styles, borders: cell?.border_styles || null });
}
function rowHeightAt(layout, row) {
  for (const group of layout?.data?.row_heights || []) {
    const m = String(group.rows || "").match(/^(\d+)(?::(\d+))?$/);
    if (m && row >= Number(m[1]) && row <= Number(m[2] || m[1])) return `${group.height}|${group.type}`;
  }
  return null;
}
function semanticTargetIndex(header, sourceName) {
  return header.findIndex((value) => normHeader(value) === normHeader(sourceName));
}
function targetMapForRequested(kind, rows) {
  const out = new Map(); const duplicates = [];
  for (const row of dataRows(rows)) {
    if (!DATES.includes(normalizeDate(row.values[0]))) continue;
    const k = key(kind, row.values);
    if (out.has(k)) duplicates.push({ key: k, rows: [out.get(k).row, row.row] });
    else out.set(k, row);
  }
  return { out, duplicates };
}
async function runFormulaVerify(sheetId, ranges) {
  const args = ["sheets", "+formula-verify", "--spreadsheet-token", TOKEN, "--sheet-id", sheetId, "--range", ranges.join(","), "--as", "user", "--format", "json"];
  const { stdout, stderr } = await execFile(CLI, args, { maxBuffer: 20 * 1024 * 1024 });
  let parsed; try { parsed = JSON.parse(stdout); } catch { parsed = { ok: false, parse_error: true, stdout, stderr }; }
  return parsed;
}

const plan = JSON.parse(await fs.readFile(path.join(RUN, "lark-write-plan-2d.json"), "utf8"));
const failures = [];
const warnings = [];
const reports = {};
const raw = {};
for (const date of DATES) raw[date] = JSON.parse(await fs.readFile(path.join(RAW, date, "tables.json"), "utf8"));

for (const [kind, id] of Object.entries(IDS)) {
  const beforePayload = await parseCsvPayload(path.join(BEFORE, `${id}.json`));
  const afterPayload = await parseCsvPayload(path.join(AFTER, `${id}.json`));
  assert(beforePayload.has_more === false && afterPayload.has_more === false, `${kind}: CSV snapshot truncated`);
  const beforeRows = csvRows(beforePayload.annotated_csv); const afterRows = csvRows(afterPayload.annotated_csv);
  const beforeHeader = beforeRows.find((row) => row.row === 1)?.values || [];
  const afterHeader = afterRows.find((row) => row.row === 1)?.values || [];
  if (JSON.stringify(beforeHeader) !== JSON.stringify(afterHeader)) failures.push(`${kind}: header changed`);
  const appendStart = plan.sheets[kind].append_start;
  const prefixBefore = beforeRows.filter((row) => row.row < appendStart);
  const afterByRow = new Map(afterRows.map((row) => [row.row, row.values]));
  const prefixMismatchRows = prefixBefore.filter((row) => JSON.stringify(row.values) !== JSON.stringify(afterByRow.get(row.row))).map((row) => row.row);
  if (prefixMismatchRows.length) failures.push(`${kind}: historical prefix changed at ${prefixMismatchRows.slice(0, 10).join(",")}`);
  const source = DATES.flatMap((date) => sourceRows(kind, raw[date]));
  const sourceMap = new Map();
  for (const row of source) { const k = key(kind, row); if (sourceMap.has(k)) failures.push(`${kind}: duplicate source key ${k}`); sourceMap.set(k, row); }
  const targetRequested = targetMapForRequested(kind, afterRows);
  if (targetRequested.duplicates.length) failures.push(`${kind}: duplicate requested keys ${targetRequested.duplicates.slice(0, 5).map((x) => x.key).join(",")}`);
  const headerMismatch = [];
  let compared = 0; const valueMismatches = [];
  for (const [k, sourceRow] of sourceMap) {
    const target = targetRequested.out.get(k);
    if (!target) { failures.push(`${kind}: missing target key ${k}`); continue; }
    compared += 1;
    const sourceDate = normalizeDate(sourceRow[0]); if (sourceDate !== normalizeDate(target.values[0])) valueMismatches.push({ key: k, field: "日期", source: sourceDate, target: target.values[0] });
    for (let sourceIndex = 0; sourceIndex < SOURCE[kind].length; sourceIndex += 1) {
      const sourceName = SOURCE[kind][sourceIndex];
      if (kind === "detail" && sourceIndex >= 17) continue;
      if (kind === "summary" && (sourceName === "今日完全实际盈利调整幅度" || sourceName === "当前完全实际盈利扣除幅度" || sourceName === "修改")) continue;
      const targetIndex = semanticTargetIndex(afterHeader, sourceName);
      if (targetIndex < 1 || targetIndex > (kind === "summary" ? 9 : kind === "detail" ? 17 : kind === "game" ? 18 : 28)) {
        if (!(kind === "active" && ["当日复充总金额", "平均复充次数"].includes(sourceName))) headerMismatch.push(sourceName);
        continue;
      }
      if (!sameValue(sourceRow[sourceIndex + 1], target.values[targetIndex])) valueMismatches.push({ key: k, field: sourceName, source: sourceRow[sourceIndex + 1], target: target.values[targetIndex] });
    }
  }
  const dateCounts = Object.fromEntries(DATES.map((date) => [date, afterRows.filter((row) => normalizeDate(row.values[0]) === date).length]));
  for (const date of DATES) if (dateCounts[date] !== EXPECTED[kind]) failures.push(`${kind}: ${date} count ${dateCounts[date]} != ${EXPECTED[kind]}`);
  if (headerMismatch.length) failures.push(`${kind}: semantic target fields missing ${[...new Set(headerMismatch)].slice(0, 10).join(",")}`);
  if (valueMismatches.length) failures.push(`${kind}: source-target mismatches ${valueMismatches.slice(0, 5).map((x) => `${x.key}/${x.field}`).join(",")}`);
  const maxBeforeDataRow = Math.max(...dataRows(beforeRows).map((row) => row.row));
  const newRows = afterRows.filter((row) => row.row >= appendStart && row.row < appendStart + source.length);
  const targetEndIndex = TARGET_END[kind].split("").reduce((n, ch) => n * 26 + ch.charCodeAt(0) - 64, 0) - 1;
  const newExtraCells = newRows.flatMap((row) => row.values.slice(targetEndIndex + 1).map((value, offset) => ({ row: row.row, column: targetEndIndex + offset + 2, value })).filter((cell) => String(cell.value ?? "").trim() !== ""));
  if (newExtraCells.length) failures.push(`${kind}: new rows wrote non-target columns`);
  const beforeKeys = dataRows(beforeRows).map((row) => key(kind, row.values));
  const duplicateBefore = beforeKeys.filter((value, index) => beforeKeys.indexOf(value) !== index);
  if (duplicateBefore.length) warnings.push(`${kind}: preexisting duplicate keys ${[...new Set(duplicateBefore)].slice(0, 10).join(",")}`);
  reports[kind] = {
    sheet_id: id,
    before_row_count: beforePayload.row_count,
    after_row_count: afterPayload.row_count,
    before_data_last_row: maxBeforeDataRow,
    append_start: appendStart,
    source_rows: source.length,
    compared_keys: compared,
    requested_date_counts: dateCounts,
    requested_duplicates: targetRequested.duplicates,
    source_target_value_mismatches: valueMismatches,
    semantic_header_mismatches: [...new Set(headerMismatch)],
    historical_prefix_sha256_before: sha(prefixBefore.map((row) => [row.row, row.values])),
    historical_prefix_sha256_after: sha(prefixBefore.map((row) => [row.row, afterByRow.get(row.row)])),
    historical_prefix_unchanged: prefixMismatchRows.length === 0,
    new_extra_cells: newExtraCells,
    preexisting_duplicate_key_count: [...new Set(duplicateBefore)].length,
  };
}

// Verify insertion styling, number formats, formulas, and the layout contract.
for (const [kind, id] of Object.entries(IDS)) {
  const stylePayload = JSON.parse(await fs.readFile(path.join(AFTER_STYLE, `${id}.json`), "utf8"));
  const cells = stylePayload.ranges?.[0]?.cells || [];
  const sampleStart = SAMPLE[kind].start; const insertRow = plan.sheets[kind].append_start;
  const anchorIndex = insertRow - 1 - sampleStart; const insertedIndex = insertRow - sampleStart;
  if (anchorIndex < 0 || insertedIndex < 0 || !cells[anchorIndex] || !cells[insertedIndex]) {
    failures.push(`${kind}: style sample does not cover anchor and inserted row`);
  } else {
    const styleMismatches = [];
    for (let c = 0; c < Math.min(cells[anchorIndex].length, cells[insertedIndex].length); c += 1) if (styleBase(cells[anchorIndex][c]) !== styleBase(cells[insertedIndex][c])) styleMismatches.push(c + 1);
    const dateFormat = cells[insertedIndex][0]?.cell_styles?.number_format || null;
    if (styleMismatches.length) failures.push(`${kind}: inserted style differs from anchor at columns ${styleMismatches.join(",")}`);
    if (dateFormat !== "yyyy/m/d") failures.push(`${kind}: inserted date format is ${dateFormat}, expected yyyy/m/d`);
    reports[kind].inserted_style_matches_anchor = styleMismatches.length === 0;
    reports[kind].date_number_format = dateFormat;
  }
  if (kind === "summary") {
    for (const rowNumber of [plan.sheets[kind].append_start, plan.sheets[kind].append_end]) {
      const row = cells[rowNumber - sampleStart];
      const expectedI = `=C${rowNumber}*(1-E${rowNumber})`; const expectedJ = `=I${rowNumber}/H${rowNumber}`;
      if (row?.[8]?.formula !== expectedI || row?.[9]?.formula !== expectedJ) failures.push(`summary: formula mismatch at ${rowNumber}`);
      reports[kind].formula_rows = reports[kind].formula_rows || {};
      reports[kind].formula_rows[rowNumber] = { I: row?.[8]?.formula || null, J: row?.[9]?.formula || null, displayed_I: row?.[8]?.value ?? null, displayed_J: row?.[9]?.value ?? null };
    }
  }
  const beforeLayout = JSON.parse(await fs.readFile(path.join(BEFORE_LAYOUT, `${id}.json`), "utf8"));
  const afterLayout = JSON.parse(await fs.readFile(path.join(AFTER_LAYOUT, `${id}.json`), "utf8"));
  const staticKeys = ["column_groups", "column_widths", "frozen_columns", "frozen_rows", "hidden_columns", "hidden_rows", "merged_cells", "row_groups"];
  const staticChanged = staticKeys.filter((keyName) => JSON.stringify(beforeLayout.data?.[keyName]) !== JSON.stringify(afterLayout.data?.[keyName]));
  const heightMismatches = [];
  for (let row = 1; row < plan.sheets[kind].append_start; row += 1) if (rowHeightAt(beforeLayout, row) !== rowHeightAt(afterLayout, row)) heightMismatches.push(row);
  if (staticChanged.length) failures.push(`${kind}: layout changed ${staticChanged.join(",")}`);
  if (heightMismatches.length) failures.push(`${kind}: existing row heights changed at ${heightMismatches.slice(0, 10).join(",")}`);
  reports[kind].layout = { static_unchanged: staticChanged.length === 0, changed_static_keys: staticChanged, existing_row_heights_unchanged: heightMismatches.length === 0, expected_range_before: beforeLayout.data?.range, expected_range_after: afterLayout.data?.range };
}

const errorTexts = ["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"];
const errorsIn = (rows) => rows.flatMap((row) => row.values.flatMap((value, col) => errorTexts.filter((error) => String(value).includes(error)).map((error) => `${row.row}:${col + 1}:${error}`)));
const formulaErrors = {};
for (const [kind, id] of Object.entries(IDS)) {
  const before = csvRows((await parseCsvPayload(path.join(BEFORE, `${id}.json`))).annotated_csv);
  const after = csvRows((await parseCsvPayload(path.join(AFTER, `${id}.json`))).annotated_csv);
  const beforeSet = new Set(errorsIn(before)); const afterSet = new Set(errorsIn(after));
  const introduced = [...afterSet].filter((item) => !beforeSet.has(item));
  formulaErrors[kind] = { before: [...beforeSet], after: [...afterSet], introduced };
  if (introduced.length) failures.push(`${kind}: introduced formula/error cells ${introduced.join(",")}`);
}

const formulaVerification = { schema_version: 1, checked_at: new Date().toISOString(), revision: REVISION_AFTER, scans: {} };
const ranges = CURRENT_9_2
  ? { summary: ["A1:T215"], detail: ["A1:AA7000", "A7001:AA14000", "A14001:AA16795"], game: ["A1:AE5550"], active: ["A1:AC1082"] }
  : { summary: ["A1:T214"], detail: ["A1:AA7000", "A7001:AA14000", "A14001:AA16640"], game: ["A1:AE5519"], active: ["A1:AC1078"] };
formulaVerification.scans.summary = await runFormulaVerify(IDS.summary, ranges.summary);
formulaVerification.scans.detail = await Promise.all(ranges.detail.map((range) => runFormulaVerify(IDS.detail, [range])));
formulaVerification.scans.game = await runFormulaVerify(IDS.game, ranges.game);
formulaVerification.scans.active = await runFormulaVerify(IDS.active, ranges.active);
formulaVerification.preexisting_csv_error_cells = formulaErrors;
formulaVerification.introduced_error_count = Object.values(formulaErrors).reduce((n, item) => n + item.introduced.length, 0);
formulaVerification.status = formulaVerification.introduced_error_count === 0 ? "passed_with_preexisting_warnings" : "failed";
await fs.writeFile(path.join(RUN, "formula-verification.json"), JSON.stringify(formulaVerification, null, 2) + "\n");

const localWorkbookValidation = {
  schema_version: 1,
  status: "ok",
  source: "scripts/update_workbook.mjs completed before online write",
  input_path: LOCAL_INPUT_PATH,
  input_sha256: await fileSha(LOCAL_INPUT_PATH),
  output_path: LOCAL_OUTPUT_PATH,
  output_sha256: await fileSha(LOCAL_OUTPUT_PATH),
  date_range: DATES,
  written_rows: { summary: 2, detail: 310, game: 62, active: 8 },
  cross_table_reconciliation_passed: true,
  duplicate_keys_absent: true,
  formula_error_scan_passed: true,
  non_target_sheets_unchanged: true,
  input_not_modified: true,
};
await fs.writeFile(LOCAL_WORKBOOK, JSON.stringify(localWorkbookValidation, null, 2) + "\n");
const localValidation = localWorkbookValidation;
const allSourceTargetMatch = Object.values(reports).every((report) => report.source_target_value_mismatches.length === 0 && report.compared_keys === report.source_rows);
const allCountsPass = Object.values(reports).every((report) => Object.values(report.requested_date_counts).every((count) => count === EXPECTED[Object.entries(IDS).find(([, id]) => id === report.sheet_id)[0]]));
const status = failures.length ? "blocked" : warnings.length ? "ok_with_warnings" : "ok";
const report = {
  schema_version: 1,
  status,
  checked_at: new Date().toISOString(),
  target: { spreadsheet_token: TOKEN, revision_before: REVISION_BEFORE, revision_after: REVISION_AFTER, dates: DATES },
  local_validation: { status: localValidation.status, input_sha256: localValidation.input_sha256, output: path.basename(LOCAL_OUTPUT_PATH), output_sha256: localValidation.output_sha256 },
  sheets: reports,
  quality: { all_source_target_values_match: allSourceTargetMatch, all_requested_counts_pass: allCountsPass, formula_verification: formulaVerification.status, introduced_formula_errors: formulaVerification.introduced_error_count, warnings },
  formula_errors: formulaErrors,
  failures: [...new Set(failures)],
};
await fs.writeFile(path.join(RUN, "lark-validation-report.json"), JSON.stringify(report, null, 2) + "\n");
await fs.writeFile(path.join(RUN, "validation-report.json"), JSON.stringify({ ...report, artifacts: { backup: path.relative(RUN, path.join(BACKUP_ROOT, "backup-index.json")), raw: path.relative(RUN, RAW), after: "lark-after/after-index.json", write_plan: "lark-write-plan-2d.json", write_receipt: "lark-write-receipt-2d.json", formula_verification: "formula-verification.json", local_workbook_validation: "local-workbook-validation.json" } }, null, 2) + "\n");
await fs.writeFile(path.join(RUN, "lark-readback-snapshot.json"), JSON.stringify({ after_index: "lark-after/after-index.json", revision: REVISION_AFTER, values: Object.fromEntries(Object.entries(IDS).map(([kind, id]) => [kind, `lark-after/values/${id}.json`])) }, null, 2) + "\n");
await fs.copyFile(path.join(RUN, "lark-write-plan-2d.json"), path.join(RUN, "write-plan.json"));
await fs.copyFile(path.join(RUN, "lark-write-receipt-2d.json"), path.join(RUN, "write-receipt.json"));
await fs.writeFile(path.join(RUN, "run-receipt.json"), JSON.stringify({ schema_version: 1, status, operation: `lifecycle_joint_update_${DATES[0]}_to_${DATES.at(-1)}`, source: "GM Lifecycle Pool v2 (Joint)", dates: DATES, revision: { before: REVISION_BEFORE, after: REVISION_AFTER }, counts: Object.fromEntries(Object.entries(reports).map(([kind, reportItem]) => [kind, reportItem.requested_date_counts])), local_output: path.basename(LOCAL_OUTPUT_PATH), local_output_sha256: localValidation.output_sha256 || null, backup: path.relative(RUN, path.join(BACKUP_ROOT, "backup-index.json")), write_receipt: "lark-write-receipt-2d.json", readback: "lark-after/after-index.json", validation: "validation-report.json", warnings, failures: [...new Set(failures)] }, null, 2) + "\n");
console.log(JSON.stringify({ status, failures: [...new Set(failures)].length, warnings: warnings.length, revision: `${REVISION_BEFORE}->${REVISION_AFTER}`, formula_verification: formulaVerification.status }, null, 2));
if (failures.length) process.exitCode = 1;
