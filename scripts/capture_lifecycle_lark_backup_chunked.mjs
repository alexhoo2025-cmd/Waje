#!/usr/bin/env node
import crypto from "node:crypto";
import { execFile as execFileCallback } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const token = "ZBD4wPBsricBWMktFqilAGxlgte";
const root = process.env.LARK_BACKUP_DIR || "data/outputs/lifecycle_joint/2026-08-31-7d/lark-backup-chunked";
const items = [
  { name: "原始数据总数", id: "2ea435", col: "T", ranges: [[1, 209]] },
  { name: "原始详细奖池", id: "wjhify", col: "AA", ranges: [[1, 3000], [3001, 6000], [6001, 9000], [9001, 12000], [12001, 15000], [15001, 15865]] },
  { name: "生命周期奖池分游戏汇总", id: "aIE757", col: "AE", ranges: [[1, 2000], [2001, 4000], [4001, 5364]] },
  { name: "原始数据活跃周期", id: "TEdtsX", col: "AC", ranges: [[1, 1058]] },
];
const sha = async (file) => crypto.createHash("sha256").update(await fs.readFile(file)).digest("hex");
await fs.mkdir(path.join(root, "cells"), { recursive: true });
await fs.mkdir(path.join(root, "layout"), { recursive: true });
const index = { schema_version: 1, status: "complete", token, revision: 1575, sheets: {} };
for (const item of items) {
  const base = ["--spreadsheet-token", token, "--sheet-id", item.id, "--as", "user", "--format", "json"];
  const chunks = [];
  for (let i = 0; i < item.ranges.length; i += 1) {
    const [start, end] = item.ranges[i];
    const file = path.join(root, "cells", `${item.id}-part${String(i + 1).padStart(2, "0")}.json`);
    await execFile(cli, ["sheets", "+cells-get", ...base, "--range", `A${start}:${item.col}${end}`, "--include", "value,formula,style", "--output-path", file], { maxBuffer: 10 * 1024 * 1024 });
    const payload = JSON.parse(await fs.readFile(file, "utf8"));
    if (payload.has_more !== false) throw new Error(`${item.name} part ${i + 1} is truncated`);
    chunks.push({ path: file, sha256: await sha(file), actual_range: payload.ranges?.[0]?.actual_range, returned_cell_count: payload.returned_cell_count, has_more: payload.has_more, row_start: start, row_end: end, col_end: item.col });
  }
  const layoutFile = path.join(root, "layout", `${item.id}.json`);
  const { stdout } = await execFile(cli, ["sheets", "+sheet-info", ...base, "--include", "merges,row_heights,col_widths,frozen"], { maxBuffer: 10 * 1024 * 1024 });
  await fs.writeFile(layoutFile, stdout);
  index.sheets[item.name] = { sheet_id: item.id, chunks, layout: { path: layoutFile, sha256: await sha(layoutFile) } };
}
await fs.writeFile(path.join(root, "backup-index.json"), JSON.stringify(index, null, 2));
console.log(JSON.stringify(index, null, 2));
