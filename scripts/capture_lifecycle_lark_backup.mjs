#!/usr/bin/env node
import { execFile as execFileCallback } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const token = "ZBD4wPBsricBWMktFqilAGxlgte";
const root = process.env.LARK_BACKUP_DIR || "data/outputs/lifecycle_joint/2026-08-31-7d/lark-backup";
const items = [
  ["原始数据总数", "2ea435", "T209"],
  ["原始详细奖池", "wjhify", "AA15865"],
  ["生命周期奖池分游戏汇总", "aIE757", "AE5364"],
  ["原始数据活跃周期", "TEdtsX", "AC1058"],
];
const safe = (value) => value.replace(/[^\w.-]+/g, "_");
await fs.mkdir(path.join(root, "cells"), { recursive: true });
await fs.mkdir(path.join(root, "layout"), { recursive: true });
for (const [name, id, range] of items) {
  const base = ["--spreadsheet-token", token, "--sheet-id", id, "--as", "user", "--format", "json"];
  const cellsPath = path.join(root, "cells", `${id}.json`);
  await execFile(cli, ["sheets", "+cells-get", ...base, "--range", `A1:${range}`, "--include", "value,formula,style", "--output-path", cellsPath], { maxBuffer: 10 * 1024 * 1024 });
  const { stdout } = await execFile(cli, ["sheets", "+sheet-info", ...base, "--include", "merges,row_heights,col_widths,frozen"], { maxBuffer: 10 * 1024 * 1024 });
  await fs.writeFile(path.join(root, "layout", `${id}.json`), stdout);
}
console.log(JSON.stringify({ status: "ok", token, root, sheets: items.map(([name]) => name) }, null, 2));
