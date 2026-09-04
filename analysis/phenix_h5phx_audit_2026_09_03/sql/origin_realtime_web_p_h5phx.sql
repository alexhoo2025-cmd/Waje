-- Exact p=h5phx marker audit in Origin realtime H5 events.
-- URL and parameter fields are searched but never returned.
WITH date_bounds AS (
  SELECT DATE '2026-08-27' AS event_date
), base AS (
  SELECT
    target_day,
    event_type,
    user_id,
    event_id,
    session_id,
    utm_source,
    utm_medium,
    utm_campaign,
    REGEXP_CONTAINS(
      LOWER(CONCAT(
        COALESCE(url, ''), '|', COALESCE(element_target_url, ''), '|', COALESCE(url_path, ''), '|',
        COALESCE(path_name, ''), '|', COALESCE(referrer, ''), '|', COALESCE(latest_referrer, ''), '|',
        COALESCE(custom, ''), '|', COALESCE(elements, '')
      )),
      r'(^|[?&])p=h5phx([&#]|$)'
    ) AS p_url_marker_present,
    REGEXP_CONTAINS(
      LOWER(CONCAT(
        COALESCE(url, ''), '|', COALESCE(element_target_url, ''), '|', COALESCE(url_path, ''), '|',
        COALESCE(path_name, ''), '|', COALESCE(referrer, ''), '|', COALESCE(latest_referrer, ''), '|',
        COALESCE(custom, ''), '|', COALESCE(elements, ''), '|', COALESCE(utm_source, ''), '|',
        COALESCE(utm_medium, ''), '|', COALESCE(utm_campaign, ''), '|', COALESCE(traffic_source_type, '')
      )),
      r'(h5phx|phenix)'
    ) AS any_h5phx_marker_present
  FROM `wajenigeria.origin_hfyl.realtime_event_web`
  CROSS JOIN date_bounds
  WHERE target_day BETWEEN event_date AND DATE '2026-09-01'
)
SELECT
  target_day,
  COALESCE(NULLIF(event_type, ''), '(blank)') AS event_type,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count,
  COUNTIF(p_url_marker_present) AS p_url_marker_count,
  COUNTIF(any_h5phx_marker_present) AS any_h5phx_marker_count,
  COUNTIF(LOWER(COALESCE(utm_source, '')) = 'h5phx') AS utm_source_h5phx_count,
  COUNTIF(LOWER(COALESCE(utm_medium, '')) = 'h5phx') AS utm_medium_h5phx_count,
  COUNTIF(LOWER(COALESCE(utm_campaign, '')) = 'h5phx') AS utm_campaign_h5phx_count,
  COUNTIF(event_id IS NULL OR event_id = '') AS missing_event_id_count,
  COUNTIF(session_id IS NULL OR session_id = '') AS missing_session_id_count
FROM base
GROUP BY target_day, event_type
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY target_day, event_count DESC
LIMIT 3000
