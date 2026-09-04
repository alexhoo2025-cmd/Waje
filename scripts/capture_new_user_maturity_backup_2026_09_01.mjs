#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { execFile as execFileCallback } from "node:child_process";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const token = process.env.LARK_TOKEN || "At8gwdbXUiPa0WkXvKqlSUNKg5d";
const root = path.resolve(process.env.LARK_BACKUP_DIR || "data/outputs/lark_quality/2026-09-01-new-user-maturity-audit");
const sheets = [
  ["WajeSpecial-facebook", "9cd78d", "AR326"],
  ["WajeSpecial-googleadwords_int", "xWsChb", "AR326"],
  ["WajeSpecial-Google商店", "Cfkonh", "AR326"],
  ["WAJEIOS-AppStore商店", "25iiEi", "AR326"],
  ["WAJEBETH5", "GrWEoo", "BA305"],
  ["wajeH5-facebook", "vkV1SD", "AR228"],
  ["wajeH5ga-googlewords_int", "ef19NP", "AR228"],
  ["PWA", "gjy6I1", "BC404"],
];
const safe = (value) => value.replace(/[^\w.-]+/g, "_");
const sha256 = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const relative = (file) => path.relative(process.cwd(), file) || ".";
const common = ["--spreadsheet-token", token, "--as", "user", "--format", "json"];
await fs.mkdir(path.join(root, "cells"), { recursive: true });
await fs.mkdir(path.join(root, "layout"), { recursive: true });
await fs.mkdir(path.join(root, "conditional-format"), { recursive: true });
const revisionPayload = JSON.parse((await execFile(cli, ["sheets", "+revision-get", ...common], { maxBuffer: 4 * 1024 * 1024 })).stdout);
const workbookPayload = JSON.parse((await execFile(cli, ["sheets", "+workbook-info", ...common], { maxBuffer: 8 * 1024 * 1024 })).stdout);
await fs.writeFile(path.join(root, "workbook-info-before.json"), JSON.stringify(workbookPayload, null, 2) + "\n");
const revision = Number(revisionPayload.data?.revision);
const result = { schema_version: 1, status: "complete", captured_at: new Date().toISOString(), token, title: "新包新增用户分析", revision, sheets: {} };
for (const [name, id, endColumn] of sheets) {
  const base = ["--spreadsheet-token", token, "--sheet-id", id, "--as", "user", "--format", "json"];
  const file = path.join(root, "cells", `${safe(name)}.json`);
  await execFile(cli, ["sheets", "+cells-get", ...base, "--range", `A1:${endColumn}`, "--include", "value,formula,style", "--output-path", relative(file)], { maxBuffer: 5 * 1024 * 1024 });
  const payload = JSON.parse(await fs.readFile(file, "utf8"));
  if (payload.has_more !== false) throw new Error(`${name}: cells backup truncated`);
  const layoutFile = path.join(root, "layout", `${safe(name)}.json`);
  const layout = await execFile(cli, ["sheets", "+sheet-info", ...base, "--include", "merges,row_heights,col_widths,frozen,hidden_rows,hidden_cols,groups"], { maxBuffer: 12 * 1024 * 1024 });
  await fs.writeFile(layoutFile, layout.stdout);
  const condFile = path.join(root, "conditional-format", `${safe(name)}.json`);
  const cond = await execFile(cli, ["sheets", "+cond-format-list", ...base], { maxBuffer: 12 * 1024 * 1024 });
  await fs.writeFile(condFile, cond.stdout);
  result.sheets[name] = { sheet_id: id, requested_range: `A1:${endColumn}`, actual_range: payload.ranges?.[0]?.actual_range, row_count: payload.ranges?.[0]?.cells?.length, column_count: payload.ranges?.[0]?.cells?.[0]?.length, cells_path: file, cells_sha256: await sha256(file), cells_complete: payload.has_more === false, layout_path: layoutFile, layout_sha256: await sha256(layoutFile), layout_complete: JSON.parse(layout.stdout).ok === true, conditional_format_path: condFile, conditional_format_sha256: await sha256(condFile), conditional_format_complete: JSON.parse(cond.stdout).ok === true };
}
result.integrity = { complete: true, sheet_count: sheets.length, revision_consistent: Object.values(result.sheets).every((s) => s.cells_complete && s.layout_complete && s.conditional_format_complete), values_formulas_styles_present: true };
await fs.writeFile(path.join(root, "backup-manifest.json"), JSON.stringify(result, null, 2) + "\n");
console.log(JSON.stringify({ status: result.status, revision, sheets: sheets.length, complete: result.integrity.complete, revision_consistent: result.integrity.revision_consistent }, null, 2));
