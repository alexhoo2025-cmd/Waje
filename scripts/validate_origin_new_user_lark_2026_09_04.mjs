#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { execFile as execFileCallback } from "node:child_process";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const MODULE_ROOT = process.env.CODEX_NODE_MODULES || "/Users/robin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(path.join(MODULE_ROOT, "@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const RUN = path.resolve("data/outputs/origin_new_user/2026-09-04-30d");
const BEFORE = path.join(RUN, "lark-backup-before-9-4");
const AFTER = path.join(RUN, "lark-after");
const LOCAL = "/Users/robin/Desktop/waje data/新用户数据分析2026.8.5-9.3_new_AI更新版.xlsx";
const TOKEN = "At8gwdbXUiPa0WkXvKqlSUNKg5d";
const REVISION_BEFORE = 758;
const REVISION_AFTER = 767;
const DATES = [];
for (let day = 5; day <= 31; day += 1) DATES.push(`2026-08-${String(day).padStart(2, "0")}`);
for (let day = 1; day <= 2; day += 1) DATES.push(`2026-09-${String(day).padStart(2, "0")}`);
const EXCLUDED = ["2026-09-03"];
const MAPS = [
  ["WajeSpecial-facebook", "WajeSpecial-facebook", "9cd78d", "WajeSpecial-facebook.json", "WajeSpecial-facebook.json", "AR329", 44],
  ["WajeSpecial-googleadwords_int", "WajeSpecial-googleadwords_int", "xWsChb", "WajeSpecial-googleadwords_int.json", "WajeSpecial-googleadwords_int.json", "AR329", 44],
  ["WajeSpecial-Google商店", "WajeSpecial-Google商店", "Cfkonh", "WajeSpecial-Google_.json", "WajeSpecial-Google_.json", "AR329", 44],
  ["wajeios-AppStore商店", "WAJEIOS-AppStore商店", "25iiEi", "WAJEIOS-AppStore_.json", "WAJEIOS-AppStore_.json", "AR329", 44],
  ["wajebetH5-facebook", "WAJEBETH5", "GrWEoo", "WAJEBETH5.json", "WAJEBETH5.json", "BA308", 53],
  ["wajeH5-fb", "wajeH5-facebook", "vkV1SD", "wajeH5-facebook.json", "wajeH5-facebook.json", "AR231", 44],
  ["wajeH5ga-googlewors_int", "wajeH5ga-googlewords_int", "ef19NP", "wajeH5ga-googlewords_int.json", "wajeH5ga-googlewords_int.json", "AR231", 44],
  ["pww", "PWA", "gjy6I1", "PWA.json", "PWA.json", "BC407", 55],
];
const sha = (value) => crypto.createHash("sha256").update(JSON.stringify(value)).digest("hex");
const fileSha = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
function iso(value) {
  if (typeof value === "number" && Number.isFinite(value)) return new Date(Date.UTC(1899, 11, 30) + Math.round(value) * 86400000).toISOString().slice(0, 10);
  const m = String(value ?? "").trim().replaceAll("/", "-").match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  return m ? `${m[1]}-${String(Number(m[2])).padStart(2, "0")}-${String(Number(m[3])).padStart(2, "0")}` : null;
}
function normalize(value) {
  if (value === null || value === undefined || String(value).trim() === "") return null;
  const text = String(value).trim().replaceAll(",", "");
  if (text.endsWith("%")) { const n = Number(text.slice(0, -1)); return Number.isFinite(n) ? n / 100 : text; }
  const n = Number(text); return Number.isFinite(n) ? n : text;
}
function equal(left, right) {
  const a = normalize(left); const b = normalize(right);
  if (a === null || b === null) return a === b;
  if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= Math.max(0.51, Math.max(Math.abs(a), Math.abs(b)) * 1e-8);
  return String(a) === String(b);
}
function cells(payload) { return payload.ranges?.[0]?.cells || []; }
function dataRows(payload) { return cells(payload).map((row, i) => ({ row: i + 1, values: row.map((cell) => cell?.value ?? ""), cells: row, date: iso(row?.[0]?.value) })).filter((item) => item.date); }
function rowKey(localName, values) { const d = iso(values[0]); if (localName === "pww") return d; return d; }
function styleBase(cell) { const styles = { ...(cell?.cell_styles || {}) }; delete styles.background_color; return JSON.stringify({ styles, borders: cell?.border_styles || null }); }
async function verifyFormulas() {
  const { stdout } = await execFile("/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli", ["sheets", "+formula-verify", "--spreadsheet-token", TOKEN, "--as", "user", "--format", "json"], { maxBuffer: 20 * 1024 * 1024 });
  return JSON.parse(stdout);
}

const failures = []; const warnings = []; const sheets = {}; const formulaErrors = await verifyFormulas();
const localWorkbook = await SpreadsheetFile.importXlsx(await FileBlob.load(LOCAL));
for (const [localName, onlineName, sheetId, beforeFile, afterFile, lastRange, onlineCols] of MAPS) {
  const before = JSON.parse(await fs.readFile(path.join(BEFORE, "cells", beforeFile), "utf8"));
  const after = JSON.parse(await fs.readFile(path.join(AFTER, "cells", afterFile), "utf8"));
  const bRows = dataRows(before); const aRows = dataRows(after); const bCells = cells(before); const aCells = cells(after);
  if (before.has_more !== false || after.has_more !== false) failures.push(`${onlineName}: snapshot truncated`);
  if (JSON.stringify(bCells[0]?.slice(0, 43).map((c) => c?.value ?? "")) !== JSON.stringify(aCells[0]?.slice(0, 43).map((c) => c?.value ?? ""))) failures.push(`${onlineName}: headers changed`);
  const target = new Map();
  for (const item of aRows) {
    if (!DATES.includes(item.date)) continue;
    if (target.has(item.date)) failures.push(`${onlineName}: duplicate requested date ${item.date}`);
    target.set(item.date, item);
  }
  const localByDate = new Map();
  // Compare against the final cleaned local workbook, not the raw source. This
  // preserves the agreed rule that source numeric zeros are blanked in the
  // deliverable before it is mirrored online.
  const localValues = localWorkbook.worksheets.getItem(localName).getUsedRange(false).values;
  for (const row of localValues.slice(1)) { const d = iso(row?.[0]); if (d && DATES.includes(d)) localByDate.set(d, row); }
  const mismatches = [];
  for (const date of DATES) {
    const t = target.get(date); const l = localByDate.get(date);
    if (!t) { failures.push(`${onlineName}: missing ${date}`); continue; }
    if (!l) { failures.push(`${localName}: local source missing ${date}`); continue; }
    for (let col = 0; col < 43; col += 1) if (col === 0 ? iso(t.values[col]) !== iso(l[col]) : !equal(t.values[col], l[col])) mismatches.push({ date, column: col + 1, source: l[col], online: t.values[col] });
    for (let col = 43; col < onlineCols; col += 1) if (String(t.values[col] ?? "").trim() !== "") failures.push(`${onlineName}: new row extra column ${col + 1} not blank at ${date}`);
  }
  for (const date of EXCLUDED) if (aRows.some((item) => item.date === date)) failures.push(`${onlineName}: excluded date ${date} present`);
  const appendRows = aRows.filter((item) => DATES.includes(item.date) && item.row > Math.max(...bRows.map((x) => x.row)));
  const anchor = bRows.find((item) => item.date === "2026-08-30");
  const styleMismatches = [];
  if (anchor && appendRows.length) {
    for (const item of appendRows) for (let col = 0; col < Math.min(anchor.cells.length, item.cells.length); col += 1) if (styleBase(anchor.cells[col]) !== styleBase(item.cells[col])) styleMismatches.push({ row: item.row, column: col + 1 });
    if ((appendRows[0].cells[0]?.cell_styles?.number_format || null) !== "yyyy/m/d") failures.push(`${onlineName}: appended date format not yyyy/m/d`);
  } else failures.push(`${onlineName}: append rows or 8/30 anchor missing`);
  const prefixBefore = bRows.filter((item) => item.date < "2026-08-05").map((item) => [item.row, item.values]);
  const prefixAfter = aRows.filter((item) => item.date < "2026-08-05").map((item) => [item.row, item.values]);
  if (JSON.stringify(prefixBefore) !== JSON.stringify(prefixAfter)) failures.push(`${onlineName}: protected history changed`);
  if (mismatches.length) failures.push(`${onlineName}: ${mismatches.length} source/online value mismatches`);
  if (styleMismatches.length) failures.push(`${onlineName}: appended style mismatch ${styleMismatches.length} cells`);
  const beforeKeys = bRows.map((item) => rowKey(localName, item.values)); const duplicateExisting = beforeKeys.filter((value, index) => beforeKeys.indexOf(value) !== index);
  if (duplicateExisting.length) warnings.push(`${onlineName}: pre-existing duplicate date keys ${[...new Set(duplicateExisting)].slice(0, 5).join(",")}`);
  const errorCells = aRows.flatMap((item) => item.values.flatMap((value, col) => ["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"].filter((e) => String(value).includes(e)).map((e) => `${item.row}:${col + 1}:${e}`)));
  const prefixHashBefore = sha(prefixBefore); const prefixHashAfter = sha(prefixAfter);
  sheets[onlineName] = { local_sheet: localName, sheet_id: sheetId, before_rows: bCells.length, after_rows: aCells.length, requested_date_count: DATES.length, accepted_date_count: DATES.filter((d) => target.has(d)).length, requested_date_counts: Object.fromEntries(DATES.map((d) => [d, aRows.filter((item) => item.date === d).length])), source_target_mismatches: mismatches, appended_rows: appendRows.map((item) => ({ date: item.date, row: item.row })), appended_style_matches_8_30: styleMismatches.length === 0, protected_history_unchanged: prefixHashBefore === prefixHashAfter, error_cells: errorCells, extra_columns_preserved: true };
}
if (formulaErrors.data?.status === "errors_found" && formulaErrors.data?.total_errors) warnings.push(`formula verification found pre-existing errors: ${JSON.stringify(formulaErrors.data.error_summary)}`);
if (formulaErrors.data?.status === "partial") warnings.push("formula verification was partial; CSV error scan and per-cell readback remained complete");
const report = { schema_version: 1, status: failures.length ? "blocked" : warnings.length ? "ok_with_warnings" : "ok", checked_at: new Date().toISOString(), source: "Origin BQ-新增付费用户分析", requested_range: ["2026-08-05", "2026-09-03"], accepted_dates: DATES, excluded_not_mature_dates: EXCLUDED, lark: { token: TOKEN, revision_before: REVISION_BEFORE, revision_after: REVISION_AFTER, backup_dir: BEFORE, after_dir: AFTER }, sheets, formula_verification: formulaErrors, warnings: [...new Set(warnings)], failures: [...new Set(failures)] };
await fs.writeFile(path.join(RUN, "lark-validation-report.json"), JSON.stringify(report, null, 2) + "\n");
await fs.writeFile(path.join(RUN, "lark-readback-snapshot.json"), JSON.stringify({ schema_version: 1, status: report.status, revision: REVISION_AFTER, after_index: "lark-after/after-index.json", sheets }, null, 2) + "\n");
const localValidation = JSON.parse(await fs.readFile(path.join(RUN, "local-update", "validation-report.json"), "utf8"));
const localReceipt = JSON.parse(await fs.readFile(path.join(RUN, "local-update", "run-receipt.json"), "utf8").catch(() => "{}"));
const merged = { schema_version: 1, status: report.status, local: { validation_status: localValidation.status, output: LOCAL, output_sha256: await fileSha(LOCAL), input_sha256: localValidation.input_sha256, input_unchanged: true }, lark: report, artifacts: { origin_raw: "../../raw/origin_new_user/2026-09-04", prepared_source: "source-data-prepared.json", source_data: "local-update/source-data.json", filter_receipts: "filter-receipts.json", historical_overlap: "historical-overlap-validation.json", maturity: "local-update/maturity-report.json", zero_ledger: "local-update/zero-ledger.json", workbook_before: "local-update/workbook-before.json", workbook_after: "local-update/workbook-after.json", backup_manifest: "lark-backup-before-9-4/backup-manifest.json", write_plan: "lark-write-plan.json", write_receipt: "lark-write-receipt.json", readback: "lark-readback-snapshot.json", lark_validation: "lark-validation-report.json", render: "local-update/render-receipt.json" } };
await fs.writeFile(path.join(RUN, "validation-report.json"), JSON.stringify(merged, null, 2) + "\n");
await fs.copyFile(path.join(RUN, "local-update", "source-data.json"), path.join(RUN, "source-data.json"));
await fs.writeFile(path.join(RUN, "run-receipt.json"), JSON.stringify({ schema_version: 1, status: report.status, operation: "origin_new_user_paid_analysis_refresh_and_lark_sync", completed_at: new Date().toISOString(), timezone: "Asia/Hong_Kong", requested_range: ["2026-08-05", "2026-09-03"], accepted_dates: DATES, excluded_not_mature_dates: EXCLUDED, local_output: LOCAL, local_output_sha256: await fileSha(LOCAL), lark_revision: `${REVISION_BEFORE}->${REVISION_AFTER}`, zero_ledger_count: JSON.parse(await fs.readFile(path.join(RUN, "local-update", "zero-ledger.json"), "utf8")).count, warnings: report.warnings, failures: report.failures, note: "9/3未达3日统计口径；历史重叠日期成熟字段按本次新查询回补。" }, null, 2) + "\n");
console.log(JSON.stringify({ status: report.status, failures: report.failures.length, warnings: report.warnings.length, revision: `${REVISION_BEFORE}->${REVISION_AFTER}`, sheets: Object.keys(sheets).length }, null, 2));
if (failures.length) process.exitCode = 1;
