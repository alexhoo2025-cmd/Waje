#!/usr/bin/env python3
"""Read back the revised Feishu report and persist a non-sensitive receipt."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC_ID = "GyZddVm2powgFBxLwH0l18Qzguf"
OUTPUT = ROOT / "full_document_optimization_receipt_2026_09_01.json"
env = os.environ.copy()
env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
result = subprocess.run([CLI, "docs", "+fetch", "--doc", DOC_ID, "--detail", "with-ids", "--format", "json", "--as", "user"], cwd=PROJECT, env=env, text=True, capture_output=True)
if result.returncode:
    raise SystemExit(result.stderr)
response = json.loads(result.stdout)
if response.get("ok") is not True:
    raise SystemExit(json.dumps(response, ensure_ascii=False))
doc = response["data"]["document"]
OUTPUT.write_text(json.dumps({"status": "ok", "revision_id": doc["revision_id"], "content": doc["content"]}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "ok", "revision_id": doc["revision_id"]}, ensure_ascii=False))
