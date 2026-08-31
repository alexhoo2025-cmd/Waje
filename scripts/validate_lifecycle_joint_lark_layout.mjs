#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const ROOT = process.cwd();
const CLI = process.env.LARK_CLI_BIN || "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    const next = argv[i + 1];
    if (next && !next.startsWith("--")) { out[key] = next; i += 1; }
    else out[key] = true;
  }
  return out;
}
const args = parseArgs(process.argv.slice(2));
const outputDir = path.resolve(args["output-dir"] || "data/outputs/lifecycle_joint/2026-08-28-30d");
const token = args.token || "ZBD4wPBsricBWMktFqilAGxlgte";

function columnLetter(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) { const remainder = (value - 1) % 26; result = String.fromCharCode(65 + remainder) + result; value = Math.floor((value - 1) / 26); }
  return result;
}
async function readJson(file) { return JSON.parse(await fs.readFile(file, "utf8")); }
async function writeJson(file, value) { await fs.writeFile(file, `${JSON.stringify(value, null, 2)}\n`, "utf8"); }
function runCli(argv) {
  return new Promise((resolve, reject) => {
    const child = spawn(CLI, argv, { cwd: ROOT, env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" }, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = ""; let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk; }); child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code) => { let payload = null; try { payload = JSON.parse(stdout); } catch {} if (code !== 0 || !payload?.ok) reject(new Error(`lark-cli failed code=${code}: ${stderr || stdout}`)); else resolve(payload); });
  });
}
function styleOf(cell) { return { cell_styles: cell?.cell_styles || null, border_styles: cell?.border_styles || null }; }
function same(left, right) { return JSON.stringify(left) === JSON.stringify(right); }

const planReceipt = await readJson(path.join(outputDir, "write-plan.json"));
const backup = await readJson(path.join(outputDir, "backup-manifest.json"));
const semantics = ["summary", "detail", "game", "active"];
const sheetAfter = {};
const checks = [];
const failures = [];
for (const semantic of semantics) {
  const plan = planReceipt.semantic_mapping[semantic];
  const backupSheet = backup.sheet_snapshots.find((item) => item.sheet_id === plan.sheet_id);
  const afterInfo = await runCli(["sheets", "+sheet-info", "--spreadsheet-token", token, "--sheet-id", plan.sheet_id, "--include", "merges,row_heights,col_widths,hidden_rows,hidden_cols,groups,frozen", "--as", "user"]);
  sheetAfter[semantic] = afterInfo;
  const beforeInfo = await readJson(path.join(ROOT, backupSheet.sheet_info));
  const beforeData = beforeInfo.data || {};
  const afterData = afterInfo.data || {};
  const structure = {
    before: { row_count: beforeData.row_count, column_count: beforeData.column_count, frozen_rows: beforeData.frozen_rows, frozen_columns: beforeData.frozen_columns, merged_cells: beforeData.merged_cells, col_widths: beforeData.col_widths, hidden_rows: beforeData.hidden_rows, hidden_cols: beforeData.hidden_cols },
    after: { row_count: afterData.row_count, column_count: afterData.column_count, frozen_rows: afterData.frozen_rows, frozen_columns: afterData.frozen_columns, merged_cells: afterData.merged_cells, col_widths: afterData.col_widths, hidden_rows: afterData.hidden_rows, hidden_cols: afterData.hidden_cols },
  };
  if (structure.before.column_count !== structure.after.column_count) failures.push(`${semantic}: column_count changed`);
  if (JSON.stringify(structure.before.frozen_rows) !== JSON.stringify(structure.after.frozen_rows) || JSON.stringify(structure.before.frozen_columns) !== JSON.stringify(structure.after.frozen_columns)) failures.push(`${semantic}: frozen state changed`);
  for (const insertion of plan.insertions || []) {
    const start = Number(insertion.position);
    const end = start + Number(insertion.count) - 1;
    const anchor = Number(insertion.base_position) - 1;
    const chunk = backupSheet.cells_chunks.find((item) => item.start <= anchor && item.end >= anchor);
    if (!chunk) { failures.push(`${semantic}: missing backup style anchor row ${anchor}`); continue; }
    const payload = await readJson(path.join(ROOT, chunk.data));
    const anchorCellRow = payload.ranges?.[0]?.cells?.[anchor - Number(chunk.start)];
    if (!anchorCellRow) { failures.push(`${semantic}: missing anchor cells row ${anchor}`); continue; }
    const lastCol = columnLetter(Number(plan.current_column_count) - 1);
    const sampled = {};
    for (const rowNumber of [start, end]) {
      const after = await runCli(["sheets", "+cells-get", "--spreadsheet-token", token, "--sheet-id", plan.sheet_id, "--range", `A${rowNumber}:${lastCol}${rowNumber}`, "--include", "value,formula,style", "--as", "user"]);
      const cells = after.data?.ranges?.[0]?.cells?.[0] || [];
      if (after.data?.has_more) failures.push(`${semantic}: style sample ${rowNumber} truncated`);
      const mismatchColumns = [];
      for (let index = 0; index < Math.min(anchorCellRow.length, cells.length); index += 1) if (!same(styleOf(anchorCellRow[index]), styleOf(cells[index]))) mismatchColumns.push(columnLetter(index));
      sampled[rowNumber] = { anchor_row: anchor, sampled_row: rowNumber, anchor_date_format: anchorCellRow[0]?.cell_styles?.number_format || null, sampled_date_format: cells[0]?.cell_styles?.number_format || null, mismatch_columns: mismatchColumns };
      if (mismatchColumns.length) failures.push(`${semantic}: inserted row ${rowNumber} style differs from anchor ${anchor} at ${mismatchColumns.join(",")}`);
    }
    checks.push({ semantic, insertion: { start, end, base_position: insertion.base_position, count: insertion.count, dates: insertion.dates }, samples: sampled });
  }
}
const result = { schema_version: 1, checked_at: new Date().toISOString(), revision: planReceipt.revision_before, status: failures.length ? "failed" : "passed", checks, sheet_after: sheetAfter, failures, note: "新增/补行样式与插入位置前一行逐单元格比较；未删除任何原有行。" };
await writeJson(path.join(outputDir, "layout-validation.json"), result);
process.stdout.write(`${JSON.stringify({ status: result.status, checks: checks.length, failures: failures.length }, null, 2)}\n`);
if (failures.length) process.exitCode = 1;
