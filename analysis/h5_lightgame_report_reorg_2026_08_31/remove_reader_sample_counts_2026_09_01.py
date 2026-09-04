#!/usr/bin/env python3
"""Remove nonessential cohort-count statistics from reader-facing report copy."""
from __future__ import annotations

import html
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
    result = subprocess.run([CLI, *args, "--as", "user"], cwd="/Users/robin/Documents/wajetan_analyst", env=ENV, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    out = json.loads(result.stdout)
    if out.get("ok") is not True:
        raise RuntimeError(json.dumps(out, ensure_ascii=False))
    return out


def replace(tag, needle, xml):
    doc = call(["docs", "+fetch", "--doc", DOC, "--detail", "full", "--format", "json"])["data"]["document"]
    for match in re.finditer(rf"<{tag}\b[^>]*\bid=\"([^\"]+)\"[^>]*>.*?</{tag}>", doc["content"], re.S):
        if needle in html.unescape(match.group(0)):
            block_id = match.group(1)
            break
    else:
        raise KeyError(needle)
    return call(["docs", "+update", "--doc", doc["document_id"], "--command", "block_replace", "--block-id", block_id, "--content", xml])["data"]["document"]["revision_id"]


def main():
    rev1 = replace("callout", "最大有效样本：", "<callout emoji=\"📌\" background-color=\"light-yellow\" border-color=\"yellow\"><p><b>统计口径：</b>D2 Day、D3 Day、D7 Day、D15 Day均使用源表中已达到对应观察天数的最大有效注册批次；D30 Day只作长周期方向参考。</p></callout>")
    rev2 = replace("p", "样本范围：", "<p><b>统计口径：</b>新增首充用户留存按首充人数加权，每个观察点仅使用源表中已达到对应Dn Day的最大有效批次；D30 Day只作方向参考。</p>")
    print(json.dumps({"status": "ok", "revision": rev2, "previous_revision": rev1}, ensure_ascii=False))


if __name__ == "__main__":
    main()
