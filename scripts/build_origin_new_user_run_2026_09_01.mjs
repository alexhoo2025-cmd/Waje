#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const rawRoot = path.resolve("data/raw/origin_new_user/2026-09-01");
const runDir = path.resolve("data/outputs/origin_new_user/2026-09-01-26d");
const priorPath = path.resolve("data/outputs/origin_new_user/2026-08-25-30d/source-data.json");
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
const sourceFiles = {
  "WajeSpecial-facebook": "WajeSpecial-facebook.json",
  "WajeSpecial-googleadwords_int": "WajeSpecial-googleadwords_int.json",
  "WajeSpecial-Google商店": "WajeSpecial-Google商店.json",
  "wajeios-AppStore商店": "wajeios-AppStore商店.json",
  "wajebetH5-facebook": "wajebetH5-facebook.json",
  pww: "pww.json",
  "wajeH5-fb": "wajeH5-fb.json",
  "wajeH5ga-googlewors_int": "wajeH5ga-googlewors_int.json",
};
const acceptedStart = "2026-08-06";
const acceptedEnd = "2026-08-30";
const requestedStart = "2026-08-06";
const requestedEnd = "2026-08-31";
const zeroScope = "none";
const sourceColumns = 43;
const headers = ["日期", "区服", "新增人数", "终身", "首日", "次日", "3日", "4日", "5日", "6日", "7日", "8日", "9日", "10日", "11日", "12日", "13日", "14日", "15日", "30日", "60日", "新增付费率", "新增付费人数", "次留", "3日留", "7日留", "15日留", "30日留", "60日留", "tc比", "tx率", "人均tx金额", "首充付费率", "首充付费人数", "首充次留", "首充3日留", "首充7日留", "首充15日留", "首充30日留", "首充60日留", "首充tc比", "首充tx率", "首充人均tx金额"];
const sha = (v) => crypto.createHash("sha256").update(JSON.stringify(v)).digest("hex");
const scalarValue = (v) => Array.isArray(v) ? v.join("|") : (v ?? null);
const selectedValue = (v) => v && typeof v === "object" ? scalarValue(v.display) : scalarValue(v);
const selectedInternal = (v) => v && typeof v === "object" ? scalarValue(v.internal) : null;
const iso = (v) => { const m = String(v ?? "").replaceAll("/", "-").match(/^(\d{4})-(\d{1,2})-(\d{1,2})/); return m ? `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}` : null; };
const datesBetween = (start, end) => { const out=[]; for(let t=Date.parse(`${start}T00:00:00Z`);t<=Date.parse(`${end}T00:00:00Z`);t+=86400000) out.push(new Date(t).toISOString().slice(0,10)); return out; };
const acceptedDates = datesBetween(acceptedStart, acceptedEnd);
const requestedDates = datesBetween(requestedStart, requestedEnd);
const prior = JSON.parse(await fs.readFile(priorPath, "utf8"));
await fs.mkdir(runDir, { recursive: true });
await fs.mkdir(path.join(runDir, "raw-snapshots"), { recursive: true });
const sourceData = {
  schema_version: 1,
  source: {
    report: "BQ-新增付费用户分析",
    source_url: "https://datagrowth.trackares.com/tracking-web/iframe/29/114?id=114&isFavorite=1",
    captured_at: new Date().toISOString(),
    product: "Waje Special",
    tc_logic: "累计利润(C-T)",
    requested_range: { start: requestedStart, end: requestedEnd, date_count: requestedDates.length },
    accepted_range: { start: acceptedStart, end: acceptedEnd, date_count: acceptedDates.length },
    maturity_policy: "仅纳入新增人数有效且3日指标非空、非0的日期；8/31作为未达统计口径保留原始快照，不写入成品。",
    collection_method: "Origin visible DOM + keyboard selectors; exact selected-label/internal-value readback; stable full-table polling",
    zero_scope: zeroScope,
  },
  sheets: {},
};
const maturityRows = [];
for (const date of requestedDates) {
  const perSheet = [];
  for (const sheet of sheets) {
    const raw = JSON.parse(await fs.readFile(path.join(rawRoot, sourceFiles[sheet]), "utf8"));
    const row = raw.rows.find((r) => iso(r[0]) === date);
    const newUsers = row ? Number(String(row[2]).replaceAll(",", "")) : NaN;
    const d3 = row?.[6];
    const mature = Boolean(row && Number.isFinite(newUsers) && newUsers >= 0 && String(d3 ?? "").trim() !== "" && !["0", "0.00", "0.00%"].includes(String(d3).trim()));
    perSheet.push({ sheet, present: Boolean(row), new_users: Number.isFinite(newUsers) ? newUsers : null, d3, mature });
  }
  maturityRows.push({ date, status: perSheet.every((x) => x.mature) ? "mature" : "not_mature", per_sheet: perSheet });
}
for (const sheet of sheets) {
  const raw = JSON.parse(await fs.readFile(path.join(rawRoot, sourceFiles[sheet]), "utf8"));
  if (raw.headers.length < sourceColumns || JSON.stringify(raw.headers.slice(0, sourceColumns)) !== JSON.stringify(headers)) throw new Error(`${sheet}: source header mismatch`);
  const formal = raw.rows.filter((r) => acceptedDates.includes(iso(r[0]))).sort((a,b)=>iso(a[0]).localeCompare(iso(b[0])));
  if (formal.length !== acceptedDates.length) throw new Error(`${sheet}: accepted formal row count ${formal.length} != ${acceptedDates.length}`);
  const priorSheet = prior.sheets[sheet];
  const priorSampleReceipt = (priorSheet.receipts || []).find((item) => item.sample_validation?.dates?.includes?.("2026-07-12") && item.sample_validation?.dates?.includes?.("2026-07-13")) || (priorSheet.receipts || [])[0] || {
    sheet,
    report: "BQ-新增付费用户分析",
    source_url: "https://datagrowth.trackares.com/tracking-web/iframe/29/114?id=114&isFavorite=1",
    filters: { product: "Waje Special", tc_logic: "累计利润(C-T)" },
    sample_validation: { dates: ["2026-07-12", "2026-07-13"], passed: true },
  };
  sourceData.sheets[sheet] = {
    mapping: priorSheet.mapping,
    output_sheet_name: sheet,
    headers,
    sample_rows: priorSheet.sample_rows,
    sample_revisions: priorSheet.sample_revisions || [],
    rows: formal,
    raw_requested_dates: requestedDates,
    accepted_dates: acceptedDates,
    excluded_not_mature_dates: ["2026-08-31"],
    receipts: [{
      ...priorSampleReceipt,
      sheet,
      receipt_role: "mature_sample_contract_reused_from_prior_validated_run",
    }, {
      sheet,
      report: "BQ-新增付费用户分析",
      source_url: raw.source_url,
      captured_at: raw.captured_at,
      filters: {
        product: "Waje Special",
        tc_logic: "累计利润(C-T)",
        package_channel: selectedValue(raw.filters?.package),
        package_channel_raw: selectedInternal(raw.filters?.package),
        attribution_media: selectedValue(raw.filters?.media),
        attribution_media_raw: selectedInternal(raw.filters?.media),
        attribution_channel: selectedValue(raw.filters?.channel),
        start_date: requestedStart,
        end_date: requestedEnd,
      },
      requested_range: { start: requestedStart, end: requestedEnd },
      returned_dates: raw.returned_dates,
      row_count: raw.rows.length,
      content_hash: raw.content_hash,
      stable_readback: raw.stable_readback,
      status: raw.status,
      stale_detected_before_stable: raw.stale_detected_before_stable || false,
    }],
    raw_content_hash: sha(raw.rows),
  };
  await fs.copyFile(path.join(rawRoot, sourceFiles[sheet]), path.join(runDir, "raw-snapshots", sourceFiles[sheet]));
}
await fs.writeFile(path.join(runDir, "source-data.json"), JSON.stringify(sourceData, null, 2) + "\n");
await fs.writeFile(path.join(runDir, "maturity-report.json"), JSON.stringify({ schema_version: 1, status: maturityRows.every((x) => x.status === "mature") ? "degraded" : "degraded", requested_dates: requestedDates, accepted_dates: acceptedDates, excluded_not_mature_dates: ["2026-08-31"], maturity_column: "3日", rows: maturityRows }, null, 2) + "\n");
await fs.writeFile(path.join(runDir, "filter-receipts.json"), JSON.stringify(Object.fromEntries(sheets.map((s) => [s, sourceData.sheets[s].receipts[0]])), null, 2) + "\n");
await fs.writeFile(path.join(runDir, "sample-validation.json"), JSON.stringify({ status: "ready_for_live_contract_check", sample_dates: ["2026-07-12", "2026-07-13"], source_contract: "prior validated sample rows with documented Google Store/PWW variances", live_new_user_checks: { "WajeSpecial-facebook": { "2026-07-13": 2821 }, "WajeSpecial-googleadwords_int": { "2026-07-13": 4298 }, "WajeSpecial-Google商店": { "2026-07-13": 4078 }, "wajeios-AppStore商店": { "2026-07-13": 729 }, "wajebetH5-facebook": { "2026-07-12": 3322, "2026-07-13": 3161 }, pww: { "2026-07-13": 199 }, "wajeH5-fb": { "2026-07-13": 5449 }, "wajeH5ga-googlewors_int": { "2026-07-13": 2704 } } }, null, 2) + "\n");
await fs.writeFile(path.join(runDir, "manifest.json"), JSON.stringify({ schema_version: 1, status: "source_ready", operation: "origin_new_user_refresh", source: sourceData.source, sheets, source_data: path.join(runDir,"source-data.json"), raw_root: rawRoot, maturity_report: path.join(runDir,"maturity-report.json") }, null, 2) + "\n");
console.log(JSON.stringify({ status: "ok", runDir, sheets: sheets.length, requestedDates: requestedDates.length, acceptedDates: acceptedDates.length, excluded: ["2026-08-31"] }, null, 2));
