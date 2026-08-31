WITH base AS (
  SELECT
    COALESCE(device.operating_system, '(not set)') AS operating_system,
    event_name
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
    AND device.category = 'mobile'
),
aggregated AS (
  SELECT
    operating_system,
    COUNTIF(event_name = 'page_view') AS page_views,
    COUNTIF(event_name = 'session_start') AS session_starts,
    COUNTIF(event_name = 'form_start') AS form_starts,
    COUNTIF(event_name = 'register') AS register_events,
    COUNTIF(event_name = 'recharge') AS recharge_events,
    COUNTIF(event_name = 'withdraw') AS withdraw_events
  FROM base
  GROUP BY operating_system
)
SELECT
  operating_system,
  page_views,
  session_starts,
  form_starts,
  register_events,
  recharge_events,
  withdraw_events,
  ROUND(SAFE_DIVIDE(form_starts, page_views) * 1000, 2) AS form_starts_per_1k_page_views,
  ROUND(SAFE_DIVIDE(register_events, page_views) * 1000, 2) AS register_events_per_1k_page_views,
  ROUND(SAFE_DIVIDE(recharge_events, page_views) * 1000, 2) AS recharge_events_per_1k_page_views,
  ROUND(SAFE_DIVIDE(withdraw_events, page_views) * 1000, 2) AS withdraw_events_per_1k_page_views
FROM aggregated
WHERE operating_system IN ('Android', 'iOS')
ORDER BY page_views DESC;
