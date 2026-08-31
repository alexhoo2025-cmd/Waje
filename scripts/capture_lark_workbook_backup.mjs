#!/usr/bin/env node
import { execFile as execFileCallback } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);

const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const token = "At8gwdbXUiPa0WkXvKqlSUNKg5d";
const dir = process.env.LARK_BACKUP_DIR || "data/outputs/origin_new_user/2026-08-28-30d/lark-backup";
const items = [
  ["WajeSpecial-facebook", "9cd78d", "AR322"],
  ["WajeSpecial-googleadwords_int", "xWsChb", "AR322"],
  ["WajeSpecial-Google商店", "Cfkonh", "AR322"],
  ["WAJEIOS-AppStore商店", "25iiEi", "AR322"],
  ["WAJEBETH5", "GrWEoo", "BA301"],
  ["wajeH5-facebook", "vkV1SD", "AR224"],
  ["wajeH5ga-googlewords_int", "ef19NP", "AR224"],
  ["PWA", "gjy6I1", "BC403"],
];
const safe = (value) => value.replace(/[^\w.-]+/g, "_");
await fs.mkdir(path.join(dir, "cells"), { recursive: true });
await fs.mkdir(path.join(dir, "layout"), { recursive: true });
for (const [name, id, range] of items) {
  const common = ["--spreadsheet-token", token, "--sheet-id", id, "--as", "user", "--format", "json"];
  const cellsPath = path.join(dir, "cells", `${safe(name)}.json`);
  await execFile(cli, ["sheets", "+cells-get", ...common, "--range", `A1:${range}`, "--include", "value,formula,style", "--output-path", cellsPath], { maxBuffer: 10 * 1024 * 1024 });
  const layout = await execFile(cli, ["sheets", "+sheet-info", ...common, "--include", "merges,row_heights,col_widths,frozen"], { maxBuffer: 10 * 1024 * 1024 });
  await fs.writeFile(path.join(dir, "layout", `${safe(name)}.json`), layout.stdout);
}
console.log(JSON.stringify({ status: "ok", count: items.length, directory: dir }));
