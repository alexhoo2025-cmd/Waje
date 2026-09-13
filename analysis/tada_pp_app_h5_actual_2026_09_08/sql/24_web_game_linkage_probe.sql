-- One complete-day telemetry linkage check, not a full-period performance measurement.
WITH events AS (
 SELECT target_day AS stat_date,user_id,event_type,page_resource_size,session_id,custom,element_id,element_content
 FROM `wajenigeria.origin_hfyl.realtime_event_web`
 WHERE target_day=DATE '2026-09-06' AND app_id=90006
)
SELECT event_type,COUNT(1) AS records,COUNT(DISTINCT user_id) AS accounts,
 COUNTIF(session_id IS NOT NULL AND session_id!='') AS session_tagged_records,
 COUNTIF(page_resource_size>0) AS page_resource_size_records,
 COUNTIF(SAFE_CAST(element_id AS INT64) BETWEEN 40001 AND 59999) AS direct_joint_game_element_records,
 COUNTIF(REGEXP_CONTAINS(COALESCE(custom,''),r'"(?:game_id|play_id|gameId)"')) AS custom_game_key_records,
 COUNTIF(REGEXP_CONTAINS(COALESCE(custom,''),r'"(?:open_id|game_open_id|load_duration|load_status|load_time|cache_hit)"')) AS custom_load_or_open_key_records,
 COUNTIF(REGEXP_CONTAINS(COALESCE(element_content,''),r'"(?:game_id|play_id|gameId)"')) AS element_game_key_records
FROM events WHERE stat_date=DATE '2026-09-06'
GROUP BY event_type HAVING COUNT(DISTINCT user_id)>=10
ORDER BY records DESC
LIMIT 50;
