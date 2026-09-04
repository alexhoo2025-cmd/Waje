"""Static, safe configuration for the Waje device-performance Agent Runtime app.

This module is deliberately independent from environment credentials. It holds
only public project identifiers, approved aggregate-view names, fixed business
dimensions and resource limits. Credentials, access tokens and service-account
key files are never read here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Final
from zoneinfo import ZoneInfo


DATA_PROJECT_ID: Final = "wajenigeria"
DATA_LOCATION: Final = "europe-west4"
MODEL_LOCATION: Final = "global"
TIMEZONE: Final = "Africa/Lagos"
PRIMARY_MODEL: Final = "gemini-3.1-pro-preview"
FALLBACK_MODEL: Final = "gemini-2.5-pro"
THINKING_LEVEL: Final = "medium"
DEFAULT_WINDOW_DAYS: Final = 7
MAX_WINDOW_DAYS: Final = 30
MAX_QUERY_BYTES: Final = 1 * 1024 * 1024 * 1024
MAX_RUN_BYTES: Final = 5 * 1024 * 1024 * 1024
MAX_RESULT_ROWS: Final = 100
MINIMUM_GROUP_SIZE: Final = 10
METRIC_DEFINITION_VERSION: Final = "waje_device_performance_agent_v1"

ENDPOINTS: Final[dict[str, dict[str, str]]] = {
    "android_main": {
        "platform": "Android",
        "app_package": "com.hfhy.waje.special",
    },
    "android_transsion_old": {
        "platform": "Android",
        "app_package": "com.hfhy.wajecasino.palmgame",
    },
    "android_transsion_new": {
        "platform": "Android",
        "app_package": "com.hfhy.wajecasino.game",
    },
    "ios_existing": {
        "platform": "iOS",
        "app_package": "com.wajegame.wajegame",
    },
    "h5": {
        "platform": "H5",
        "app_package": "waje_ng_firebase_h5",
    },
}

SAFE_VIEWS: Final[dict[str, str]] = {
    "data_health": "wajenigeria.agent_analytics.vw_firebase_endpoint_coverage_daily_safe",
    "event_session": "wajenigeria.agent_analytics.vw_firebase_event_session_daily_safe",
    "native_performance": "wajenigeria.agent_analytics.vw_firebase_native_performance_daily_safe",
    "stability": "wajenigeria.agent_analytics.vw_firebase_stability_daily_safe",
    "h5_observability": "wajenigeria.agent_analytics.vw_firebase_h5_behavior_daily_safe",
}

RANK_DIMENSIONS: Final = {
    "device_name_bucket",
    "os_version",
    "country",
    "carrier_bucket",
    "network_type",
}

QUALITY_STATES: Final = {
    "certified",
    "provisional",
    "immature",
    "delayed",
    "data_gap",
    "blocked",
}


class RequestValidationError(ValueError):
    """A tool request violates a fixed Agent Runtime input contract."""


@dataclass(frozen=True)
class DateWindow:
    """Inclusive Lagos-business-date filter after enforcing complete-day rules."""

    date_from: date
    date_to: date

    @property
    def days(self) -> int:
        return (self.date_to - self.date_from).days + 1


@dataclass(frozen=True)
class QueryFilters:
    """Whitelisted filter values accepted by every aggregate query tool."""

    window: DateWindow
    endpoint: str | None = None
    app_package: str | None = None
    app_version: str | None = None
    country: str | None = None
    rank_dimension: str | None = None
    top_n: int = 5


def _parse_iso_date(value: str | None, *, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError(f"{field_name}_must_use_yyyy_mm_dd") from exc


def default_complete_window(*, today_lagos: date | None = None) -> DateWindow:
    """Return the latest seven completed Lagos natural days, excluding today."""

    if today_lagos is None:
        from datetime import datetime

        today_lagos = datetime.now(ZoneInfo(TIMEZONE)).date()
    end = today_lagos - timedelta(days=1)
    return DateWindow(date_from=end - timedelta(days=DEFAULT_WINDOW_DAYS - 1), date_to=end)


def normalize_window(
    date_from: str | None,
    date_to: str | None,
    *,
    today_lagos: date | None = None,
) -> DateWindow:
    """Apply defaults and prevent requests for incomplete or overlong windows."""

    default = default_complete_window(today_lagos=today_lagos)
    start = _parse_iso_date(date_from, field_name="date_from") or default.date_from
    end = _parse_iso_date(date_to, field_name="date_to") or default.date_to
    if start > end:
        raise RequestValidationError("date_from_must_not_exceed_date_to")
    if end > default.date_to:
        raise RequestValidationError("incomplete_lagos_day_not_allowed")
    window = DateWindow(date_from=start, date_to=end)
    if window.days > MAX_WINDOW_DAYS:
        raise RequestValidationError("window_exceeds_30_complete_days")
    return window


def _bounded_text(value: str | None, *, field_name: str, max_length: int = 128) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    if not normalized or len(normalized) > max_length:
        raise RequestValidationError(f"invalid_{field_name}")
    return normalized


def normalize_filters(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    endpoint: str | None = None,
    app_package: str | None = None,
    app_version: str | None = None,
    country: str | None = None,
    rank_dimension: str | None = None,
    top_n: int | None = None,
) -> QueryFilters:
    """Return one fully bounded, non-sensitive query filter object."""

    normalized_endpoint = _bounded_text(endpoint, field_name="endpoint", max_length=64)
    normalized_package = _bounded_text(app_package, field_name="app_package")
    if normalized_endpoint and normalized_endpoint not in ENDPOINTS:
        raise RequestValidationError("endpoint_not_in_waje_registry")
    if normalized_package and normalized_package not in {item["app_package"] for item in ENDPOINTS.values()}:
        raise RequestValidationError("app_package_not_in_waje_registry")
    if normalized_endpoint and normalized_package:
        expected = ENDPOINTS[normalized_endpoint]["app_package"]
        if normalized_package != expected:
            raise RequestValidationError("endpoint_and_app_package_do_not_match")

    normalized_dimension = _bounded_text(rank_dimension, field_name="rank_dimension", max_length=64)
    if normalized_dimension and normalized_dimension not in RANK_DIMENSIONS:
        raise RequestValidationError("rank_dimension_not_allowed")
    try:
        bounded_top_n = 5 if top_n is None else int(top_n)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError("top_n_must_be_an_integer") from exc
    if bounded_top_n < 1 or bounded_top_n > 5:
        raise RequestValidationError("top_n_must_be_between_1_and_5")

    return QueryFilters(
        window=normalize_window(date_from, date_to),
        endpoint=normalized_endpoint,
        app_package=normalized_package,
        app_version=_bounded_text(app_version, field_name="app_version"),
        country=_bounded_text(country, field_name="country", max_length=64),
        rank_dimension=normalized_dimension,
        top_n=bounded_top_n,
    )
