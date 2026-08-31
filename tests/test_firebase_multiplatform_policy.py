from __future__ import annotations

from pathlib import Path

from tools.firebase_multiplatform_policy import validate_sql


ALLOWLIST = [
    "wajenigeria.waje_ng_firebase_android",
    "wajenigeria.waje_ng_firebase_android_performance",
    "wajenigeria.waje_ng_firebase_android_sessions",
    "wajenigeria.waje_ng_firebase_android_crashlytics",
    "wajenigeria.waje_ng_firebase_ios",
    "wajenigeria.waje_ng_firebase_ios_performance",
    "wajenigeria.waje_ng_firebase_h5",
]


def test_allows_bounded_aggregate_and_internal_session_key() -> None:
    sql = """
    SELECT DATE(event_timestamp, 'Africa/Lagos') AS metric_date_lagos,
           COUNT(DISTINCT session_id) AS distinct_sessions
    FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID`
    WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
    GROUP BY metric_date_lagos
    LIMIT 3000
    """
    assert validate_sql(sql, allowed_datasets=ALLOWLIST) == []


def test_blocks_writes_sensitive_output_unbounded_and_wrong_project() -> None:
    bad = {
        "write": "INSERT INTO `wajenigeria.waje_ng_firebase_android.events_20260824` SELECT 1",
        "sensitive": "SELECT user_id FROM `wajenigeria.waje_ng_firebase_android.events_*` WHERE _TABLE_SUFFIX='20260824' LIMIT 10",
        "unbounded": "SELECT event_name FROM `wajenigeria.waje_ng_firebase_android.events_*` WHERE _TABLE_SUFFIX='20260824'",
        "wrong_project": "SELECT event_name FROM `other-project.dataset.events_*` WHERE _TABLE_SUFFIX='20260824' LIMIT 10",
    }
    errors = {key: validate_sql(value, allowed_datasets=ALLOWLIST) for key, value in bad.items()}
    assert any(item.startswith("forbidden_operation:insert") for item in errors["write"])
    assert any(item.startswith("direct_sensitive_identifier_projection:user_id") for item in errors["sensitive"])
    assert "limit_required" in errors["unbounded"]
    assert "source_outside_wajenigeria" in errors["wrong_project"]


def test_metadata_queries_can_use_region_information_schema_without_date() -> None:
    sql = """
    SELECT table_schema, table_name, table_type
    FROM `wajenigeria`.region-europe-west4.INFORMATION_SCHEMA.TABLES
    WHERE STARTS_WITH(table_schema, 'waje_ng_firebase_')
    LIMIT 3000
    """
    assert validate_sql(sql, allowed_datasets=ALLOWLIST) == []
