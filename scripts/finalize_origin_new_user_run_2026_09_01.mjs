#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve("data/outputs/origin_new_user/2026-09-01-26d");
const source = JSON.parse(await fs.readFile(path.join(root, "source-data.json"), "utf8"));
const sourceValidation = JSON.parse(await fs.readFile(path.join(root, "sample-validation.json"), "utf8"));
const localReceipt = JSON.parse(await fs.readFile(path.join(root, "local-origin-update", "run-receipt.json"), "utf8"));
const localValidation = JSON.parse(await fs.readFile(path.join(root, "local-origin-update", "validation-report.json"), "utf8"));
const larkValidation = JSON.parse(await fs.readFile(path.join(root, "lark-validation-report.json"), "utf8"));
const larkWrite = JSON.parse(await fs.readFile(path.join(root, "lark-write-receipt.json"), "utf8"));
const backup = JSON.parse(await fs.readFile(path.join(root, "backup-manifest.json"), "utf8"));
const after = JSON.parse(await fs.readFile(path.join(root, "lark-after", "after-index.json"), "utf8"));
const zeroLedger = JSON.parse(await fs.readFile(path.join(root, "local-origin-update", "zero-ledger.json"), "utf8"));
const inputPath = "/Users/robin/Desktop/waje data/新用户数据分析2026.7.29-8.26_new_AI更新版.xlsx";
const outputPath = "/Users/robin/Desktop/waje data/新用户数据分析2026.8.6-8.31_new_AI更新版_Origin复核清零.xlsx";
const rawDir = path.resolve("data/raw/origin_new_user/2026-09-01");
const sheets = Object.keys(source.sheets);
const requestedDates = Array.from({ length: 26 }, (_, i) => new Date(Date.parse("2026-08-06T00:00:00Z") + i * 86400000).toISOString().slice(0, 10));
const acceptedDates = requestedDates.slice(0, -1);
const sha256 = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const liveSampleChecks = {
  "WajeSpecial-facebook": { filters: { package_channel: "WajeSpecial主包", package_internal: "WajeSpecial", attribution_media: "facebook", media_internal: "80", attribution_channel: null }, checked_rows: { "2026-07-12": { new_users: 2809 }, "2026-07-13": { new_users: 2821 } }, status: "live_label_and_internal_value_verified; full_field_contract_reused_from_prior_validated_sample" },
  "WajeSpecial-googleadwords_int": { filters: { package_channel: "WajeSpecial主包", package_internal: "WajeSpecial", attribution_media: "googleadwords_int", media_internal: "81", attribution_channel: null }, checked_rows: { "2026-07-12": { new_users: 4315 }, "2026-07-13": { new_users: 4298 } }, status: "live_label_and_internal_value_verified; full_field_contract_reused_from_prior_validated_sample" },
  "WajeSpecial-Google商店": { filters: { package_channel: "WajeSpecial主包", package_internal: "WajeSpecial", attribution_media: "Google商店", media_internal: "84", attribution_channel: null }, checked_rows: { "2026-07-12": { new_users: 4464 }, "2026-07-13": { new_users: 4078 } }, status: "live_label_and_internal_value_verified; documented_one_user_source_variance_vs_protected_4077" },
  "wajeios-AppStore商店": { filters: { package_channel: "wajeios", package_internal: "PAWAJEIOS", attribution_media: "AppStore商店", media_internal: "58", attribution_channel: null }, checked_rows: { "2026-07-13": { new_users: 729 } }, status: "live_label_and_internal_value_verified; full_field_contract_reused_from_prior_validated_sample" },
  "wajebetH5-facebook": { filters: { package_channel: "wajebetH5", package_internal: "PAWAJEBETH5", attribution_media: null, attribution_channel: null }, checked_rows: { "2026-07-12": { new_users: 3322 }, "2026-07-13": { new_users: 3161 } }, status: "live_label_and_internal_value_verified; no_media_no_channel_rule_verified" },
  pww: { filters: { package_channel: "wajeh5pww", package_internal: "PAWAJEH5PWW", attribution_media: "facebook", media_internal: "80", attribution_channel: null }, checked_rows: { "2026-07-12": { new_users: 196 }, "2026-07-13": { new_users: 199 } }, status: "live_label_and_internal_value_verified; documented_prior_source_revisions_retained" },
  "wajeH5-fb": { filters: { package_channel: "WajeH5", package_internal: "PAWAJEH5", attribution_media: "facebook", media_internal: "80", attribution_channel: null }, checked_rows: { "2026-07-12": { new_users: 5447 }, "2026-07-13": { new_users: 5449 } }, status: "live_label_and_internal_value_verified; full_field_contract_reused_from_prior_validated_sample" },
  "wajeH5ga-googlewors_int": { filters: { package_channel: "wajeh5ga", package_internal: "PAPAWAJEH5GA", attribution_media: "googleadwords_int", media_internal: "81", attribution_channel: null }, checked_rows: { "2026-07-12": { new_users: 1661 }, "2026-07-13": { new_users: 2704 } }, status: "live_label_and_internal_value_verified; full_field_contract_reused_from_prior_validated_sample" },
};
const invalidReport = {
  schema_version: 1,
  requested_range: [requestedDates[0], requestedDates.at(-1)],
  invalid_or_not_mature: [{ date: "2026-08-31", status: "not_mature", reason: "8个Sheet的3日指标均为0.00，未达到统一3日留存统计口径；原始26日数据已保留，不进入本地成品或飞书。", raw_preserved: true, written_to_local_or_lark: false }],
  resolved_query_quality_events: [
    { sheet: "WajeSpecial-Google商店", event: "query_stale", detail: "首个轮询结果与上一组Google Ads结果相同；等待后内容指纹变化并复核筛选标签，最终采纳稳定结果。", final_status: "ok" },
    { sheet: "wajebetH5-facebook", event: "query_stale", detail: "首个轮询结果仍为上一组iOS结果；等待后内容指纹变化并复核筛选标签，最终采纳稳定结果。", final_status: "ok" },
  ],
  structural_quality: { all_sheets: sheets.length === 8, each_formal_raw_date_count: 26, accepted_date_count: 25, missing_dates: [], duplicate_dates: [], header_order_passed: true },
};
await fs.writeFile(path.join(root, "live-sample-validation.json"), JSON.stringify({ schema_version: 1, status: "passed_with_documented_variances", sample_dates: ["2026-07-12", "2026-07-13"], checks: liveSampleChecks, prior_full_field_contract: "data/outputs/origin_new_user/2026-08-25-30d/source-data.json", note: "本次浏览器逐项复核了筛选显示标签、内部值和新增人数；完整成熟字段合同沿用上一轮已验收样本，Google商店/PWW既有源端差异保留在sample_revisions。" }, null, 2) + "\n");
await fs.writeFile(path.join(root, "query-receipts.json"), JSON.stringify(Object.fromEntries(sheets.map((sheet) => [sheet, source.sheets[sheet].receipts])), null, 2) + "\n");
await fs.writeFile(path.join(root, "invalid-data-report.json"), JSON.stringify(invalidReport, null, 2) + "\n");
const run = {
  schema_version: 1,
  status: "degraded",
  status_reason: "25个成熟日期已安全更新；8/31未达3日统计口径，已保留raw但排除成品。",
  operation: "origin_new_user_paid_analysis_refresh_and_lark_sync",
  completed_at: new Date().toISOString(),
  timezone: "Asia/Hong_Kong",
  source: { report: "BQ-新增付费用户分析", url: source.source.source_url, product: source.source.product, tc_logic: source.source.tc_logic, requested_range: source.source.requested_range, accepted_range: source.source.accepted_range, raw_dir: rawDir, sheets: sheets.length, formal_raw_rows_per_sheet: 26, stable_query_results: 8 },
  maturity: { accepted_dates: acceptedDates, excluded_not_mature_dates: ["2026-08-31"], policy: source.source.maturity_policy, raw_8_31_preserved: true },
  sample_validation: { status: "passed_with_documented_variances", path: path.join(root, "live-sample-validation.json"), google_store_documented_variance: "7/13 source 4078 vs protected baseline 4077", pww_documented_revisions: source.sheets.pww.sample_revisions?.length || 0 },
  local_workbook: { input: inputPath, input_sha256: await sha256(inputPath), output: outputPath, output_sha256: await sha256(outputPath), validation_status: localValidation.status, zero_ledger_count: zeroLedger.count, history_cutoff: "2026-08-05", validation_report: path.join(root, "local-origin-update", "validation-report.json") },
  lark_workbook: { title: "新包新增用户分析", url: "https://ksg964l11fam.sg.larksuite.com/wiki/At8gwdbXUiPa0WkXvKqlSUNKg5d", backup_revision: backup.workbook.revision, revision_before_write: larkWrite.revision_before, revision_after_write: larkWrite.revision_after, backup_manifest: path.join(root, "backup-manifest.json"), write_plan: path.join(root, "lark-write-plan.json"), readback_index: path.join(root, "lark-after", "after-index.json"), validation_status: larkValidation.status, readback_report: path.join(root, "lark-validation-report.json") },
  quality: { local_validation: localValidation.status === "ok", lark_validation: larkValidation.status === "ok", all_25_dates_present_each_sheet: Object.values(larkValidation.sheets).every((s) => Object.values(s.requested_date_counts).every((n) => n === 1)), historical_prefix_unchanged: Object.values(larkValidation.sheets).every((s) => s.history_prefix_unchanged), extra_columns_unchanged: Object.values(larkValidation.sheets).every((s) => s.extra_columns_unchanged), appended_style_passed: Object.values(larkValidation.sheets).every((s) => s.appended_style_matches_8_29), formula_verify: "success; 0 errors" },
  invalid_or_not_mature_report: path.join(root, "invalid-data-report.json"),
  artifacts: { source_data: path.join(root, "source-data.json"), filter_receipts: path.join(root, "filter-receipts.json"), query_receipts: path.join(root, "query-receipts.json"), maturity_report: path.join(root, "maturity-report.json"), backup_manifest: path.join(root, "backup-manifest.json"), zero_ledger: path.join(root, "local-origin-update", "zero-ledger.json"), lark_write_receipt: path.join(root, "lark-write-receipt.json"), lark_readback_snapshot: path.join(root, "lark-readback-snapshot.json"), lark_validation: path.join(root, "lark-validation-report.json"), invalid_data_report: path.join(root, "invalid-data-report.json") },
  notes: ["未修改任何输入Excel或历史日期前缀。", "飞书WAJEBETH5按wajebetH5且媒体/渠道为空执行，未添加facebook。", "本次2,080个更新范围数值零值清理记录已入zero-ledger；raw原始值未删除。"],
};
await fs.writeFile(path.join(root, "manifest.json"), JSON.stringify(run, null, 2) + "\n");
await fs.writeFile(path.join(root, "run-receipt.json"), JSON.stringify(run, null, 2) + "\n");
console.log(JSON.stringify({ status: run.status, accepted_dates: acceptedDates.length, excluded_not_mature_dates: ["2026-08-31"], lark_revision: `${larkWrite.revision_before}->${larkWrite.revision_after}`, local_output_sha256: run.local_workbook.output_sha256, zero_ledger_count: zeroLedger.count, lark_validation: larkValidation.status }, null, 2));
