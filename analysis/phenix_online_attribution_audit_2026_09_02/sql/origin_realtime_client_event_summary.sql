-- Origin realtime client event summary for one complete day.
-- No identifiers or payment amounts are returned; only event/package aggregate counts.
WITH date_bounds AS (
  SELECT DATE '2026-09-01' AS event_date
)
SELECT
  COALESCE(NULLIF(CAST(client_type AS STRING), ''), '(blank)') AS client_type,
  COALESCE(NULLIF(package_name, ''), '(blank)') AS package_name,
  COALESCE(NULLIF(package_channel, ''), '(blank)') AS package_channel,
  COALESCE(NULLIF(package_sub_channel, ''), '(blank)') AS package_sub_channel,
  COALESCE(NULLIF(event_type, ''), '(blank)') AS event_type,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) AS approx_subject_count,
  COUNTIF(is_success IS NOT NULL AND is_success != '') AS success_flag_present_count,
  COUNTIF(is_first_buy = TRUE) AS first_buy_flag_count,
  COUNTIF(is_robot = TRUE) AS robot_flag_count,
  COUNTIF(app_version IS NULL OR app_version = '') AS missing_app_version_count,
  COUNTIF(session_id IS NULL OR session_id = '') AS missing_session_id_count,
  COUNTIF(REGEXP_CONTAINS(LOWER(event_type), r'(register|recharge|purchase|withdraw|payment|login|pay)')) AS business_event_candidate_count
FROM `wajenigeria.origin_hfyl.realtime_event_client`
CROSS JOIN date_bounds
WHERE target_day = event_date
GROUP BY client_type, package_name, package_channel, package_sub_channel, event_type
HAVING APPROX_COUNT_DISTINCT(IF(user_id IS NULL OR user_id = '', NULL, user_id)) >= 10
ORDER BY event_count DESC, package_name, event_type
LIMIT 3000
