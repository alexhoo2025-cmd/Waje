WITH events AS (
 SELECT target_day AS cohort_date,app_id,user_id,client_type,event_type,custom,
  JSON_KEYS(SAFE.PARSE_JSON(custom),1) AS custom_keys,
  timezone,timezone_offset,SAFE_CAST(time AS INT64) AS event_time_number
 FROM `wajenigeria.origin_hfyl.view_event_web`
 WHERE target_day BETWEEN DATE '2026-09-01' AND DATE '2026-09-03'
)
SELECT cohort_date,app_id,client_type,event_type,
 COUNT(*) AS events,COUNT(DISTINCT user_id) AS users,
 COUNTIF(custom IS NOT NULL AND custom NOT IN ('','{}','null')) AS with_custom,
 COUNTIF(JSON_VALUE(custom,'$.is_pwa') IS NOT NULL) AS is_pwa_count,
 COUNTIF(JSON_VALUE(custom,'$.display_mode') IS NOT NULL) AS display_mode_count,
 COUNTIF(JSON_VALUE(custom,'$.standalone') IS NOT NULL) AS standalone_count,
 COUNTIF(JSON_VALUE(custom,'$.is_webview') IS NOT NULL) AS webview_count,
 COUNTIF(EXISTS(SELECT 1 FROM UNNEST(custom_keys) k WHERE REGEXP_CONTAINS(LOWER(k),r'pwa|standalone|display.?mode|webview'))) AS other_runtime_keys,
 COUNTIF(cohort_date=DATE(TIMESTAMP_MILLIS(event_time_number),'Africa/Lagos')) AS lagos_date_match,
 COUNTIF(cohort_date=DATE(TIMESTAMP_MILLIS(event_time_number),'UTC')) AS utc_date_match
FROM events
WHERE cohort_date BETWEEN DATE '2026-09-01' AND DATE '2026-09-03'
GROUP BY cohort_date,app_id,client_type,event_type
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY events DESC
LIMIT 3000;
