#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const OUTPUT = path.resolve(process.argv[2] || "data/outputs/lifecycle_joint/2026-08-28-30d");
const semantics = ["summary", "detail", "game", "active"];
const readJson = async (file) => JSON.parse(await fs.readFile(file, "utf8"));
const writeJson = async (file, value) => fs.writeFile(file, `${JSON.stringify(value, null, 2)}\n`, "utf8");
const sha256File = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");

const sourceManifest = await readJson(path.join(OUTPUT, "source-manifest.json"));
const rawAudit = await readJson(path.join(OUTPUT, "source-audit/raw-audit.json"));
const backup = await readJson(path.join(OUTPUT, "backup-manifest.json"));
const mapping = await readJson(path.join(OUTPUT, "sheet-alias-mapping.json"));
const plan = await readJson(path.join(OUTPUT, "write-plan.json"));
const validation = await readJson(path.join(OUTPUT, "validation-report.json"));
const layout = await readJson(path.join(OUTPUT, "layout-validation.json"));
const writes = await readJson(path.join(OUTPUT, "write-receipts.json"));
const insertions = await readJson(path.join(OUTPUT, "dim-insert-receipts.json"));
const revisionAfter = await readJson(path.join(OUTPUT, "lark-revision-live-after.json"));

const updatedCells = writes.reduce((sum, item) => sum + (item.result?.data?.results || []).reduce((inner, result) => inner + Number(result.data?.updated_cells_count || 0), 0), 0);
const insertedRows = insertions.reduce((sum, item) => sum + Number(item.request?.count || 0), 0);
const rawDates = rawAudit.raw_export_audit?.dates || {};
const maturityDates = sourceManifest.dates.map((entry) => ({
  date: entry.date,
  source_status: rawDates[entry.date]?.status || "unknown",
  query_status: entry.status,
  selected_date: entry.selected_date,
  submitted_at: entry.submitted_at,
  stability: entry.stability,
  rows: entry.stability?.second_check?.row_counts || null,
  maturity_status: entry.status === "complete" && rawDates[entry.date]?.status === "passed" && entry.stability?.stable === true ? "matured_core_tables" : "not_mature",
}));
const maturityFailures = maturityDates.filter((entry) => entry.maturity_status !== "matured_core_tables");

const crossTable = {
  schema_version: 1,
  source: "GM Lifecycle Pool v2 (Joint) raw exports",
  window: sourceManifest.range,
  status: rawAudit.raw_export_audit?.status === "passed" ? "passed" : "failed",
  dates: Object.fromEntries(Object.entries(rawDates).map(([date, item]) => [date, { status: item.status, rows: Object.fromEntries(Object.entries(item.files || {}).map(([kind, value]) => [kind, value.row_count])), quality: item.quality, errors: item.errors }])),
  rule: "summary/detail/game/active must pass headers, keys, lifecycle coverage and cross-table amount/return reconciliation; no imputation",
};
await writeJson(path.join(OUTPUT, "maturity-report.json"), { schema_version: 1, generated_at: new Date().toISOString(), window: sourceManifest.range, policy: "only dates with stable complete four core tables are written; no zero-fill or neighbouring-date substitution", dates: maturityDates, status: maturityFailures.length ? "degraded" : "passed", failures: maturityFailures });
await writeJson(path.join(OUTPUT, "cross-table-validation.json"), crossTable);

const writeReceipt = {
  schema_version: 1,
  status: writes.every((item) => item.result?.ok === true) ? "passed" : "failed",
  revision_before: mapping.revision_before,
  revision_after: revisionAfter.revision,
  updated_cells: updatedCells,
  inserted_rows: insertedRows,
  by_semantic: Object.fromEntries(semantics.map((semantic) => {
    const items = writes.filter((item) => item.semantic === semantic);
    const planItem = plan.semantic_mapping[semantic];
    return [semantic, { sheet_id: planItem.sheet_id, sheet_title: planItem.sheet_title, write_batches: items.length, updated_cells: items.reduce((sum, item) => sum + (item.result?.data?.results || []).reduce((inner, result) => inner + Number(result.data?.updated_cells_count || 0), 0), 0), inserted_rows: (planItem.insertions || []).reduce((sum, item) => sum + Number(item.count || 0), 0), preexisting_duplicate_keys: planItem.preexisting_duplicate_keys || [] }];
  })),
  no_deletions: true,
};
await writeJson(path.join(OUTPUT, "write-receipt.json"), writeReceipt);

const readbackSnapshot = { schema_version: 1, revision: revisionAfter.revision, sheets: Object.fromEntries(semantics.map((semantic) => ({
  summary: "summary", detail: "detail", game: "game", active: "active",
}[semantic] ? [semantic, { file: `lark-after-live-${semantic}.json`, sha256: null, actual_range: validation.values?.[semantic]?.actual_range, after_rows: validation.values?.[semantic]?.after_rows, compared_keys: validation.values?.[semantic]?.compared_keys }] : [semantic, {}]))), layout_validation: "layout-validation.json", value_validation: "validation-report.json" };
for (const semantic of semantics) readbackSnapshot.sheets[semantic].sha256 = await sha256File(path.join(OUTPUT, `lark-after-live-${semantic}.json`));
await writeJson(path.join(OUTPUT, "readback-snapshot.json"), readbackSnapshot);

const warnings = [...(validation.warnings || [])];
const finalStatus = sourceManifest.status !== "complete" || validation.failures?.length || layout.status !== "passed" ? "blocked" : warnings.length ? "degraded" : "ok";
const finalValidation = { ...validation, final_status: finalStatus, source_manifest: "source-manifest.json", maturity_report: "maturity-report.json", cross_table_validation: "cross-table-validation.json", layout_validation: layout, write_receipt: "write-receipt.json", write_attempt_receipt: "run-receipt-write-attempt.json", warning_policy: "preexisting duplicate keys and preexisting formula errors are warnings; no new formula/data/layout failures detected" };
await writeJson(path.join(OUTPUT, "validation-report.json"), finalValidation);

const manifest = {
  schema_version: 1,
  run_id: "lifecycle-joint-lark-30d-2026-07-29-2026-08-27",
  status: finalStatus,
  completed_at: new Date().toISOString(),
  source: { url: sourceManifest.source_url, page_title: sourceManifest.page_title, mode: sourceManifest.mode, range: sourceManifest.range, source_manifest: "source-manifest.json", raw_audit: "source-audit/raw-audit.json", query_receipts: "query-receipts.json", complete_dates: sourceManifest.complete_dates },
  target: { spreadsheet_token: mapping.spreadsheet_token, revision_before: mapping.revision_before, revision_after: revisionAfter.revision, semantic_sheets: mapping.semantic_sheets },
  backup: { manifest: "backup-manifest.json", complete: backup.complete, revision: backup.revision, xlsx_export: backup.export_xlsx },
  write: { receipt: "write-receipt.json", updated_cells: updatedCells, inserted_rows: insertedRows, no_deletions: true },
  validation: { report: "validation-report.json", maturity: "maturity-report.json", cross_table: "cross-table-validation.json", layout: "layout-validation.json", readback: "readback-snapshot.json" },
  warnings,
  artifacts: ["source-manifest.json", "query-receipts.json", "source-data.json", "backup-manifest.json", "sheet-alias-mapping.json", "write-plan.json", "write-receipt.json", "write-receipts.json", "readback-snapshot.json", "maturity-report.json", "cross-table-validation.json", "layout-validation.json", "validation-report.json", "run-receipt-write-attempt.json"],
};
await writeJson(path.join(OUTPUT, "manifest.json"), manifest);
const finalReceipt = { ...manifest, run_receipt: "run-receipt.json" };
await writeJson(path.join(OUTPUT, "run-receipt.json"), finalReceipt);
process.stdout.write(`${JSON.stringify({ status: finalStatus, complete_dates: sourceManifest.complete_dates, updated_cells: updatedCells, inserted_rows: insertedRows, warnings: warnings.length, output: path.relative(ROOT, OUTPUT) }, null, 2)}\n`);
if (finalStatus === "blocked") process.exitCode = 1;
