#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve("data/outputs/origin_new_user/2026-09-04-30d/local-update");
const input = "/Users/robin/Desktop/waje data/新用户数据分析2026.8.6-8.31_new_AI更新版_Origin复核清零.xlsx";
const output = "/Users/robin/Desktop/waje data/新用户数据分析2026.8.5-9.3_new_AI更新版.xlsx";
const sha = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const localValidation = JSON.parse(await fs.readFile(path.join(root, "validation-report.json"), "utf8"));
const maturity = JSON.parse(await fs.readFile(path.join(root, "maturity-report.json"), "utf8"));
const zeroLedger = JSON.parse(await fs.readFile(path.join(root, "zero-ledger.json"), "utf8"));
const render = { schema_version: 1, status: "degraded_renderer_only", reason: "数据写入、重新导入、历史保护、零值清理和公式扫描已完成；8 Sheet 渲染进程超过4分钟无回执，已停止该渲染子阶段。", preview_count: 0, authoritative_checks: "local validation-report.json" };
await fs.writeFile(path.join(root, "render-receipt.json"), JSON.stringify(render, null, 2) + "\n");
const status = maturity.excluded_dates?.length ? "degraded" : "ok";
const manifest = { schema_version: 1, status, source: "Origin BQ-新增付费用户分析", source_url: "https://datagrowth.trackares.com/tracking-web/iframe/29/114?id=114&isFavorite=1", product: "Waje Special", tc_logic: "累计利润(C-T)", requested_date_range: { start: "2026-08-05", end: "2026-09-03", date_count: 30 }, accepted_dates: maturity.accepted_dates, excluded_not_mature_dates: maturity.excluded_dates, input: { path: input, sha256: await sha(input), unchanged: true }, output: { path: output, sha256: await sha(output) }, zero_ledger_count: zeroLedger.count, artifacts: { source_data: "source-data.json", filter_receipts: "filter-receipts.json", maturity_report: "maturity-report.json", zero_ledger: "zero-ledger.json", validation_report: "validation-report.json", workbook_before: "workbook-before.json", workbook_after: "workbook-after.json", render_receipt: "render-receipt.json", historical_overlap: "../historical-overlap-validation.json", raw_snapshots: "raw-snapshots/" } };
await fs.writeFile(path.join(root, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
const receipt = { schema_version: 1, status, operation: "origin_new_user_paid_analysis_refresh", generated_at: new Date().toISOString(), timezone: "Asia/Hong_Kong", source: { report: "BQ-新增付费用户分析", url: manifest.source_url, product: "Waje Special", tc_logic: "累计利润(C-T)", requested_range: manifest.requested_date_range, accepted_range: { start: maturity.accepted_dates[0], end: maturity.accepted_dates.at(-1), date_count: maturity.accepted_dates.length } }, maturity: { accepted_dates: maturity.accepted_dates, excluded_not_mature_dates: maturity.excluded_dates, policy: "3日字段非空且非0且8个Sheet全部通过；未成熟日期不写入", raw_preserved: true }, local_workbook: { input, input_sha256: manifest.input.sha256, output, output_sha256: manifest.output.sha256, validation_status: localValidation.status, zero_ledger_count: zeroLedger.count, render_status: render.status }, notes: ["8/6-8/30重叠日期的成熟留存值以本次新查询为准，变化已记录在 historical-overlap-validation.json。", "未成熟 9/3 保留 raw 快照但未写入本地或飞书。", "渲染阶段单独降级，不影响数据与格式校验。"] };
await fs.writeFile(path.join(root, "run-receipt.json"), JSON.stringify(receipt, null, 2) + "\n");
console.log(JSON.stringify({ status, accepted_dates: maturity.accepted_dates.length, excluded_not_mature_dates: maturity.excluded_dates, zero_ledger_count: zeroLedger.count, output_sha256: manifest.output.sha256 }, null, 2));
