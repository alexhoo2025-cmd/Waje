#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";

const CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli";
const TOKEN = process.env.LARK_TOKEN || "At8gwdbXUiPa0WkXvKqlSUNKg5d";
const runDir = path.resolve(process.env.RUN_DIR || "data/outputs/origin_new_user/2026-09-01-26d");
const plan = JSON.parse(await fs.readFile(path.join(runDir, "lark-write-plan.json"), "utf8"));
const writes = JSON.parse(await fs.readFile(path.join(runDir, "lark-writes.json"), "utf8"));
const expectedRevision = Number(process.env.EXPECTED_REVISION || plan.target_revision_before_write_expected);

function runCli(argv, stdin = undefined) {
  return new Promise((resolve, reject) => {
    const child = spawn(CLI, argv, { cwd: process.cwd(), env: { ...process.env, LARKSUITE_CLI_NO_UPDATE_NOTIFIER: "1", LARKSUITE_CLI_NO_SKILLS_NOTIFIER: "1" }, stdio: ["pipe", "pipe", "pipe"] });
    let stdout = ""; let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code) => {
      let payload; try { payload = JSON.parse(stdout); } catch { payload = null; }
      if (code !== 0 || !payload?.ok) reject(new Error(`lark-cli failed code=${code}: ${stderr || stdout}`));
      else resolve(payload);
    });
    child.stdin.end(stdin ?? "");
  });
}
async function currentRevision() {
  const result = await runCli(["sheets", "+revision-get", "--spreadsheet-token", TOKEN, "--as", "user", "--format", "json"]);
  return Number(result.data.revision);
}
const revisionBefore = await currentRevision();
if (revisionBefore !== expectedRevision) throw new Error(`revision changed after plan: expected ${expectedRevision}, got ${revisionBefore}`);

const insertReceipts = [];
for (const item of plan.insertions) {
  const result = await runCli(["sheets", "+dim-insert", "--spreadsheet-token", TOKEN, "--sheet-id", item.sheet_id, "--position", String(item.position), "--count", String(item.insert_count), "--inherit-style", "before", "--as", "user", "--format", "json"]);
  insertReceipts.push({ ...item, revision: result.data?.revision, response: result.data });
}

// The plan ranges are based on the pre-insertion row positions.  All insertions
// are at each sheet's tail, so the ranges remain valid after the new row exists.
const result = await runCli(["sheets", "+cells-set", "--spreadsheet-token", TOKEN, "--writes", "-", "--as", "user", "--format", "json"], JSON.stringify(writes));
const revisionAfter = await currentRevision();
const receipt = {
  schema_version: 1,
  status: "ok",
  completed_at: new Date().toISOString(),
  target_token: TOKEN,
  revision_before: revisionBefore,
  revision_after: revisionAfter,
  insertions: insertReceipts,
  write_response: result.data,
  write_region_count: writes.length,
  write_regions: writes.map((w) => ({ sheet_id: w.sheet_id, range: w.range, rows: w.cells.length, columns: w.cells[0]?.length || 0 })),
  accepted_dates: plan.accepted_dates,
  excluded_not_mature_dates: plan.excluded_not_mature_dates,
  zero_ledger_count: plan.zero_ledger_count,
};
await fs.writeFile(path.join(runDir, "lark-write-receipt.json"), JSON.stringify(receipt, null, 2) + "\n");
console.log(JSON.stringify({ status: receipt.status, revision: `${revisionBefore}->${revisionAfter}`, write_regions: writes.length, zero_ledger_count: plan.zero_ledger_count }, null, 2));
