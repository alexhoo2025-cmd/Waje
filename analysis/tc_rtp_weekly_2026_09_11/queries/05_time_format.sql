WITH raw AS (
SELECT
  target_day AS biz_date,event_type,`time`,server_time,local_time
FROM `wajenigeria.origin_hfyl.view_event_server`
WHERE target_day = DATE '2026-09-10'
  AND app_id=90006
  AND ((event_type='ORDER' AND is_success='pay_success') OR (event_type='WITHDRAW' AND log_event_type='server_event'))
)
SELECT
  CASE WHEN event_type='ORDER' THEN '充值' ELSE '提现' END AS metric,
  LENGTH(COALESCE(`time`,'')) AS time_length,
  LENGTH(COALESCE(server_time,'')) AS server_time_length,
  LENGTH(COALESCE(local_time,'')) AS local_time_length,
  COUNT(*) AS event_rows,
  COUNTIF(SAFE_CAST(`time` AS INT64) IS NOT NULL) AS numeric_time_rows,
  COUNTIF(SAFE_CAST(server_time AS INT64) IS NOT NULL) AS numeric_server_time_rows,
  COUNTIF(SAFE.PARSE_TIMESTAMP('%F %H:%M:%E*S',server_time) IS NOT NULL) AS parsed_server_time_rows,
  COUNTIF(SAFE.PARSE_TIMESTAMP('%F %H:%M:%E*S',local_time) IS NOT NULL) AS parsed_local_time_rows,
  MIN(SAFE_CAST(`time` AS INT64)) AS min_numeric_time,
  MAX(SAFE_CAST(`time` AS INT64)) AS max_numeric_time
FROM raw
WHERE biz_date = DATE '2026-09-10'
GROUP BY 1,2,3,4
ORDER BY metric,event_rows DESC
LIMIT 100;
