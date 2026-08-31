-- H5 GA4 -> BigQuery 设备与性能专题单日审计
-- Source: waje-analytics-readonly.analytics_504208609.events_20260820
-- Privacy: aggregate-only. Do not select user_id, user_pseudo_id, cookie values,
-- raw event rows, or complete page_location/page_referrer values.

WITH src AS (
  SELECT
    event_name,
    event_timestamp,
    device.category AS device_category,
    device.operating_system AS operating_system,
    device.web_info.browser AS browser,
    geo.country AS country,
    traffic_source.source AS source_name,
    traffic_source.medium AS medium_name,
    (SELECT ANY_VALUE(value.string_value) FROM UNNEST(event_params)
      WHERE key = 'page_location') AS page_location,
    (SELECT ANY_VALUE(value.string_value) FROM UNNEST(event_params)
      WHERE key = 'page_referrer') AS page_referrer,
    (SELECT COUNT(*) FROM UNNEST(event_params)
      WHERE key = 'ga_session_id') > 0 AS has_session_id,
    (SELECT COUNT(*) FROM UNNEST(event_params)
      WHERE key = 'page_title') > 0 AS has_page_title,
    (SELECT COUNT(*) FROM UNNEST(event_params)
      WHERE key = 'engagement_time_msec') > 0 AS has_engagement_time,
    (SELECT COUNT(*) FROM UNNEST(event_params)
      WHERE key = 'value') > 0 AS has_value,
    event_params
  FROM `waje-analytics-readonly.analytics_504208609.events_20260820`
),
tot AS (
  SELECT COUNT(*) AS total_events,
         MIN(event_timestamp) AS min_ts,
         MAX(event_timestamp) AS max_ts
  FROM src
),
event_mix AS (
  SELECT event_name AS key, COUNT(*) AS n
  FROM src
  GROUP BY event_name
),
device_mix AS (
  SELECT COALESCE(NULLIF(device_category, ''), '(not set)') AS key, COUNT(*) AS n
  FROM src GROUP BY key
),
os_mix AS (
  SELECT COALESCE(NULLIF(operating_system, ''), '(not set)') AS key, COUNT(*) AS n
  FROM src GROUP BY key
),
browser_mix AS (
  SELECT COALESCE(NULLIF(browser, ''), '(not set)') AS key, COUNT(*) AS n
  FROM src GROUP BY key
),
country_mix AS (
  SELECT COALESCE(NULLIF(country, ''), '(not set)') AS key, COUNT(*) AS n
  FROM src GROUP BY key
),
page_host_mix AS (
  SELECT COALESCE(
    NULLIF(REGEXP_EXTRACT(page_location, r'^(?:https?://)?([^/]+)'), ''),
    '(not set)') AS key,
    COUNT(*) AS n
  FROM src GROUP BY key
),
source_mix AS (
  SELECT CONCAT(COALESCE(NULLIF(source_name, ''), '(not set)'), ' / ',
                COALESCE(NULLIF(medium_name, ''), '(not set)')) AS key,
         COUNT(*) AS n
  FROM src GROUP BY key
),
param_mix AS (
  SELECT ep.key AS key, COUNT(*) AS n
  FROM src, UNNEST(event_params) ep
  GROUP BY ep.key
),
quality AS (
  SELECT
    COUNTIF(device_category IS NOT NULL AND device_category <> '') AS device_present,
    COUNTIF(operating_system IS NOT NULL AND operating_system <> '') AS os_present,
    COUNTIF(browser IS NOT NULL AND browser <> '') AS browser_present,
    COUNTIF(page_location IS NOT NULL AND page_location <> '') AS page_location_present,
    COUNTIF(page_referrer IS NOT NULL AND page_referrer <> '') AS page_referrer_present,
    COUNTIF(has_session_id) AS session_id_present,
    COUNTIF(has_page_title) AS page_title_present,
    COUNTIF(has_engagement_time) AS engagement_time_present,
    COUNTIF(has_value) AS value_present
  FROM src
),
behavior_names AS (
  SELECT name FROM UNNEST([
    'page_view', 'scroll', 'user_engagement', 'session_start', 'first_visit',
    'form_start', 'register', 'rechargeAndWithdrawTotalTimes', 'recharge',
    'rechargeDollar', 'withdraw', 'firstCharge', 'rechargeFix'
  ]) AS name
),
performance_names AS (
  SELECT name FROM UNNEST([
    'web_vitals', 'lcp', 'inp', 'cls', 'fcp', 'ttfb', 'page_load',
    'js_error', 'frontend_error', 'network_latency', 'performance'
  ]) AS name
),
key_behavior AS (
  SELECT b.name AS key, COALESCE(e.n, 0) AS n
  FROM behavior_names b LEFT JOIN event_mix e ON b.name = e.key
),
performance_signal AS (
  SELECT p.name AS key, COALESCE(e.n, 0) AS n
  FROM performance_names p LEFT JOIN event_mix e ON p.name = e.key
)
SELECT 'table_total' AS section, 'total_events' AS key,
       t.total_events AS metric_num, t.total_events AS denominator,
       CAST(NULL AS STRING) AS metric_text, 1.0 AS metric_pct,
       'certified' AS status
FROM tot t
UNION ALL SELECT 'table_total', 'event_timestamp_min', NULL, NULL,
  FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', TIMESTAMP_MICROS(t.min_ts)), NULL,
  'certified' FROM tot t
UNION ALL SELECT 'table_total', 'event_timestamp_max', NULL, NULL,
  FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', TIMESTAMP_MICROS(t.max_ts)), NULL,
  'certified' FROM tot t
UNION ALL SELECT 'device_mix', key, n, t.total_events, NULL,
  SAFE_DIVIDE(n, t.total_events), 'provisional'
  FROM device_mix CROSS JOIN tot t
UNION ALL SELECT 'os_mix', key, n, t.total_events, NULL,
  SAFE_DIVIDE(n, t.total_events), 'provisional'
  FROM os_mix CROSS JOIN tot t
UNION ALL SELECT 'browser_mix', key, n, t.total_events, NULL,
  SAFE_DIVIDE(n, t.total_events), 'provisional'
  FROM browser_mix CROSS JOIN tot t
UNION ALL SELECT 'country_mix', key, n, t.total_events, NULL,
  SAFE_DIVIDE(n, t.total_events), 'provisional'
  FROM country_mix CROSS JOIN tot t
UNION ALL SELECT 'page_host_mix', key, n, t.total_events, NULL,
  SAFE_DIVIDE(n, t.total_events), 'provisional'
  FROM page_host_mix CROSS JOIN tot t
UNION ALL SELECT 'source_medium_mix', key, n, t.total_events, NULL,
  SAFE_DIVIDE(n, t.total_events), 'provisional'
  FROM source_mix CROSS JOIN tot t
UNION ALL SELECT 'event_mix', key, n, t.total_events, NULL,
  SAFE_DIVIDE(n, t.total_events), 'provisional'
  FROM event_mix CROSS JOIN tot t
UNION ALL SELECT 'key_behavior', key, n, t.total_events, NULL,
  SAFE_DIVIDE(n, t.total_events), 'provisional'
  FROM key_behavior CROSS JOIN tot t
UNION ALL SELECT 'performance_signal', key, n, t.total_events,
  IF(n = 0, 'not_observed', 'observed'), SAFE_DIVIDE(n, t.total_events),
  IF(n = 0, 'data_gap', 'provisional')
  FROM performance_signal CROSS JOIN tot t
UNION ALL SELECT 'parameter_occurrences', key, n, NULL, NULL, NULL,
  'provisional' FROM param_mix
UNION ALL SELECT 'quality_presence', 'device_category', q.device_present,
  t.total_events, NULL, SAFE_DIVIDE(q.device_present, t.total_events),
  IF(q.device_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
UNION ALL SELECT 'quality_presence', 'operating_system', q.os_present,
  t.total_events, NULL, SAFE_DIVIDE(q.os_present, t.total_events),
  IF(q.os_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
UNION ALL SELECT 'quality_presence', 'browser', q.browser_present,
  t.total_events, NULL, SAFE_DIVIDE(q.browser_present, t.total_events),
  IF(q.browser_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
UNION ALL SELECT 'quality_presence', 'page_location', q.page_location_present,
  t.total_events, NULL, SAFE_DIVIDE(q.page_location_present, t.total_events),
  IF(q.page_location_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
UNION ALL SELECT 'quality_presence', 'page_referrer', q.page_referrer_present,
  t.total_events, NULL, SAFE_DIVIDE(q.page_referrer_present, t.total_events),
  IF(q.page_referrer_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
UNION ALL SELECT 'quality_presence', 'ga_session_id', q.session_id_present,
  t.total_events, NULL, SAFE_DIVIDE(q.session_id_present, t.total_events),
  IF(q.session_id_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
UNION ALL SELECT 'quality_presence', 'page_title', q.page_title_present,
  t.total_events, NULL, SAFE_DIVIDE(q.page_title_present, t.total_events),
  IF(q.page_title_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
UNION ALL SELECT 'quality_presence', 'engagement_time_msec', q.engagement_time_present,
  t.total_events, NULL, SAFE_DIVIDE(q.engagement_time_present, t.total_events),
  IF(q.engagement_time_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
UNION ALL SELECT 'quality_presence', 'value', q.value_present,
  t.total_events, NULL, SAFE_DIVIDE(q.value_present, t.total_events),
  IF(q.value_present = t.total_events, 'certified', 'provisional')
  FROM quality q CROSS JOIN tot t
ORDER BY section, metric_num DESC, key;

-- Device category x behavior event counts. Still aggregate-only and not a funnel
-- conversion rate: event counts are not users, sessions, orders, or success rates.
SELECT
  COALESCE(NULLIF(device.category, ''), '(not set)') AS device_category,
  event_name,
  COUNT(*) AS event_count
FROM `waje-analytics-readonly.analytics_504208609.events_20260820`
WHERE event_name IN (
  'page_view', 'scroll', 'user_engagement', 'session_start', 'form_start',
  'register', 'rechargeAndWithdrawTotalTimes', 'recharge', 'rechargeDollar',
  'withdraw', 'firstCharge'
)
GROUP BY device_category, event_name
ORDER BY device_category, event_count DESC;
