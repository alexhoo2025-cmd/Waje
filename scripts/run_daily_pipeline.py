#!/usr/bin/env python3
"""Run the daily intelligence pipeline in dependency order."""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(script: str, date: str) -> None:
    command = [sys.executable, str(ROOT / script), "--date", date]
    subprocess.run(command, cwd=ROOT, check=True)


def run_command(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def stage_status(date: str, stage: str) -> str:
    if stage == "collect":
        manifests = sorted((ROOT / "data/raw" / date).glob("manifest-*.json"))
        if not manifests: return "degraded"
        payload = json.loads(manifests[-1].read_text(encoding="utf-8"))
        return "degraded" if any(item.get("status") != "ok" for item in payload.get("items", [])) else "ok"
    if stage == "wechat_collect":
        manifests = sorted((ROOT / "data/raw/wechat" / date).glob("manifest-*.json"))
        if not manifests: return "degraded"
        return json.loads(manifests[-1].read_text(encoding="utf-8")).get("status", "degraded")
    if stage == "quality":
        quality_path = ROOT / "data/outputs" / date / "quality.json"
        if not quality_path.exists(): return "degraded"
        return json.loads(quality_path.read_text(encoding="utf-8")).get("status", "degraded")
    if stage == "report":
        report_path = ROOT / "knowledge/03-竞品/日报" / f"{date}-Waje产品与竞品情报.md"
        return "ok" if report_path.exists() else "degraded"
    if stage == "play_reviews_quality":
        quality_path = ROOT / "data/outputs/play_reviews" / date / "quality.json"
        if not quality_path.exists(): return "degraded"
        return json.loads(quality_path.read_text(encoding="utf-8")).get("status", "degraded")
    if stage == "play_reviews_knowledge":
        note_path = ROOT / "knowledge/01-产品/Google Play用户评价" / f"{date}-Google Play用户评价分析.md"
        return "ok" if note_path.exists() else "degraded"
    return "ok"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    parser.add_argument("--skip-collect", action="store_true")
    parser.add_argument("--skip-play-reviews", action="store_true")
    parser.add_argument("--include-play-reviews", action="store_true", help="Run the Play review stages inline for manual/backward-compatible runs")
    args = parser.parse_args()
    date = args.date or datetime.datetime.now().astimezone().date().isoformat()
    started_at = datetime.datetime.now().astimezone().isoformat()
    stages = []
    status = "error"
    try:
        if not args.skip_collect:
            run("scripts/collect_intelligence.py", date)
            stages.append({"stage": "collect", "status": stage_status(date, "collect")})
            if args.include_play_reviews and not args.skip_play_reviews:
                run_command(["node", str(ROOT / "scripts/collect_play_reviews.mjs"), "--date", date, "--mode", "incremental"])
                stages.append({"stage": "play_reviews_collect", "status": stage_status(date, "play_reviews_collect")})
                for stage, script in [
                    ("play_reviews_normalize", "scripts/normalize_play_reviews.py"),
                    ("play_reviews_analyze", "scripts/analyze_play_reviews.py"),
                    ("play_reviews_quality", "scripts/assess_play_reviews_quality.py"),
                    ("play_reviews_knowledge", "scripts/build_play_reviews_knowledge.py"),
                ]:
                    run(script, date)
                    stages.append({"stage": stage, "status": stage_status(date, stage)})
            else:
                stages.append({"stage": "play_reviews_collect", "status": "skipped"})
            run("scripts/collect_wechat_articles.py", date)
            stages.append({"stage": "wechat_collect", "status": stage_status(date, "wechat_collect")})
        else:
            stages.append({"stage": "collect", "status": "skipped"})
            stages.append({"stage": "play_reviews_collect", "status": "skipped"})
            stages.append({"stage": "wechat_collect", "status": "skipped"})
        run("scripts/parse_wechat_article.py", date)
        stages.append({"stage": "wechat_parse", "status": "ok"})
        for stage, script in [
            ("normalize", "scripts/normalize_intelligence.py"),
            ("analyze", "scripts/analyze_intelligence.py"),
        ]:
            run(script, date)
            stages.append({"stage": stage, "status": "ok"})
        run("scripts/assess_intelligence_quality.py", date)
        stages.append({"stage": "quality", "status": stage_status(date, "quality")})
        run("scripts/build_daily_intelligence_report.py", date)
        stages.append({"stage": "report", "status": stage_status(date, "report")})
        if datetime.date.fromisoformat(date).weekday() == 4:
            run("scripts/build_wechat_weekly_report.py", date)
            stages.append({"stage": "wechat_weekly_report", "status": "ok"})
        subprocess.run([sys.executable, str(ROOT / "tools/build_graph.py")], cwd=ROOT, check=True)
        stages.append({"stage": "graph", "status": "ok"})
        status = "degraded" if any(stage.get("status") in {"degraded", "skipped"} for stage in stages) else "ok"
    except subprocess.CalledProcessError as exc:
        stages.append({"stage": "failed", "status": "error", "returncode": exc.returncode})
        status = "error"
        raise
    finally:
        out_dir = ROOT / "data/outputs" / date
        out_dir.mkdir(parents=True, exist_ok=True)
        log = {
            "schema_version": 1,
            "job_id": "daily_waje_intelligence",
            "date": date,
            "status": status,
            "started_at": started_at,
            "finished_at": datetime.datetime.now().astimezone().isoformat(),
            "stages": stages,
        }
        (out_dir / "run-log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"daily pipeline completed: {date}")


if __name__ == "__main__":
    main()
