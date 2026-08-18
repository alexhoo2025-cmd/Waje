#!/usr/bin/env python3
"""Bind an existing Lark custom app to the official CLI without persisting secrets."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import subprocess
from pathlib import Path


def resolve_cli() -> Path:
    explicit = os.environ.get("LARK_CLI_BIN", "").strip()
    if explicit and Path(explicit).expanduser().is_file():
        return Path(explicit).expanduser()
    found = shutil.which("lark-cli")
    if found:
        return Path(found)
    candidates = sorted(Path.home().glob(".local/node-*/bin/lark-cli"), reverse=True)
    if candidates:
        return candidates[0]
    raise FileNotFoundError("lark-cli not found; run: npx -y @larksuite/cli@latest install")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-id", default="", help="Lark custom app ID; prompts when omitted.")
    args = parser.parse_args()
    app_id = args.app_id.strip() or input("Lark App ID: ").strip()
    if not app_id:
        raise SystemExit("App ID is required")
    app_secret = getpass.getpass("Lark App Secret（输入不显示，也不会写入项目）: ")
    if not app_secret:
        raise SystemExit("App Secret is required")
    completed = subprocess.run(
        [
            str(resolve_cli()),
            "config",
            "init",
            "--app-id",
            app_id,
            "--app-secret-stdin",
            "--brand",
            "lark",
            "--lang",
            "zh_cn",
        ],
        input=app_secret + "\n",
        text=True,
        check=False,
        capture_output=True,
    )
    app_secret = ""  # Drop the Python reference immediately after CLI handoff.
    if completed.returncode != 0:
        print((completed.stderr or completed.stdout).strip())
        raise SystemExit(completed.returncode)
    verify = subprocess.run(
        [str(resolve_cli()), "auth", "status", "--json", "--verify"],
        text=True,
        check=False,
        capture_output=True,
    )
    try:
        status = json.loads(verify.stdout or verify.stderr or "{}")
    except json.JSONDecodeError:
        status = {}
    bot = status.get("identities", {}).get("bot", {}) if isinstance(status, dict) else {}
    if not bot.get("verified"):
        message = str(bot.get("message") or "应用凭证未通过服务端验证")
        print(f"绑定已保存，但验真失败：{message}")
        print("请在 Lark 开放平台确认 App ID 与当前 App Secret 后重新运行本脚本。")
        return 2
    print("Lark CLI 应用绑定并验真成功。App Secret 未写入项目文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
