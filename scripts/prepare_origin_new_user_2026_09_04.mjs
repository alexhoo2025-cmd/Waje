#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const RAW_ORIGINAL = path.resolve("data/raw/origin_new_user/2026-09-04");
const RUN = path.resolve("data/outputs/origin_new_user/2026-09-04-30d");
const RAW_INPUT = path.join(RUN, "raw-input");
const PRIOR = path.resolve("data/outputs/origin_new_user/2026-09-01-26d/local-origin-update/source-data.json");
const DATES = [];
for (let day = 5; day <= 31; day += 1) DATES.push(`2026-08-${String(day).padStart(2, "0")}`);
for (let day = 1; day <= 3; day += 1) DATES.push(`2026-09-${String(day).padStart(2, "0")}`);
const SHEETS = {
  "WajeSpecial-facebook": { package_channel: "WajeSpecial主包", attribution_media: "facebook", attribution_channel: null },
  "WajeSpecial-googleadwords_int": { package_channel: "WajeSpecial主包", attribution_media: "googleadwords_int", attribution_channel: null },
  "WajeSpecial-Google商店": { package_channel: "WajeSpecial主包", attribution_media: "Google商店", attribution_channel: null },
  "wajeios-AppStore商店": { package_channel: "wajeios", attribution_media: "AppStore商店", attribution_channel: null },
  "wajebetH5-facebook": { package_channel: "wajebetH5", attribution_media: null, attribution_channel: null },
  pww: { package_channel: "wajeh5pww", attribution_media: "facebook", attribution_channel: null },
  "wajeH5-fb": { package_channel: "WajeH5", attribution_media: "facebook", attribution_channel: null },
  "wajeH5ga-googlewors_int": { package_channel: "wajeh5ga", attribution_media: "googleadwords_int", attribution_channel: null },
};
const HEADERS = [
  "日期", "区服", "新增人数", "终身", "首日", "次日", "3日", "4日", "5日", "6日", "7日", "8日", "9日", "10日", "11日", "12日", "13日", "14日", "15日", "30日", "60日",
  "新增付费率", "新增付费人数", "次留", "3日留", "7日留", "15日留", "30日留", "60日留", "tc比", "tx率", "人均tx金额", "首充付费率", "首充付费人数", "首充次留", "首充3日留", "首充7日留", "首充15日留", "首充30日留", "首充60日留", "首充tc比", "首充tx率", "首充人均tx金额",
];
function sha(value) { return crypto.createHash("sha256").update(value).digest("hex"); }
function normalizeHeader(value) { return String(value ?? "").replace(/[\s\u00a0]+/g, "").trim(); }
function date(value) { const m = String(value ?? "").trim().match(/^(20\d\d)[-/](\d{1,2})[-/](\d{1,2})/); return m ? `${m[1]}-${String(Number(m[2])).padStart(2, "0")}-${String(Number(m[3])).padStart(2, "0")}` : null; }
function numeric(value) {
  if (value === null || value === undefined || String(value).trim() === "" || value === "-") return null;
  const text = String(value).trim().replaceAll(",", "");
  if (text.endsWith("%")) { const n = Number(text.slice(0, -1)); return Number.isFinite(n) ? n / 100 : text; }
  const n = Number(text); return Number.isFinite(n) ? n : text;
}
function same(left, right) { const a = numeric(left); const b = numeric(right); if (a === null || b === null) return a === b; if (typeof a === "number" && typeof b === "number") return Math.abs(a - b) <= Math.max(0.000001, Math.max(Math.abs(a), Math.abs(b)) * 0.000001); return String(a) === String(b); }
await fs.mkdir(RAW_INPUT, { recursive: true });
const prior = JSON.parse(await fs.readFile(PRIOR, "utf8"));
const manifest = { schema_version: 1, source: { report: "BQ-新增付费用户分析", source_url: "https://datagrowth.trackares.com/tracking-web/iframe/29/114?id=114&isFavorite=1", product: "Waje Special", tc_logic: "累计利润(C-T)", captured_at: new Date().toISOString(), requested_range: { start: DATES[0], end: DATES.at(-1), date_count: DATES.length }, collection_method: "Origin visible report with exact filter label readback, 43-column table and fresh-result fingerprint gate" }, sheets: {} };
const filterReceipts = {};
const overlapValidation = {};
for (const [sheet, mapping] of Object.entries(SHEETS)) {
  const sourcePath = path.join(RAW_ORIGINAL, `${sheet}.json`);
  const payload = JSON.parse(await fs.readFile(sourcePath, "utf8"));
  if (!Array.isArray(payload.headers) || payload.headers.length !== HEADERS.length || payload.headers.some((h, i) => normalizeHeader(h) !== normalizeHeader(HEADERS[i]))) throw new Error(`${sheet}: header mismatch`);
  if (!Array.isArray(payload.rows) || payload.rows.length !== DATES.length) throw new Error(`${sheet}: row count ${payload.rows?.length} != ${DATES.length}`);
  const seen = new Set();
  for (const row of payload.rows) { if (!Array.isArray(row) || row.length !== HEADERS.length) throw new Error(`${sheet}: row width is not 43`); const d = date(row[0]); if (!d || !DATES.includes(d)) throw new Error(`${sheet}: invalid or out-of-window date ${row[0]}`); if (seen.has(d)) throw new Error(`${sheet}: duplicate date ${d}`); seen.add(d); }
  if (seen.size !== DATES.length) throw new Error(`${sheet}: missing requested dates`);
  const normalizedPayload = { ...payload, filters: { ...mapping, start_date: DATES[0], end_date: DATES.at(-1) }, ui_filters: payload.filters?.package ? payload.filters : null, returned_dates: [...seen].sort(), row_count: payload.rows.length, content_hash: sha(JSON.stringify({ headers: payload.headers, rows: payload.rows })), stable_readback: payload.stable_readback === true, prepared_at: new Date().toISOString() };
  if (!normalizedPayload.stable_readback) throw new Error(`${sheet}: stable readback missing`);
  await fs.writeFile(path.join(RAW_INPUT, `${sheet}.json`), JSON.stringify(normalizedPayload, null, 2) + "\n");
  const priorRows = new Map((prior.sheets?.[sheet]?.rows || []).map((row) => [date(row[0]), row]));
  const overlap = []; const allSame = [];
  for (const row of payload.rows) { const d = date(row[0]); const old = priorRows.get(d); if (!old || d > "2026-08-30") continue; const changed = []; for (let i = 0; i < HEADERS.length; i += 1) if (!same(row[i], old[i])) changed.push(i + 1); overlap.push({ date: d, changed_columns: changed, changed: changed.length > 0 }); if (changed.length) allSame.push(d); }
  overlapValidation[sheet] = { overlap_dates_checked: overlap.length, overlap_dates: overlap, changed_overlap_dates: allSame, note: "重叠日期允许源端复算差异，但差异全部记录，窗口外历史不写入。" };
  manifest.sheets[sheet] = { mapping, headers: HEADERS, rows: payload.rows, raw_file: sourcePath, prepared_file: path.join(RAW_INPUT, `${sheet}.json`), content_hash: normalizedPayload.content_hash, returned_dates: normalizedPayload.returned_dates, stable_readback: true, ui_filter_readback: payload.filters?.package ? payload.filters : null };
  filterReceipts[sheet] = { report: manifest.source.report, source_url: manifest.source.source_url, filters: normalizedPayload.filters, ui_filter_readback: payload.filters?.package ? payload.filters : null, returned_dates: normalizedPayload.returned_dates, row_count: payload.rows.length, content_hash: normalizedPayload.content_hash, stable_readback: true, raw_path: sourcePath, prepared_path: path.join(RAW_INPUT, `${sheet}.json`) };
}
await fs.mkdir(RUN, { recursive: true });
await fs.writeFile(path.join(RUN, "source-data-prepared.json"), JSON.stringify(manifest, null, 2) + "\n");
await fs.writeFile(path.join(RUN, "filter-receipts.json"), JSON.stringify(filterReceipts, null, 2) + "\n");
await fs.writeFile(path.join(RUN, "historical-overlap-validation.json"), JSON.stringify({ schema_version: 1, compared_to: PRIOR, compared_window: ["2026-08-06", "2026-08-30"], sheets: overlapValidation }, null, 2) + "\n");
console.log(JSON.stringify({ status: "ok", requested_dates: DATES.length, sheets: Object.keys(SHEETS).length, raw_input: RAW_INPUT, manifest: path.join(RUN, "source-data-prepared.json"), overlap: path.join(RUN, "historical-overlap-validation.json") }, null, 2));
