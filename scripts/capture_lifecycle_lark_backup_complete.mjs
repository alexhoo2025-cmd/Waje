#!/usr/bin/env node
import crypto from "node:crypto";
import { execFile as execFileCallback } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const token = "ZBD4wPBsricBWMktFqilAGxlgte";
const root = process.env.LARK_BACKUP_DIR || "data/outputs/lifecycle_joint/2026-08-31-7d/lark-backup-complete";
const defaultItems = [
  { name: "原始数据总数", id: "2ea435", col: "T", rows: 212, sample: "A168:T174" },
  { name: "原始详细奖池", id: "wjhify", col: "AA", rows: 16330, sample: "A5037:AA5042" },
  { name: "生命周期奖池分游戏汇总", id: "aIE757", col: "AE", rows: 5457, sample: "A5452:AE5457" },
  { name: "原始数据活跃周期", id: "TEdtsX", col: "AC", rows: 1070, sample: "A945:AC950" },
];
const currentItems = [
  { name: "原始数据总数", id: "2ea435", col: "T", rows: 214, sample: "A168:T178" },
  { name: "原始详细奖池", id: "wjhify", col: "AA", rows: 16640, sample: "A5037:AA5052" },
  { name: "生命周期奖池分游戏汇总", id: "aIE757", col: "AE", rows: 5519, sample: "A5452:AE5470" },
  { name: "原始数据活跃周期", id: "TEdtsX", col: "AC", rows: 1078, sample: "A945:AC962" },
];
const items = process.env.LARK_BACKUP_CURRENT === "1" ? currentItems : defaultItems;
const sha = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
const safe = (value) => value.replace(/[^\w.-]+/g, "_");
await fs.mkdir(path.join(root, "values"), { recursive: true });
await fs.mkdir(path.join(root, "style-samples"), { recursive: true });
await fs.mkdir(path.join(root, "layout"), { recursive: true });
const revisionResult = await execFile(cli, ["sheets", "+revision-get", "--spreadsheet-token", token, "--as", "user", "--format", "json"], { maxBuffer: 4 * 1024 * 1024 });
const revision = JSON.parse(revisionResult.stdout).data?.revision;
const index = { schema_version: 1, status: "complete", token, revision, backup_method: "full csv values plus bounded cells-get formula/style samples and full layout", sheets: {} };
for (const item of items) {
  const base = ["--spreadsheet-token", token, "--sheet-id", item.id, "--as", "user", "--format", "json"];
  const valuesFile = path.join(root, "values", `${item.id}.json`);
  await execFile(cli, ["sheets", "+csv-get", ...base, "--output-path", valuesFile], { maxBuffer: 10 * 1024 * 1024 });
  const valuesPayload = JSON.parse(await fs.readFile(valuesFile, "utf8"));
  if (valuesPayload.has_more !== false) throw new Error(`${item.name}: full CSV snapshot is truncated`);
  const sampleFile = path.join(root, "style-samples", `${item.id}.json`);
  await execFile(cli, ["sheets", "+cells-get", ...base, "--range", item.sample, "--include", "value,formula,style", "--output-path", sampleFile], { maxBuffer: 10 * 1024 * 1024 });
  const samplePayload = JSON.parse(await fs.readFile(sampleFile, "utf8"));
  if (samplePayload.has_more !== false) throw new Error(`${item.name}: style sample is truncated`);
  const layoutFile = path.join(root, "layout", `${item.id}.json`);
  const { stdout } = await execFile(cli, ["sheets", "+sheet-info", ...base, "--include", "merges,row_heights,col_widths,frozen"], { maxBuffer: 10 * 1024 * 1024 });
  await fs.writeFile(layoutFile, stdout);
  index.sheets[item.name] = { sheet_id: item.id, expected_rows: item.rows, values: { path: valuesFile, sha256: await sha(valuesFile), complete: valuesPayload.has_more === false, actual_range: valuesPayload.actual_range, row_count: valuesPayload.row_count, column_count: valuesPayload.col_count, revision: valuesPayload.revision }, style_sample: { path: sampleFile, sha256: await sha(sampleFile), complete: samplePayload.has_more === false, actual_range: samplePayload.ranges?.[0]?.actual_range, returned_cell_count: samplePayload.returned_cell_count, revision: samplePayload.revision }, layout: { path: layoutFile, sha256: await sha(layoutFile), complete: true, revision: JSON.parse(stdout).data?.revision } };
}
await fs.writeFile(path.join(root, "backup-index.json"), JSON.stringify(index, null, 2));
console.log(JSON.stringify(index, null, 2));
