#!/usr/bin/env python3
"""Run the dedicated Google Play review daily or weekly pipeline."""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(command: list[str], allow_returncodes: set[int] | None = None) -> int:
    result = subprocess.run(command, cwd=ROOT)
    allowed = allow_returncodes or {0}
    if result.returncode not in allowed:
        raise subprocess.CalledProcessError(result.returncode, command)
    return result.returncode


def latest_manifest(date: str) -> Path | None:
    paths = sorted((ROOT / "data/raw/play_reviews" / date).glob("manifest-*.json"))
    return paths[-1] if paths else None


def read_json(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=dt.datetime.now().astimezone().date().isoformat())
    parser.add_argument("--period", choices=("daily", "weekly"), default="daily")
    parser.add_argument("--skip-collect", action="store_true")
    parser.add_argument("--skip-graph", action="store_true")
    args = parser.parse_args()
    if args.period == "weekly":
        args.skip_collect = True

    lock_path = ROOT / "data/processed/play_reviews/.pipeline.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    started_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    stages: list[dict] = []
    status = "error"
    with lock_path.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Play review pipeline is already running", file=sys.stderr)
            return 3
        try:
            if not args.skip_collect:
                seed = run([PYTHON, "scripts/play_review_index.py", "seed-existing"])
                stages.append({"stage": "index_seed", "status": "ok", "returncode": seed})
                collect_rc = run(["node", "scripts/collect_play_reviews.mjs", "--date", args.date, "--mode", "incremental", "--min-new-reviews", "200", "--backfill-unseen"], {0, 2})
                manifest_path = latest_manifest(args.date)
                manifest = read_json(manifest_path)
                stages.append({"stage": "collect", "status": manifest.get("status", "error"), "returncode": collect_rc, "manifest": str(manifest_path.relative_to(ROOT)) if manifest_path else ""})
                if manifest.get("raw_file"):
                    normalize_rc = run([PYTHON, "scripts/normalize_play_reviews.py", "--date", args.date, "--manifest", str(manifest_path)])
                    stages.append({"stage": "normalize", "status": "ok", "returncode": normalize_rc})
                    records_path = ROOT / "data/processed/play_reviews" / args.date / "reviews.jsonl"
                    index_rc = run([PYTHON, "scripts/play_review_index.py", "upsert", "--records", str(records_path), "--manifest", str(manifest_path)])
                    stages.append({"stage": "index_upsert", "status": "ok", "returncode": index_rc})
                    analyze_rc = run([PYTHON, "scripts/analyze_play_reviews.py", "--date", args.date])
                    stages.append({"stage": "analyze", "status": "ok", "returncode": analyze_rc})
                else:
                    stages.append({"stage": "normalize", "status": "skipped"})
                    stages.append({"stage": "index_upsert", "status": "skipped"})
                    stages.append({"stage": "analyze", "status": "skipped"})
                quality_rc = run([PYTHON, "scripts/assess_play_reviews_quality.py", "--date", args.date])
                stages.append({"stage": "quality", "status": read_json(ROOT / "data/outputs/play_reviews" / args.date / "quality.json").get("status", "degraded"), "returncode": quality_rc})
                analysis_path = ROOT / "data/outputs/play_reviews" / args.date / "analysis.json"
                if analysis_path.exists():
                    knowledge_rc = run([PYTHON, "scripts/build_play_reviews_knowledge.py", "--date", args.date])
                    stages.append({"stage": "knowledge", "status": "ok", "returncode": knowledge_rc})
                else:
                    stages.append({"stage": "knowledge", "status": "skipped"})
            else:
                stages.append({"stage": "collect", "status": "skipped"})
            report_rc = run([PYTHON, "scripts/build_play_reviews_report.py", "--date", args.date, "--period", args.period])
            report_dir = ROOT / "data/outputs/play_reviews" / ("weekly/" if args.period == "weekly" else "") / args.date
            stages.append({"stage": "report", "status": read_json(report_dir / "report-receipt.json").get("status", "degraded"), "returncode": report_rc})
            if not args.skip_graph:
                graph_rc = run([PYTHON, "tools/build_graph.py"])
                stages.append({"stage": "graph", "status": "ok", "returncode": graph_rc})
            status = "degraded" if any(stage.get("status") in {"degraded", "shortfall", "blocked"} for stage in stages) else "ok"
        except subprocess.CalledProcessError as exc:
            stages.append({"stage": "failed", "status": "error", "returncode": exc.returncode, "command": exc.cmd})
            status = "error"
            raise
        finally:
            output_dir = ROOT / "data/outputs/play_reviews" / args.date
            output_dir.mkdir(parents=True, exist_ok=True)
            log = {
                "schema_version": 1,
                "job_id": "google_play_reviews_daily" if args.period == "daily" else "google_play_reviews_weekly",
                "date": args.date,
                "period": args.period,
                "status": status,
                "started_at": started_at,
                "finished_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "stages": stages,
            }
            (output_dir / "run-log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Play review pipeline completed: {args.period} {args.date} ({status})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
