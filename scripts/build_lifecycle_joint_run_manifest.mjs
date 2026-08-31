#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) { out[key] = next; i += 1; } else out[key] = true;
  }
  return out;
}
const args = parseArgs(process.argv.slice(2));
const rawRoot = path.resolve(args["raw-root"] || "data/raw/lifecycle_joint/2026-08-28-30d");
const recheckRoot = path.resolve(args["recheck-root"] || path.join(rawRoot, "recheck-2026-08-28"));
const outputDir = path.resolve(args["output-dir"] || "data/outputs/lifecycle_joint/2026-08-28-30d");
const startDate = args["start-date"] || "2026-07-29";
const endDate = args["end-date"] || "2026-08-27";
const kinds = ["summary", "detail", "game", "active"];

function datesBetween(start, end) {
  const result = [];
  for (let ms = Date.parse(`${start}T00:00:00Z`); ms <= Date.parse(`${end}T00:00:00Z`); ms += 86400000) result.push(new Date(ms).toISOString().slice(0, 10));
  return result;
}
function sha256(file) { return fs.readFile(file).then((data) => crypto.createHash("sha256").update(data).digest("hex")); }
function validIso(value) { return typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/.test(value); }
async function readJson(file) { return JSON.parse(await fs.readFile(file, "utf8")); }
async function writeJson(file, value) { await fs.mkdir(path.dirname(file), { recursive: true }); await fs.writeFile(file, `${JSON.stringify(value, null, 2)}\n`, "utf8"); }

const dates = datesBetween(startDate, endDate);
const entries = [];
const failures = [];
for (const date of dates) {
  const canonicalDir = path.join(rawRoot, date);
  const canonicalReceiptPath = path.join(canonicalDir, "query-receipt.json");
  const recheckReceiptPath = path.join(recheckRoot, date, "query-receipt.json");
  let receipt = null;
  let receiptPath = null;
  for (const candidate of [canonicalReceiptPath, recheckReceiptPath]) {
    try {
      const value = await readJson(candidate);
      if (value.status === "complete" && value.selected_date === date && value.stability?.stable === true && validIso(value.submitted_at)) { receipt = value; receiptPath = candidate; break; }
    } catch {}
  }
  if (!receipt) { failures.push({ date, stage: "receipt", error: "no complete stable receipt with valid submitted_at" }); continue; }
  const files = {};
  for (const kind of kinds) {
    const canonicalFile = path.join(canonicalDir, `${kind}.xlsx`);
    try {
      const actualHash = await sha256(canonicalFile);
      const expectedHash = receipt.files?.[kind]?.sha256;
      if (!expectedHash || actualHash !== expectedHash) failures.push({ date, kind, stage: "file_hash", error: `canonical hash mismatch actual=${actualHash} receipt=${expectedHash}` });
      files[kind] = { path: path.relative(ROOT, canonicalFile), sha256: actualHash, bytes: (await fs.stat(canonicalFile)).size, receipt_source: path.relative(ROOT, receiptPath) };
    } catch (error) { failures.push({ date, kind, stage: "file", error: String(error.message || error) }); }
  }
  entries.push({ date, status: "complete", receipt_path: path.relative(ROOT, receiptPath), data_root: path.relative(ROOT, canonicalDir), selected_date: receipt.selected_date, submitted_at: receipt.submitted_at, exported_at: receipt.exported_at, stability: receipt.stability, headers: receipt.headers, files });
}
const manifest = {
  schema_version: 1,
  kind: "lifecycle_joint_30d_source_manifest",
  source_url: "https://prod-ac.waje-special.com:8443/sys/dynamic/lifecyclev2/pool/co",
  page_title: "Lifecycle Pool v2 (Joint)",
  mode: "joint",
  range: { start_date: startDate, end_date: endDate, date_count: dates.length, timezone: "Asia/Hong_Kong" },
  raw_root: path.relative(ROOT, rawRoot),
  recheck_root: path.relative(ROOT, recheckRoot),
  dates: entries,
  expected_dates: dates,
  complete_dates: entries.length,
  failures,
  status: entries.length === dates.length && failures.length === 0 ? "complete" : "degraded",
  policy: "canonical raw files are used; recheck receipts may provide complete query evidence when canonical receipt metadata was incomplete; no source values are imputed",
};
await writeJson(path.join(outputDir, "source-manifest.json"), manifest);
await writeJson(path.join(outputDir, "query-receipts.json"), entries);
process.stdout.write(`${JSON.stringify({ status: manifest.status, expected_dates: dates.length, complete_dates: entries.length, failures: failures.length, output: path.relative(ROOT, outputDir) }, null, 2)}\n`);
if (manifest.status !== "complete") process.exitCode = 1;
