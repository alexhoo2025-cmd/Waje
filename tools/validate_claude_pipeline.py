#!/usr/bin/env python3
"""Verify routine Play reports no longer dispatch Claude or add collaboration."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",default="pipeline_fixture");a=p.parse_args()
    if not a.run_id.replace("_", "").isalnum():raise ValueError("invalid fixture name")
    fixture=ROOT/"analysis/agent_collaboration_validation_2026_09_04"/a.run_id
    if fixture.exists():raise ValueError("fixture already exists; preserve previous run")
    directory=fixture/"data/outputs/play_reviews/2026-09-04"
    directory.mkdir(parents=True)
    items=[{"rating":rating,"record_state":"new","topics":["general_product_feedback"],"review_text":"Synthetic fixture only","rating_bucket":"positive" if rating>=4 else "negative"} for rating in (5,4,2,1)]
    (directory/"analysis.json").write_text(json.dumps({"items":items}),encoding="utf-8")
    (directory/"quality.json").write_text(json.dumps({"status":"ok","collection":{"status":"ok"},"shortfall":0}),encoding="utf-8")
    env={**os.environ,"WAJE_ANALYST_ROOT":str(fixture),"WAJE_CLAUDE_ALLOW_TEST_ROOT":"1","WAJE_CLAUDE_DISABLE":"0"}
    subprocess.run([sys.executable,str(ROOT/"scripts/build_play_reviews_report.py"),"--date","2026-09-04","--period","daily"],env=env,check=True)
    receipt=json.loads((directory/"report-receipt.json").read_text())
    text=(fixture/receipt["html"]).read_text()
    assert "collaboration" not in receipt
    assert "协作重点摘录" not in text
    assert receipt["summary"]["new_count"]==4
    print(json.dumps({"status":"passed","fixture_only":True,"routine_collaboration":False,"html":str(fixture/receipt["html"]),"original_metrics_preserved":True},ensure_ascii=False))


if __name__=="__main__":main()
