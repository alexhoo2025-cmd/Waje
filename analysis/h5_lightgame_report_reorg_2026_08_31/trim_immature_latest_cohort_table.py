#!/usr/bin/env python3
"""Keep only mature retention points in the latest-cohort snapshot table."""
from __future__ import annotations

import json
import os
import re
import subprocess


CLI = "/Users/robin/.local/node-v24.18.1-darwin-arm64/bin/lark-cli"
DOC = "https://ksg964l11fam.sg.larksuite.com/wiki/QYbiws4OEit03Uke92rlfzmcgWb"
ENV = os.environ.copy()
ENV["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
ENV["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"


def call(args):
    done = subprocess.run([CLI, *args, "--as", "user"], cwd="/Users/robin/Documents/wajetan_analyst", env=ENV, text=True, capture_output=True)
    if done.returncode:
        raise RuntimeError(done.stderr)
    out = json.loads(done.stdout)
    if out.get("ok") is not True:
        raise RuntimeError(json.dumps(out, ensure_ascii=False))
    return out


def main():
    doc = call(["docs", "+fetch", "--doc", DOC, "--detail", "full", "--format", "json"])["data"]["document"]
    for match in re.finditer(r"<table\b[^>]*\bid=\"([^\"]+)\"[^>]*>.*?</table>", doc["content"], re.S):
        if "8月27日注册批次" in match.group(0):
            table_id = match.group(1)
            break
    else:
        raise KeyError("latest cohort table not found")
    xml = """<table><thead><tr><th background-color=\"light-gray\"><p>8月27日注册批次</p></th><th background-color=\"light-gray\"><p>新增</p></th><th background-color=\"light-gray\"><p>D2 Day</p></th><th background-color=\"light-gray\"><p>D3 Day</p></th></tr></thead><tbody><tr><td><p>H5自然</p></td><td><p>3,149</p></td><td><p>46.3%</p></td><td><p>31.6%</p></td></tr><tr><td><p>H5 Facebook</p></td><td><p>5,451</p></td><td><p>32.4%</p></td><td><p>20.6%</p></td></tr><tr><td><p>H5 Google</p></td><td><p>851</p></td><td><p>44.2%</p></td><td><p>23.4%</p></td></tr><tr><td><p>PWA自然</p></td><td><p>550</p></td><td><p>48.9%</p></td><td><p>29.6%</p></td></tr></tbody></table><p><b>说明：</b>该快照只展示截至8月30日已达到统计口径的D2 Day和D3 Day；D7 Day及更长周期尚未达到观察日，不在本表展示。</p>"""
    out = call(["docs", "+update", "--doc", doc["document_id"], "--command", "block_replace", "--block-id", table_id, "--content", xml])
    print(json.dumps({"status": "ok", "revision": out["data"]["document"]["revision_id"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
