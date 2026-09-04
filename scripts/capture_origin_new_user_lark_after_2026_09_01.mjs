#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { execFile as execFileCallback } from "node:child_process";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const cli = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const token = process.env.LARK_TOKEN || "At8gwdbXUiPa0WkXvKqlSUNKg5d";
const root = path.resolve(process.env.LARK_AFTER_DIR || "data/outputs/origin_new_user/2026-09-01-26d/lark-after");
const defaultItems = [
  ["WajeSpecial-facebook", "9cd78d", "AR326", "A300:AR326"],
  ["WajeSpecial-googleadwords_int", "xWsChb", "AR326", "A300:AR326"],
  ["WajeSpecial-Google商店", "Cfkonh", "AR326", "A300:AR326"],
  ["WAJEIOS-AppStore商店", "25iiEi", "AR326", "A300:AR326"],
  ["WAJEBETH5", "GrWEoo", "BA305", "A279:BA305"],
  ["wajeH5-facebook", "vkV1SD", "AR228", "A202:AR228"],
  ["wajeH5ga-googlewords_int", "ef19NP", "AR228", "A202:AR228"],
  ["PWA", "gjy6I1", "BC404", "A197:BC404"],
];
const currentItems = [
  ["WajeSpecial-facebook", "9cd78d", "AR329", "A301:AR329"],
  ["WajeSpecial-googleadwords_int", "xWsChb", "AR329", "A301:AR329"],
  ["WajeSpecial-Google商店", "Cfkonh", "AR329", "A301:AR329"],
  ["WAJEIOS-AppStore商店", "25iiEi", "AR329", "A301:AR329"],
  ["WAJEBETH5", "GrWEoo", "BA308", "A280:BA308"],
  ["wajeH5-facebook", "vkV1SD", "AR231", "A203:AR231"],
  ["wajeH5ga-googlewords_int", "ef19NP", "AR231", "A203:AR231"],
  ["PWA", "gjy6I1", "BC407", "A198:BC407"],
];
const items = process.env.LARK_AFTER_CURRENT_9_4 === "1" ? currentItems : defaultItems;
const cliPath = (p) => path.relative(process.cwd(), p) || ".";
const sha = async (p) => crypto.createHash("sha256").update(await fs.readFile(p)).digest("hex");
await fs.mkdir(path.join(root, "cells"), { recursive: true });
await fs.mkdir(path.join(root, "layout"), { recursive: true });
const common = ["--spreadsheet-token", token, "--as", "user", "--format", "json"];
const rev = await execFile(cli, ["sheets", "+revision-get", ...common], { maxBuffer: 4 * 1024 * 1024 });
const revision = JSON.parse(rev.stdout).data?.revision;
const index = { schema_version: 1, status: "complete", captured_at: new Date().toISOString(), token, revision, sheets: {} };
for (const [name, id, range, layoutRange] of items) {
  const base = ["--spreadsheet-token", token, "--sheet-id", id, "--as", "user", "--format", "json"];
  const cellFile = path.join(root, "cells", `${name.replace(/[^\w.-]+/g, "_")}.json`);
  await execFile(cli, ["sheets", "+cells-get", ...base, "--range", `A1:${range}`, "--include", "value,formula,style", "--output-path", cliPath(cellFile)], { maxBuffer: 12 * 1024 * 1024 });
  const cells = JSON.parse(await fs.readFile(cellFile, "utf8"));
  if (cells.has_more !== false) throw new Error(`${name}: after cells snapshot truncated`);
  const layoutFile = path.join(root, "layout", `${name.replace(/[^\w.-]+/g, "_")}.json`);
  const layout = await execFile(cli, ["sheets", "+sheet-info", ...base, "--include", "merges,row_heights,col_widths,frozen"], { maxBuffer: 8 * 1024 * 1024 });
  await fs.writeFile(layoutFile, layout.stdout);
  index.sheets[name] = { sheet_id: id, range, row_count: cells.ranges?.[0]?.cells?.length, column_count: cells.ranges?.[0]?.cells?.[0]?.length, actual_range: cells.ranges?.[0]?.actual_range, cells_path: cellFile, cells_sha256: await sha(cellFile), cells_complete: cells.has_more === false, layout_path: layoutFile, layout_sha256: await sha(layoutFile), layout_complete: JSON.parse(layout.stdout).ok === true };
}
await fs.writeFile(path.join(root, "after-index.json"), JSON.stringify(index, null, 2) + "\n");
console.log(JSON.stringify(index, null, 2));
