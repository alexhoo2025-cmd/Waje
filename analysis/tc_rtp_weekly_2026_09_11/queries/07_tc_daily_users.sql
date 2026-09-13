WITH events AS (
  SELECT
    target_day AS biz_date,
    CASE WHEN event_type='ORDER' THEN '充值' ELSE '提现' END AS metric,
    CASE WHEN event_type='ORDER' THEN order_no ELSE serial_num END AS transaction_key,
    user_id,
    CASE WHEN event_type='ORDER' THEN pay_amount ELSE cash_num/100.0 END AS amount
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
    AND app_id=90006
    AND ((event_type='ORDER' AND is_success='pay_success') OR (event_type='WITHDRAW' AND log_event_type='server_event'))
), deduplicated AS (
  SELECT biz_date,metric,transaction_key,ANY_VALUE(user_id) AS user_id,MAX(amount) AS amount
  FROM events
  WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
    AND transaction_key IS NOT NULL
  GROUP BY 1,2,3
)
SELECT
  biz_date,
  metric,
  COUNT(*) AS transactions,
  APPROX_COUNT_DISTINCT(user_id) AS users,
  SUM(amount) AS amount,
  SAFE_DIVIDE(SUM(amount),APPROX_COUNT_DISTINCT(user_id)) AS amount_per_user,
  SAFE_DIVIDE(COUNT(*),APPROX_COUNT_DISTINCT(user_id)) AS transactions_per_user
FROM deduplicated
WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
GROUP BY 1,2
HAVING users>=10
ORDER BY biz_date,metric
LIMIT 100;
