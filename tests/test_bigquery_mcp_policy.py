from __future__ import annotations

from pathlib import Path

from tools.bigquery_mcp_policy import build_preflight, validate_dry_run_bytes, validate_query


VIEW = "wajenigeria.agent_analytics.vw_h5_performance_daily_safe"
ROOT = Path(__file__).resolve().parents[1]


def policy_fixture() -> dict:
    return {
        "project_id": "wajenigeria",
        "policy_mode": "fail_closed",
        "remote_mcp": {
            "endpoint": "https://bigquery.googleapis.com/mcp",
            "trusted": True,
            "allowed_tools": ["execute_sql_readonly"],
            "denied_tools": ["execute_sql"],
        },
        "active_allowed_views": [VIEW],
        "candidate_views": [],
        "required_external_actions": [],
        "limits": {"max_bytes_per_query": 100, "max_bytes_per_audit": 200, "max_rows": 3000},
        "sql_policy": {
            "allowed_statement_starts": ["select", "with"],
            "forbidden_operations": ["insert", "update", "delete", "create", "drop", "export", "call"],
            "require_date_predicate": True,
            "date_predicate_fields": ["event_date", "cohort_date", "dt", "_partitiondate"],
            "forbid_select_star": True,
            "require_limit": True,
            "forbidden_identifiers": ["user_id", "phone", "order_id", "token"],
        },
    }


def allowed_sql() -> str:
    return """SELECT event_date, page_id, SUM(sample_size) AS sample_size
FROM `wajenigeria.agent_analytics.vw_h5_performance_daily_safe`
WHERE event_date BETWEEN @start_date AND @end_date
GROUP BY event_date, page_id
LIMIT 3000"""


def test_allows_authorized_bounded_query() -> None:
    assert validate_query(allowed_sql(), policy_fixture()) == []


def test_blocks_writes_and_unbounded_or_sensitive_queries() -> None:
    policy = policy_fixture()
    assert "forbidden_operation:insert" in validate_query("INSERT INTO `wajenigeria.agent_analytics.vw_h5_performance_daily_safe` SELECT 1", policy)
    assert "select_star_not_allowed" in validate_query("SELECT * FROM `wajenigeria.agent_analytics.vw_h5_performance_daily_safe` WHERE event_date = @start_date LIMIT 10", policy)
    assert "date_or_partition_predicate_required" in validate_query("SELECT page_id FROM `wajenigeria.agent_analytics.vw_h5_performance_daily_safe` LIMIT 10", policy)
    assert "direct_sensitive_identifier_projection" in validate_query("SELECT user_id FROM `wajenigeria.agent_analytics.vw_h5_performance_daily_safe` WHERE event_date = @start_date LIMIT 10", policy)
    assert "source_outside_active_authorized_views" in validate_query("SELECT event_date FROM `wajenigeria.raw.events` WHERE event_date = @start_date LIMIT 10", policy)


def test_blocks_untrusted_or_unactivated_policy() -> None:
    policy = policy_fixture()
    policy["remote_mcp"]["trusted"] = False
    policy["active_allowed_views"] = []
    errors = validate_query(allowed_sql(), policy)
    assert "remote_mcp_not_trusted" in errors
    assert "no_active_authorized_views" in errors
    assert build_preflight(policy, "blocked_authentication")["status"] == "blocked_external_prerequisites"


def test_dry_run_budgets_are_fail_closed() -> None:
    policy = policy_fixture()
    assert validate_dry_run_bytes(99, policy) == []
    assert validate_dry_run_bytes(101, policy) == ["query_bytes_exceed_policy"]
    assert validate_dry_run_bytes(80, policy, cumulative_bytes=150) == ["audit_bytes_exceed_policy"]


def test_four_pilot_sql_templates_pass_when_views_are_activated() -> None:
    policy = policy_fixture()
    policy["active_allowed_views"] = [
        "wajenigeria.agent_analytics.vw_kyc_daily_safe",
        "wajenigeria.agent_analytics.vw_game_rtp_daily_safe",
        "wajenigeria.agent_analytics.vw_lifecycle_payer_daily_safe",
        VIEW,
    ]
    template_dir = ROOT / "analysis" / "bigquery_mcp_pilot_2026_08_27" / "sql_templates"
    for template in sorted(template_dir.glob("*.sql")):
        assert validate_query(template.read_text(encoding="utf-8"), policy) == [], template.name
