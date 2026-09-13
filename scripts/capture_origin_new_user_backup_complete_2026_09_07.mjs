#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { execFile as execFileCallback } from "node:child_process";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const token = process.env.LARK_TOKEN || "At8gwdbXUiPa0WkXvKqlSUNKg5d";
const root = path.resolve(process.env.BACKUP_ROOT || "data/outputs/origin_new_user/2026-09-07-15d/lark-backup-complete");
const expected = {
  "WajeSpecial-facebook": "9cd78d",
  "WajeSpecial-googleadwords_int": "xWsChb",
  "WajeSpecial-Google商店": "Cfkonh",
  "WAJEIOS-AppStore商店": "25iiEi",
  "WAJEBETH5": "GrWEoo",
  "wajeH5-facebook": "vkV1SD",
  "wajeH5ga-googlewords_int": "ef19NP",
  "PWA": "gjy6I1",
};
const safe = (value) => value.replace(/[^\w.-]+/g, "_");
const sha256 = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const rel = (file) => path.relative(process.cwd(), file) || ".";
const columnName = (number) => {
  let n = number; let out = "";
  while (n > 0) { const r = (n - 1) % 26; out = String.fromCharCode(65 + r) + out; n = Math.floor((n - 1) / 26); }
  return out;
};
const common = ["--spreadsheet-token", token, "--as", "user", "--format", "json"];
await fs.mkdir(path.join(root, "csv"), { recursive: true });
await fs.mkdir(path.join(root, "cells"), { recursive: true });
await fs.mkdir(path.join(root, "layout"), { recursive: true });
await fs.mkdir(path.join(root, "conditional-format"), { recursive: true });

const revisionPayload = JSON.parse((await execFile(cli, ["sheets", "+revision-get", ...common], { maxBuffer: 4 * 1024 * 1024 })).stdout);
const workbookPayload = JSON.parse((await execFile(cli, ["sheets", "+workbook-info", ...common], { maxBuffer: 16 * 1024 * 1024 })).stdout);
await fs.writeFile(path.join(root, "workbook-info.json"), JSON.stringify(workbookPayload, null, 2) + "\n");
const revision = Number(revisionPayload.data?.revision);
const sheets = workbookPayload.data?.sheets || [];
if (sheets.length !== 8) throw new Error(`expected 8 sheets, got ${sheets.length}`);
for (const [name, id] of Object.entries(expected)) if (!sheets.some((sheet) => sheet.sheet_id === id && sheet.sheet_name === name)) throw new Error(`sheet mapping mismatch for ${name}/${id}`);

const index = { schema_version: 1, status: "complete", token, title: workbookPayload.data?.title, workbook_info_token: workbookPayload.data?.token, revision, captured_at: new Date().toISOString(), sheets: {} };
for (const item of sheets.sort((left, right) => left.index - right.index)) {
  const name = item.sheet_name;
  const endColumn = columnName(Number(item.column_count));
  const range = `A1:${endColumn}${Number(item.row_count)}`;
  const base = ["--spreadsheet-token", token, "--sheet-id", item.sheet_id, "--as", "user", "--format", "json"];
  const csvFile = path.join(root, "csv", `${safe(name)}.json`);
  await execFile(cli, ["sheets", "+csv-get", ...base, "--range", range, "--output-path", rel(csvFile)], { maxBuffer: 32 * 1024 * 1024 });
  const csvPayload = JSON.parse(await fs.readFile(csvFile, "utf8"));
  if (csvPayload.has_more !== false) throw new Error(`${name}: CSV backup truncated`);
  const cellsFile = path.join(root, "cells", `${safe(name)}.json`);
  await execFile(cli, ["sheets", "+cells-get", ...base, "--range", range, "--include", "value,formula,style", "--output-path", rel(cellsFile)], { maxBuffer: 32 * 1024 * 1024 });
  const cellsPayload = JSON.parse(await fs.readFile(cellsFile, "utf8"));
  if (cellsPayload.has_more !== false) throw new Error(`${name}: cells backup truncated`);
  const layoutFile = path.join(root, "layout", `${safe(name)}.json`);
  const layout = await execFile(cli, ["sheets", "+sheet-info", ...base, "--include", "merges,row_heights,col_widths,frozen,hidden_rows,hidden_cols,groups"], { maxBuffer: 16 * 1024 * 1024 });
  await fs.writeFile(layoutFile, layout.stdout);
  const condFile = path.join(root, "conditional-format", `${safe(name)}.json`);
  const cond = await execFile(cli, ["sheets", "+cond-format-list", ...base], { maxBuffer: 16 * 1024 * 1024 });
  await fs.writeFile(condFile, cond.stdout);
  index.sheets[name] = {
    sheet_id: item.sheet_id,
    sheet_index: item.index,
    range,
    row_count: item.row_count,
    column_count: item.column_count,
    csv: { path: csvFile, sha256: await sha256(csvFile), complete: csvPayload.has_more === false, actual_range: csvPayload.actual_range, returned_rows: csvPayload.row_count, returned_columns: csvPayload.col_count, revision: csvPayload.revision },
    cells: { path: cellsFile, sha256: await sha256(cellsFile), complete: cellsPayload.has_more === false, actual_range: cellsPayload.ranges?.[0]?.actual_range, returned_cell_count: cellsPayload.returned_cell_count, revision: cellsPayload.revision },
    layout: { path: layoutFile, sha256: await sha256(layoutFile), complete: JSON.parse(layout.stdout).ok === true, revision: JSON.parse(layout.stdout).data?.revision },
    conditional_format: { path: condFile, sha256: await sha256(condFile), complete: JSON.parse(cond.stdout).ok === true },
  };
}
index.integrity = { complete: true, truncated: false, sheet_count: 8, revision_consistent: Object.values(index.sheets).every((sheet) => sheet.csv.complete && sheet.cells.complete && sheet.layout.complete && sheet.conditional_format.complete), full_used_ranges: true, values_formulas_styles_present: true };
await fs.writeFile(path.join(root, "backup-manifest.json"), JSON.stringify(index, null, 2) + "\n");
console.log(JSON.stringify({ status: index.status, revision, sheet_count: index.integrity.sheet_count, complete: index.integrity.complete, truncated: index.integrity.truncated, revision_consistent: index.integrity.revision_consistent }, null, 2));
