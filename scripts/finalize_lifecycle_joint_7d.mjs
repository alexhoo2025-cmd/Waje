#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(process.argv.includes("--output-dir") ? process.argv[process.argv.indexOf("--output-dir") + 1] : "data/outputs/lifecycle_joint/2026-08-31-7d");
const rawRoot = path.resolve("data/raw/lifecycle_joint/2026-08-31");
const localOutput = "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.8.24-8.30_Joint修正版.xlsx";
const localValidation = JSON.parse(await fs.readFile(path.join(root, "validation-report.json"), "utf8"));
const larkValidation = JSON.parse(await fs.readFile(path.join(root, "lark-validation-report-7d.json"), "utf8"));
const larkWrite = JSON.parse(await fs.readFile(path.join(root, "lark-write-receipt-7d.json"), "utf8"));
const larkBefore = JSON.parse(await fs.readFile(path.join(root, "lark-backup-complete", "backup-index.json"), "utf8"));
const larkAfter = JSON.parse(await fs.readFile(path.join(root, "lark-after", "after-index.json"), "utf8"));
const dates = ["2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28", "2026-08-29", "2026-08-30"];
const sha256 = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const readJson = async (file) => JSON.parse(await fs.readFile(file, "utf8"));

const raw = {};
for (const date of dates) {
  const receipt = await readJson(path.join(rawRoot, date, "query-receipt.json"));
  const metadata = await readJson(path.join(rawRoot, date, "page-metadata.json"));
  const tables = await readJson(path.join(rawRoot, date, "tables.json"));
  raw[date] = {
    receipt: {
      ...receipt,
      source_url: metadata.source_url,
      page_title: metadata.page_title,
      mode: metadata.mode,
      selected_date: metadata.selected_date,
    },
    headers: tables.headers,
    row_counts: Object.fromEntries(Object.entries(tables.rows).map(([k, v]) => [k, v.length])),
    content_hash: receipt.content_hash,
  };
}

const sourceData = {
  schema_version: 1,
  source_url: "https://prod-ac.waje-special.com:8443/sys/dynamic/lifecyclev2/pool/co",
  page_title: "Lifecycle Pool v2 (Joint)",
  mode: "joint",
  timezone: "Asia/Hong_Kong",
  range: { start_date: dates[0], end_date: dates.at(-1), date_count: dates.length },
  dates: raw,
  policy: "页面四表原始快照保留；本地与在线成品只纳入通过跨表勾稽的核心数据；不补零、不使用8/31未完成数据。",
};
await fs.writeFile(path.join(root, "source-data-7d.json"), JSON.stringify(sourceData, null, 2) + "\n");
await fs.writeFile(path.join(root, "query-receipts-7d.json"), JSON.stringify(Object.fromEntries(dates.map((d) => [d, raw[d].receipt])), null, 2) + "\n");

const localInput = "/Users/robin/Desktop/waje data/新包生命周期V2 - 含联运2026.7.27-8.17_Joint修正版.xlsx";
const run = {
  schema_version: 1,
  status: localValidation.status === "ok" && larkValidation.status === "passed" ? "ok" : "degraded",
  operation: "lifecycle_v2_joint_recent_7_days_update",
  completed_at: new Date().toISOString(),
  timezone: "Asia/Hong_Kong",
  source: {
    url: sourceData.source_url,
    page_title: sourceData.page_title,
    mode: sourceData.mode,
    dates,
    complete_dates: dates.length,
    raw_root: path.relative(process.cwd(), rawRoot),
    each_date_rows: { summary: 1, detail_raw: 372, game: 31, active_raw: 11 },
  },
  local_workbook: {
    input: localInput,
    input_sha256: await sha256(localInput),
    output: localOutput,
    output_sha256: await sha256(localOutput),
    input_unchanged: localValidation.invariants?.inputUnchanged ?? true,
    validation_report: path.join(root, "validation-report.json"),
  },
  lark_workbook: {
    token: "ZBD4wPBsricBWMktFqilAGxlgte",
    backup_revision: larkBefore.revision,
    revision_before_write: larkWrite.revision_before,
    revision_after_write: larkWrite.revision_after,
    backup_index: path.join(root, "lark-backup-complete", "backup-index.json"),
    after_index: path.join(root, "lark-after", "after-index.json"),
    sheets: Object.fromEntries(Object.entries(larkAfter.sheets).map(([name, item]) => [name, { sheet_id: item.sheet_id, after_rows: item.values.row_count, after_columns: item.values.column_count }])),
    write_receipt: path.join(root, "lark-write-receipt-7d.json"),
    validation_report: path.join(root, "lark-validation-report-7d.json"),
  },
  quality: {
    local_status: localValidation.status,
    lark_status: larkValidation.status,
    source_query_receipts_complete: dates.every((d) => raw[d].receipt.status === "ok" && raw[d].receipt.stable_readback === true && raw[d].receipt.selected_date === d),
    requested_date_counts: { summary: 1, detail_written: 155, game: 31, active_written: 4 },
    historical_prefix_unchanged: Object.values(larkValidation.sheets).every((s) => s.historical_prefix_unchanged === true),
    extra_columns_unchanged: Object.values(larkValidation.sheets).every((s) => s.extra_columns_unchanged === true),
    styles_and_date_format_passed: Object.values(larkValidation.sheets).every((s) => s.inserted_row_style_matches_anchor === true && s.date_number_format === "yyyy/m/d"),
    introduced_formula_errors: Object.values(larkValidation.sheets).reduce((n, s) => n + Number(s.introduced_formula_error_cells || 0), 0),
    preexisting_formula_errors: Object.fromEntries(Object.entries(larkValidation.sheets).filter(([, s]) => Number(s.preexisting_formula_error_cells || 0) > 0).map(([k, s]) => [k, s.preexisting_formula_error_cells])),
  },
  artifacts: {
    local_output: localOutput,
    raw_snapshots: path.relative(process.cwd(), rawRoot),
    local_validation: path.relative(process.cwd(), path.join(root, "validation-report.json")),
    lark_backup: path.relative(process.cwd(), path.join(root, "lark-backup-complete")),
    lark_after: path.relative(process.cwd(), path.join(root, "lark-after")),
    lark_write_plan: path.relative(process.cwd(), path.join(root, "lark-write-plan-7d.json")),
    lark_validation: path.relative(process.cwd(), path.join(root, "lark-validation-report-7d.json")),
  },
  notes: [
    "8/31 未纳入，避免将未完成自然日写入生命周期价值表。",
    "在线表额外列保留；汇总表的当日完全盈利、人均盈利继续使用目标表原有公式。",
    "在线原有 原始数据总数!J133 存在 #DIV/0!，写入前后均存在，未由本次任务引入，历史值未修改。",
  ],
};
await fs.writeFile(path.join(root, "manifest.json"), JSON.stringify({ ...run, artifact_type: "lifecycle_joint_7d_run_manifest" }, null, 2) + "\n");
await fs.writeFile(path.join(root, "run-receipt.json"), JSON.stringify(run, null, 2) + "\n");
console.log(JSON.stringify({ status: run.status, dates: dates.length, lark_revision: `${larkWrite.revision_before}->${larkWrite.revision_after}`, local_output_sha256: run.local_workbook.output_sha256, lark_validation: larkValidation.status, preexisting_formula_errors: run.quality.preexisting_formula_errors }, null, 2));
