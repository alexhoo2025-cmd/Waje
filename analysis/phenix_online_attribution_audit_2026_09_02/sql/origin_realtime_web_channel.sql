-- Origin realtime H5 channel and event coverage for complete days.
-- No user identifiers, full URLs, or raw payload values are returned.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
)
SELECT
  target_day,
  COALESCE(NULLIF(traffic_source_type, ''), '(blank)') AS traffic_source_type,
  COALESCE(NULLIF(utm_source, ''), '(blank)') AS utm_source,
  COALESCE(NULLIF(utm_medium, ''), '(blank)') AS utm_medium,
  COALESCE(NULLIF(url_host, ''), '(blank)') AS url_host,
  COALESCE(NULLIF(event_type, ''), '(blank)') AS event_type,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count,
  COUNTIF(event_id IS NULL OR event_id = '') AS missing_event_id_count,
  COUNTIF(session_id IS NULL OR session_id = '') AS missing_session_id_count,
  COUNTIF(utm_source IS NOT NULL AND utm_source != '') AS utm_source_present_count,
  COUNTIF(utm_medium IS NOT NULL AND utm_medium != '') AS utm_medium_present_count,
  COUNTIF(utm_campaign IS NOT NULL AND utm_campaign != '') AS utm_campaign_present_count,
  COUNTIF(REGEXP_CONTAINS(
    LOWER(CONCAT(
      COALESCE(traffic_source_type, ''), '|',
      COALESCE(utm_source, ''), '|',
      COALESCE(utm_medium, ''), '|',
      COALESCE(utm_campaign, ''), '|',
      COALESCE(url_host, '')
    )),
    r'(wajeh5phx|waje5phx|phenix)'
  )) AS phx_marker_count
FROM `wajenigeria.origin_hfyl.realtime_event_web`
CROSS JOIN date_bounds
WHERE target_day BETWEEN event_date AND DATE '2026-09-01'
GROUP BY target_day, traffic_source_type, utm_source, utm_medium, url_host, event_type
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY target_day, event_count DESC, url_host, event_type
LIMIT 3000
