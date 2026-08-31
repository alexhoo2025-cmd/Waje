from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from tools.gemini_bridge import run_task, validate_sql


ROOT = Path(__file__).resolve().parents[1]


def test_validate_sql_blocks_writes_and_missing_date() -> None:
    config = {
        "project_id": "wajenigeria",
        "allowed_datasets": ["wajenigeria.analytics"],
        "allowed_views": [],
        "sensitive_identifiers": ["user_id", "phone"],
    }
    assert any("forbidden" in item for item in validate_sql("DELETE FROM `wajenigeria.analytics.v_daily`", config))
    assert any("SELECT *" in item for item in validate_sql("SELECT * FROM `wajenigeria.analytics.v_daily`", config))
    assert any("date" in item for item in validate_sql("SELECT COUNT(*) FROM `wajenigeria.analytics.v_daily`", config))


def test_dry_run_does_not_call_gemini() -> None:
    result = run_task(
        task="检查 H5 性能",
        task_type="h5_performance",
        config_path=ROOT / "config" / "gemini-enterprise.json",
        task_id="dry-run-test",
        dry_run=True,
    )
    assert result["status"] == "dry_run"
    assert "企业账号" in result["prompt"]


def test_enterprise_response_is_sanitized_and_receipted(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "project_id": "wajenigeria",
                "data_project_id": "wajenigeria",
                "runtime_project_id": "indigo-gecko-500503-j3",
                "location": "us-central1",
                "gemini_command": ["gemini"],
                "approval_mode": "plan",
                "output_format": "json",
                "timezone": "Africa/Lagos",
                "limits": {"timeout_seconds": 10},
                "allowed_datasets": ["wajenigeria.analytics"],
                "allowed_views": [],
                "sensitive_identifiers": ["user_id", "email"],
            }
        ),
        encoding="utf-8",
    )
    model = {
        "status": "ok",
        "auth_context": {"enterprise_account": True, "bigquery_connection": True, "workspace": "company"},
        "sql": "SELECT event_date, COUNT(DISTINCT user_id) AS users FROM `wajenigeria.analytics.v_daily` WHERE event_date BETWEEN '2026-08-01' AND '2026-08-07' GROUP BY event_date",
        "source_objects": ["wajenigeria.analytics.v_daily"],
        "data_cutoff": "2026-08-08 00:00:00 Africa/Lagos",
        "complete_day": True,
        "metrics": [{"name": "用户数", "value": 42, "definition": "聚合用户数"}],
        "summary": "聚合结果，仅包含汇总值。",
        "quality": {"sample_size": 42, "denominator": "日活用户", "missing_reason": None},
        "next_steps": [],
        "rows": [{"user_id": "should-not-persist"}],
    }
    fake = CompletedProcess(args=["gemini"], returncode=0, stdout=json.dumps(model), stderr="")
    with patch("tools.gemini_bridge.subprocess.run", return_value=fake):
        result = run_task(
            task="检查 H5 性能",
            task_type="h5_performance",
            config_path=config_path,
            task_id="sanitized-test",
            output_dir=tmp_path / "outputs",
        )
    assert result["status"] == "ok"
    result_payload = json.loads((Path(result["output_dir"]) / "result.json").read_text(encoding="utf-8"))
    assert "rows" not in result_payload
    assert "should-not-persist" not in json.dumps(result_payload)
