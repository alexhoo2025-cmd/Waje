WITH events AS (
 SELECT target_day AS cohort_date,app_id,user_id,client_type,event_type,custom,is_success,is_first_buy,
  timezone,timezone_offset,SAFE_CAST(time AS INT64) AS event_time_number,noun_type
 FROM `wajenigeria.origin_hfyl.view_event_server`
 WHERE target_day BETWEEN DATE '2026-09-01' AND DATE '2026-09-03'
 AND event_type IN ('REGISTER','LOGIN','ORDER','LOGOUT')
)
SELECT cohort_date,app_id,client_type,event_type,is_success,is_first_buy,noun_type,
 COUNT(*) AS events,COUNT(DISTINCT user_id) AS users,
 COUNTIF(JSON_VALUE(custom,'$.is_pwa') IS NOT NULL) AS is_pwa_count,
 COUNTIF(JSON_VALUE(custom,'$.display_mode') IS NOT NULL) AS display_mode_count,
 COUNTIF(JSON_VALUE(custom,'$.standalone') IS NOT NULL) AS standalone_count,
 COUNTIF(JSON_VALUE(custom,'$.is_webview') IS NOT NULL) AS webview_count,
 MIN(timezone) AS min_timezone,MAX(timezone) AS max_timezone,
 MIN(timezone_offset) AS min_timezone_offset,MAX(timezone_offset) AS max_timezone_offset,
 COUNTIF(event_time_number BETWEEN 1788220800000 AND 1788566400000) AS timestamp_millis_in_window
FROM events
WHERE cohort_date BETWEEN DATE '2026-09-01' AND DATE '2026-09-03'
GROUP BY cohort_date,app_id,client_type,event_type,is_success,is_first_buy,noun_type
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY events DESC
LIMIT 3000;
