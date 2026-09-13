WITH events AS (
  SELECT
    target_day AS biz_date,
    CASE WHEN event_type='ORDER' THEN '充值' ELSE '提现' END AS metric,
    CASE WHEN event_type='ORDER' THEN order_no ELSE serial_num END AS transaction_key,
    CASE WHEN event_type='ORDER' THEN pay_amount ELSE cash_num/100.0 END AS amount,
    EXTRACT(HOUR FROM DATETIME(TIMESTAMP_MILLIS(SAFE_CAST(`time` AS INT64)),'Africa/Lagos')) AS local_hour
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
    AND app_id=90006
    AND ((event_type='ORDER' AND is_success='pay_success') OR (event_type='WITHDRAW' AND log_event_type='server_event'))
), deduplicated AS (
  SELECT biz_date,metric,transaction_key,MAX(amount) AS amount,ANY_VALUE(local_hour) AS local_hour
  FROM events
  WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
    AND transaction_key IS NOT NULL AND local_hour IS NOT NULL
  GROUP BY 1,2,3
)
SELECT
  metric,
  IF(biz_date=DATE '2026-09-10','9月10日','9月4—9日') AS period,
  FORMAT('%02d:00—%02d:59',DIV(local_hour,3)*3,DIV(local_hour,3)*3+2) AS time_band,
  SUM(amount) AS amount,
  COUNT(*) AS transactions,
  AVG(amount) AS mean_amount
FROM deduplicated
WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
GROUP BY 1,2,3
ORDER BY metric,period,time_band
LIMIT 100;
