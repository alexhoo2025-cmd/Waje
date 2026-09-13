WITH scoped AS (
 SELECT target_day AS stat_date,app_id,event_type,client_type,user_id,play_id,
        element_id,app_key,session_id,custom,package_name
 FROM `wajenigeria.origin_hfyl.realtime_event_client`
 WHERE target_day=DATE '2026-09-06' AND app_id=90006
   AND event_type IN ('GAMEEND','GAMESTART','MC','MV','PV','PD','AL')
)
SELECT event_type,client_type,package_name,
       COUNT(1) AS event_rows,COUNT(DISTINCT user_id) AS users,
       COUNTIF(SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9169999) AS joint_play_code_rows,
       COUNTIF(SAFE_CAST(element_id AS INT64) BETWEEN 40001 AND 59999) AS joint_element_code_rows,
       COUNTIF(app_key IS NOT NULL AND app_key!='') AS app_key_rows,
       COUNTIF(session_id IS NOT NULL AND session_id!='') AS session_present_rows,
       COUNTIF(custom IS NOT NULL AND custom NOT IN ('','{}')) AS custom_present_rows
FROM scoped WHERE stat_date=DATE '2026-09-06'
GROUP BY event_type,client_type,package_name
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY event_type,event_rows DESC
LIMIT 1000;
