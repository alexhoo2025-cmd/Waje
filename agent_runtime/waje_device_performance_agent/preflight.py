"""Non-mutating preflight for the Waje device-performance Agent Runtime app."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import DATA_LOCATION, DATA_PROJECT_ID, SAFE_VIEWS, normalize_filters
from .query_gateway import build_plan


ROOT = Path(__file__).resolve().parents[2]


def _run(command: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    return result.returncode, (result.stdout or result.stderr or "").strip()


def local_contract_status() -> dict[str, Any]:
    filters = normalize_filters(endpoint="android_main", app_package="com.hfhy.waje.special")
    plan = build_plan("native_performance", filters)
    return {
        "status": "ok",
        "project": DATA_PROJECT_ID,
        "data_location": DATA_LOCATION,
        "safe_views": list(SAFE_VIEWS.values()),
        "tool_query_references_only_safe_view": plan.view_name in plan.sql,
        "tool_query_has_date_predicate": "metric_date_lagos BETWEEN @date_from AND @date_to" in plan.sql,
        "tool_query_has_no_select_star": "SELECT *" not in plan.sql,
    }


def cloud_auth_status() -> dict[str, str]:
    gcloud = shutil.which("gcloud")
    if not gcloud:
        return {"status": "blocked_tooling", "reason": "gcloud_not_found"}
    code, output = _run([gcloud, "auth", "application-default", "print-access-token"])
    # Never return the token or the raw gcloud output.
    if code == 0:
        return {"status": "ok"}
    lowered = output.lower()
    if "reauthentication" in lowered or "login" in lowered or "credential" in lowered:
        return {"status": "blocked_authentication", "reason": "application_default_credentials_need_interactive_login"}
    return {"status": "blocked", "reason": "application_default_credentials_unavailable"}


def main() -> int:
    payload = {
        "local_contract": local_contract_status(),
        "cloud_auth": cloud_auth_status(),
        "required_external_gates": [
            "Agent Studio creator account has roles/aiplatform.user or roles/aiplatform.expressUser on wajenigeria",
            "aiplatform.googleapis.com, bigquery.googleapis.com and serviceusage.googleapis.com are enabled",
            "agent_analytics safe views have been created and validated in europe-west4",
            "Agent Runtime deployment staging bucket exists and uses least-privilege access",
            "deployed Agent Identity has BigQuery Job User plus Data/Metadata Viewer only on agent_analytics",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
