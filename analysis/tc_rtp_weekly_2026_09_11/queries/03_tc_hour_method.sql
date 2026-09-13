WITH events AS (
  SELECT
    target_day AS biz_date,
    CASE WHEN event_type='ORDER' THEN '充值' ELSE '提现' END AS metric,
    CASE WHEN event_type='ORDER' THEN order_no ELSE serial_num END AS transaction_key,
    user_id,
    CASE WHEN event_type='ORDER' THEN pay_amount ELSE cash_num/100.0 END AS amount,
    CASE WHEN event_type='ORDER' THEN COALESCE(NULLIF(pay_way,''),'(unknown)') ELSE COALESCE(NULLIF(withdraw_method,''),'(unknown)') END AS method,
    SAFE.PARSE_TIMESTAMP('%F %H:%M:%E*S',local_time) AS local_ts
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
    AND app_id=90006
    AND ((event_type='ORDER' AND is_success='pay_success') OR (event_type='WITHDRAW' AND log_event_type='server_event'))
), deduplicated AS (
  SELECT biz_date,metric,transaction_key,ANY_VALUE(user_id) AS user_id,MAX(amount) AS amount,
         ANY_VALUE(method) AS method,ANY_VALUE(local_ts) AS local_ts
  FROM events
  WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10' AND transaction_key IS NOT NULL
  GROUP BY 1,2,3
), hourly AS (
  SELECT metric,IF(biz_date=DATE '2026-09-10','9月10日','9月4—9日') AS period,
         FORMAT('%02d时',EXTRACT(HOUR FROM local_ts)) AS bucket,
         SUM(amount) AS amount,COUNT(*) AS transactions,APPROX_COUNT_DISTINCT(user_id) AS users,
         SAFE_DIVIDE(COUNTIF(local_ts IS NOT NULL),COUNT(*)) AS parsed_time_share
  FROM deduplicated
  WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
  GROUP BY 1,2,3
  HAVING users>=10
), methods AS (
  SELECT metric,IF(biz_date=DATE '2026-09-10','9月10日','9月4—9日') AS period,
         method AS bucket,SUM(amount) AS amount,COUNT(*) AS transactions,
         APPROX_COUNT_DISTINCT(user_id) AS users,CAST(NULL AS FLOAT64) AS parsed_time_share
  FROM deduplicated
  WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
  GROUP BY 1,2,3
  HAVING users>=10
)
SELECT '小时' AS row_type,metric,period,bucket,amount,transactions,users,parsed_time_share
FROM hourly
WHERE period IN ('9月10日','9月4—9日')
UNION ALL
SELECT '方式',metric,period,bucket,amount,transactions,users,parsed_time_share
FROM methods
WHERE period IN ('9月10日','9月4—9日')
ORDER BY row_type,metric,period,amount DESC
LIMIT 3000;
