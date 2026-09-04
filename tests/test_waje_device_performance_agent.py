from __future__ import annotations

from datetime import date
from pathlib import Path
import json
import unittest

from agent_runtime.waje_device_performance_agent.config import (
    FALLBACK_MODEL,
    PRIMARY_MODEL,
    RequestValidationError,
    normalize_filters,
    normalize_window,
)
from agent_runtime.waje_device_performance_agent.deploy import ModelProbeError, select_deployment_model
from agent_runtime.waje_device_performance_agent.query_gateway import QueryGatewayError, build_plan


class WajeDevicePerformanceAgentTests(unittest.TestCase):
    def test_default_window_excludes_incomplete_lagos_day(self) -> None:
        window = normalize_window(None, None, today_lagos=date(2026, 9, 3))
        self.assertEqual(window.date_from.isoformat(), "2026-08-27")
        self.assertEqual(window.date_to.isoformat(), "2026-09-02")

    def test_window_rejects_today_and_over_30_days(self) -> None:
        with self.assertRaisesRegex(RequestValidationError, "incomplete_lagos_day"):
            normalize_window("2026-08-28", "2026-09-03", today_lagos=date(2026, 9, 3))
        with self.assertRaisesRegex(RequestValidationError, "window_exceeds"):
            normalize_window("2026-08-01", "2026-09-02", today_lagos=date(2026, 9, 3))

    def test_endpoint_and_package_must_match_registry(self) -> None:
        with self.assertRaisesRegex(RequestValidationError, "do_not_match"):
            normalize_filters(
                endpoint="android_main",
                app_package="com.hfhy.wajecasino.game",
            )

    def test_queries_only_reference_safe_views_and_have_date_bounds(self) -> None:
        filters = normalize_filters(endpoint="android_main", app_package="com.hfhy.waje.special")
        plan = build_plan("data_health", filters)
        self.assertIn("agent_analytics.vw_firebase_endpoint_coverage_daily_safe", plan.sql)
        self.assertNotIn("waje_ng_firebase_", plan.sql)
        self.assertIn("metric_date_lagos BETWEEN @date_from AND @date_to", plan.sql)
        self.assertNotIn("SELECT *", plan.sql)
        self.assertIn("LIMIT 100", plan.sql)

    def test_country_filter_is_bound_to_country_rank_dimension_not_dynamic_sql(self) -> None:
        filters = normalize_filters(
            endpoint="android_main",
            app_package="com.hfhy.waje.special",
            country="NG",
        )
        plan = build_plan("native_performance", filters)
        self.assertIn("analysis_dimension = 'country'", plan.sql)
        self.assertIn("analysis_value = @country", plan.sql)
        self.assertEqual(plan.parameters["country"], "NG")
        self.assertNotIn("country = @country", plan.sql)

    def test_unavailable_filter_is_rejected_instead_of_ignored(self) -> None:
        filters = normalize_filters(country="NG")
        with self.assertRaisesRegex(QueryGatewayError, "filter_not_available_for_tool:country"):
            build_plan("data_health", filters)

    def test_only_explicit_model_unavailability_allows_fallback(self) -> None:
        attempted: list[str] = []

        def unavailable_primary(model: str) -> None:
            attempted.append(model)
            if model == PRIMARY_MODEL:
                raise ModelProbeError(f"model_unavailable:{model}")

        selected, reason = select_deployment_model(unavailable_primary)
        self.assertEqual(selected, FALLBACK_MODEL)
        self.assertEqual(reason, f"model_unavailable:{PRIMARY_MODEL}")
        self.assertEqual(attempted, [PRIMARY_MODEL, FALLBACK_MODEL])

        def permission_failure(_: str) -> None:
            raise ModelProbeError("non_retryable_model_probe_failure:permission")

        with self.assertRaisesRegex(ModelProbeError, "non_retryable"):
            select_deployment_model(permission_failure)

    def test_public_web_research_is_enabled_but_separated_from_internal_facts(self) -> None:
        config = json.loads(Path("config/gemini-enterprise.json").read_text(encoding="utf-8"))
        self.assertEqual(config["agent_platform"]["model"], PRIMARY_MODEL)
        self.assertEqual(config["agent_platform"]["model_fallback"], [FALLBACK_MODEL])
        self.assertEqual(config["agent_platform"]["agent_runtime_region_preference"], "us-west1")
        web_tools = config["agent_platform"]["web_tools"]
        self.assertTrue(web_tools["google_search"])
        self.assertTrue(web_tools["url_context"])
        instruction = Path(
            "agent_runtime/waje_device_performance_agent/system_instruction.md"
        ).read_text(encoding="utf-8")
        self.assertIn("公开网络搜索与 URL Context", instruction)
        self.assertIn("不能直接表述为 Waje 内部运营事实", instruction)
