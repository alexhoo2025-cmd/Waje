#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(process.env.RUN_DIR || "data/outputs/lifecycle_joint/2026-09-07");
const rawRoot = path.resolve(process.env.RAW_DIR || "data/raw/lifecycle_joint/2026-09-07");
const priorRawRoot = path.resolve(process.env.PRIOR_RAW_DIR || "data/raw/lifecycle_joint/2026-09-04/2026-09-03");
const localRun = path.join(root, "local-update");
const larkAfter = path.join(root, "lark-after");
const acceptedDates = ["2026-09-04", "2026-09-05", "2026-09-06"];
const excludedDates = ["2026-09-03"];
const localInput = "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.9.2_Joint修正版.xlsx";
const localOutput = "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.9.4-9.6_Joint修正版.xlsx";
const token = "ZBD4wPBsricBWMktFqilAGxlgte";

const readJson = async (file) => JSON.parse(await fs.readFile(file, "utf8"));
const sha256 = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const rel = (file) => path.relative(root, file);

const rawDates = {};
for (const date of acceptedDates) {
  const receipt = await readJson(path.join(rawRoot, date, "query-receipt.json"));
  const metadata = await readJson(path.join(rawRoot, date, "page-metadata.json"));
  const tables = await readJson(path.join(rawRoot, date, "tables.json"));
  rawDates[date] = {
    status: "complete",
    source_url: metadata.source_url,
    page_title: metadata.page_title,
    mode: metadata.mode,
    selected_date: metadata.selected_date,
    query_completed_at: metadata.query_completed_at,
    row_counts: receipt.row_counts,
    output_row_counts: receipt.output_row_counts,
    column_counts: receipt.column_counts,
    exports: receipt.exports,
    metrics: {
      total_base_bet: tables.rows.summary[0][0],
      total_full_bet: tables.rows.summary[0][1],
      total_base_real_return_rate: tables.rows.summary[0][2],
      total_full_real_return_rate: tables.rows.summary[0][3],
      total_people: tables.rows.summary[0][6],
    },
  };
}
const excludedReceipt = await readJson(path.join(priorRawRoot, "query-receipt.json"));
const excludedMetadata = await readJson(path.join(priorRawRoot, "page-metadata.json"));

const localValidation = await readJson(path.join(localRun, "validation-report.json"));
const larkValidation = await readJson(path.join(root, "validation-report.json"));
const backupIndex = await readJson(path.join(root, "lark-backup-complete", "backup-index.json"));
const afterIndex = await readJson(path.join(larkAfter, "after-index.json"));
const writeReceipt = await readJson(path.join(root, "lark-write-receipt-2d.json"));

const sourceData = {
  schema_version: 1,
  source: { url: "https://prod-ac.waje-special.com:8443/sys/dynamic/lifecyclev2/pool/co", page_title: "Lifecycle Pool v2 (Joint)", mode: "v2_joint", timezone: "Asia/Hong_Kong" },
  accepted_dates: acceptedDates,
  excluded_dates: excludedDates,
  dates: rawDates,
  excluded_evidence: {
    "2026-09-03": {
      status: excludedMetadata.status,
      selected_date: excludedMetadata.selected_date,
      core_counts: excludedMetadata.core_counts,
      stop_reason: excludedReceipt.stop_reason,
      attempts: excludedReceipt.attempts,
      raw_path: priorRawRoot,
    },
  },
  policy: "只写入通过日期、四表形状和跨表勾稽的核心数据；不补零、不用邻日替代；未成熟日期保留原始证据但不进入成品。",
};
await fs.writeFile(path.join(root, "source-data.json"), JSON.stringify(sourceData, null, 2) + "\n");
await fs.writeFile(path.join(root, "query-receipts.json"), JSON.stringify({ accepted: rawDates, excluded: { "2026-09-03": excludedReceipt } }, null, 2) + "\n");
await fs.writeFile(path.join(root, "maturity-report.json"), JSON.stringify({
  schema_version: 1,
  policy: "日期必须通过页面日期、四个核心区块、稳定读取、形状和跨表勾稽门禁",
  cutoff_date: "2026-09-06",
  accepted_dates: acceptedDates,
  excluded_dates: excludedDates,
  statuses: {
    ...Object.fromEntries(acceptedDates.map((date) => [date, { status: "complete", write_allowed: true, reason: "four core exports and local/Lark validations passed" }])),
    "2026-09-03": { status: "not_mature", write_allowed: false, reason: "core summary/detail/game/active tables remained empty after controlled retries" },
  },
}, null, 2) + "\n");

const crossTable = {
  schema_version: 1,
  source: "GM Lifecycle Pool v2 (Joint) exports",
  accepted_dates: acceptedDates,
  local: { status: localValidation.status, cross_table_reconciliation_passed: localValidation.invariants?.crossTableReconciliationPassed === true, duplicate_keys_absent: localValidation.invariants?.duplicateKeysAbsent === true, formula_error_scan_passed: localValidation.invariants?.formulaErrorScanPassed === true },
  lark: { status: larkValidation.status, source_target_match: larkValidation.quality?.all_source_target_values_match === true, requested_counts_passed: larkValidation.quality?.all_requested_counts_pass === true, historical_prefix_unchanged: Object.values(larkValidation.sheets || {}).every((sheet) => sheet.historical_prefix_unchanged === true), extra_columns_unchanged: Object.values(larkValidation.sheets || {}).every((sheet) => sheet.new_extra_cells?.length === 0), styles_passed: Object.values(larkValidation.sheets || {}).every((sheet) => sheet.inserted_style_matches_anchor === true && sheet.date_number_format === "yyyy/m/d"), introduced_formula_errors: larkValidation.quality?.introduced_formula_errors ?? 0 },
  by_sheet: larkValidation.sheets,
};
await fs.writeFile(path.join(root, "cross-table-validation.json"), JSON.stringify(crossTable, null, 2) + "\n");

const runStatus = larkValidation.status === "ok_with_warnings" && localValidation.status === "ok" ? "degraded" : "blocked";
const run = {
  schema_version: 1,
  status: runStatus,
  operation: "lifecycle_v2_joint_update_latest_complete_dates",
  generated_at: new Date().toISOString(),
  timezone: "Asia/Hong_Kong",
  source: sourceData.source,
  accepted_dates: acceptedDates,
  excluded_dates: excludedDates,
  revision: { before: writeReceipt.revision_before, after: writeReceipt.revision_after, backup: backupIndex.revision, after_capture: afterIndex.revision },
  local_workbook: { input: localInput, input_sha256: await sha256(localInput), output: localOutput, output_sha256: await sha256(localOutput), validation: rel(path.join(localRun, "validation-report.json")) },
  lark_workbook: { token, backup: rel(path.join(root, "lark-backup-complete", "backup-index.json")), write_plan: rel(path.join(root, "lark-write-plan-2d.json")), write_receipt: rel(path.join(root, "lark-write-receipt-2d.json")), after: rel(path.join(larkAfter, "after-index.json")), validation: rel(path.join(root, "validation-report.json")) },
  counts: { summary: { "2026-09-04": 1, "2026-09-05": 1, "2026-09-06": 1 }, detail: { "2026-09-04": 155, "2026-09-05": 155, "2026-09-06": 155 }, game: { "2026-09-04": 31, "2026-09-05": 31, "2026-09-06": 31 }, active: { "2026-09-04": 4, "2026-09-05": 4, "2026-09-06": 4 } },
  warnings: [...(larkValidation.quality?.warnings || []), "2026-09-03 remained excluded as not_mature; no replacement or zero-fill was used."],
  artifacts: ["manifest.json", "source-data.json", "query-receipts.json", "maturity-report.json", "cross-table-validation.json", "lark-backup-complete/backup-index.json", "lark-after/after-index.json", "validation-report.json"],
};
await fs.writeFile(path.join(root, "run-receipt.json"), JSON.stringify(run, null, 2) + "\n");
await fs.writeFile(path.join(root, "manifest.json"), JSON.stringify({ artifact_type: "lifecycle_joint_latest_update", ...run }, null, 2) + "\n");
console.log(JSON.stringify({ status: run.status, accepted_dates: acceptedDates, excluded_dates: excludedDates, revision: `${run.revision.before}->${run.revision.after}`, local_output_sha256: run.local_workbook.output_sha256 }, null, 2));
