#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC_ID = "GyZddVm2powgFBxLwH0l18Qzguf"

ordered = [
    "doxlg7eXZeJ4M7pnF4OS0Y1odBd", "doxlgdYLUqkzFbqmgWLcUwZnzPd",
    "doxlge17K0NG8rWNNgqaE1EADme", "doxlgkXdh0ocoyPzEMZBqi4N7lF", "doxlgYlbhMfAu8IOd3uaTyUUvCe", "doxlgo3bdysGjM5gH6KQ51p2tHc",
    "doxlgOnJxaPzrQsEqckPYCXDiBh", "doxlgH0gh6anBfB6irNTZJFO3Qb", "doxlgEsURSX1yS1kpIRGV3uHwRe", "doxlgeIb9IUCXkNoVr0pA6qIu1b", "doxlghy8QZ2qThdDlvTzPHKuPrb", "doxlgQ6nCmra57EUGc99FNTPlHb", "doxlgsXivWjXpwDZ5uJf2FJb0Yb",
    "doxlgapdHc8ZCDjOA1lEAdTtDmg", "doxlgrPLsn1XjK3mbGVsQD4qrfh", "doxlgsQ5Hqrr2gptt2vLPWP49Sd", "doxlgbGgqvlFyUEBWeESQECeoPf", "doxlgnxMnxY44q38iNKyjO57JdC", "doxlgRsoQnB3jo6mMVx8jBC4xhd",
    "doxlg0WwlSciS5vZe7bkSDnCs4c", "doxlg6dkWviVRpWXHuXDX3ZKLhg", "doxlgXyatalD8YSpKRyG8y3e3yd", "doxlgZOeFWwz2lwR5u1LB8hlUbc",
    "doxlgKug97e8sBpfFtBbMgX4rDg", "doxlgK1yam9yiB9ipnQYXR9Xccb", "doxlgcaL3wj6EsHmX5Js9d4itIc",
    "doxlgIRH18Hpio4HpF2RfFlHSUb", "doxlg1HqOOIq3zmZsu3PpspH6ae", "doxlgiuR3Up5nHUvsOikniiG7eY", "doxlg46r1Hpw5aRUHVmFva0VIye", "doxlgAutphogvrVxuskp8V1jX5d", "doxlgrdu04YxmLSB0bxpiHnEThd",
    "doxlg0Lz2SFS4Qv0l3I5JB0Fg9b", "doxlgeVyZVVv8vF8zl6nNASXpju", "doxlgqdBXhKuEF4G1BOFQBXK40b", "doxlgzB4zYDwe30pVtAcuj2a0Xb",
    "doxlg2SkS4gnyVST9Z0mHYpScwU", "doxlg0hGumudrxf3QdOWsfdiHxh", "doxlgfTAk6rbmpcIEhbehko6ARh", "doxlgC9KOogBZA9sG2ewYnJXSCe", "doxlgdD15Z3cpjvDsASll8FsvFf",
    "doxlgxkqAqO7gBcaL97mkb9AoTe", "doxlgWx4KkuYbbjzkcbC97ajKqd", "doxlgZYtFLJdLa2fBYVTSO3o32g", "doxlg22Ve6h8MLkM9PNBE208Acb",
    "doxlg9sesWX8hLDnG4lxC3nBM0f", "doxlgcgz0UuN6TkvLf7Fn8i2sfd", "doxlgqIgyRQM9iJlAvwy2uHYT4c", "doxlgMuNA8EhjgCWeBzzTcf8bwg",
    "doxlgrsaB0XKnptxocFXYZZmtnf", "doxlgSSWYSjI1llQ70hftXbm1df", "doxlgbMGh9e8La2ABPtRYSuiosd",
    "doxlguEROsvGvuCJVeIBG0xdWUf", "doxlgAR7UvUI3qDARbBXVVntjCd", "doxlgqTKUOi8w6dNSQaNJTznj7e", "doxlg07InegsYIy8JsGblsDQfZd", "doxlglStC95CSMlxk4F8X1NJg9b", "doxlgi1vvUz4SqEIyhpP2SPx9sf", "doxlgr5rnmf1rWoDLsasonn63tc",
    "doxlghCz3gaS64NkY8BqAeIki6b", "doxlgQhVYBi2emAf6uBU1rR4Ygc",
]

env = os.environ.copy()
env["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
env["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"

move = subprocess.run([
    CLI, "docs", "+update", "--doc", DOC_ID, "--command", "block_move_after",
    "--block-id", DOC_ID, "--src-block-ids", ",".join(ordered), "--as", "user",
], cwd=PROJECT, env=env, text=True, capture_output=True)
if move.returncode != 0:
    raise SystemExit(move.stderr)

fetch = subprocess.run([
    CLI, "docs", "+fetch", "--doc", DOC_ID, "--scope", "outline",
    "--max-depth", "3", "--detail", "with-ids", "--as", "user", "--format", "json",
], cwd=PROJECT, env=env, text=True, capture_output=True, check=True)
payload = json.loads(fetch.stdout)
receipt = {
    "status": "ok",
    "ordered_blocks": len(ordered),
    "revision_id": payload["data"]["document"]["revision_id"],
    "outline": payload["data"]["document"]["content"],
}
(ROOT / "feishu_reorg_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": "ok", "revision_id": receipt["revision_id"], "ordered_blocks": len(ordered)}, ensure_ascii=False))
