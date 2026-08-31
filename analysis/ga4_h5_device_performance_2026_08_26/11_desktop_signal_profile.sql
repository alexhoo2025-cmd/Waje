WITH base AS (
  SELECT
    COALESCE(geo.country, '(not set)') AS country,
    COALESCE(device.web_info.browser, device.browser, '(not set)') AS browser,
    event_name
  FROM `waje-analytics-readonly.analytics_504208609.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260824'
    AND device.category = 'desktop'
)
SELECT
  country,
  browser,
  COUNT(*) AS event_count,
  COUNTIF(event_name = 'page_view') AS page_views,
  COUNTIF(event_name = 'register') AS register_events,
  COUNTIF(event_name = 'recharge') AS recharge_events,
  COUNTIF(event_name = 'withdraw') AS withdraw_events
FROM base
GROUP BY country, browser
HAVING event_count >= 50
ORDER BY recharge_events + register_events + withdraw_events DESC, event_count DESC
LIMIT 20;
