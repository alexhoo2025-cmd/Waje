WITH tada_players AS (
  SELECT
    target_day AS biz_date,
    user_id
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN DATE '2026-09-03' AND DATE '2026-09-10'
    AND app_id=90006
    AND event_type='GAMEEND'
    AND mode_id=11
    AND SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9159999
    AND CAST(bet_num AS BIGNUMERIC)-COALESCE(refund_num,0)>0
    AND is_robot IS FALSE
    AND (is_test_uid IS NULL OR is_test_uid!=1)
    AND user_id IS NOT NULL
  GROUP BY 1,2
), money_events AS (
  SELECT
    target_day AS biz_date,
    user_id,
    CASE WHEN event_type='ORDER' THEN '充值' ELSE '提现' END AS metric,
    CASE WHEN event_type='ORDER' THEN order_no ELSE serial_num END AS transaction_key,
    CASE WHEN event_type='ORDER' THEN pay_amount ELSE cash_num/100.0 END AS amount
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN DATE '2026-09-03' AND DATE '2026-09-10'
    AND app_id=90006
    AND user_id IS NOT NULL
    AND ((event_type='ORDER' AND is_success='pay_success') OR (event_type='WITHDRAW' AND log_event_type='server_event'))
), deduplicated_money AS (
  SELECT biz_date,user_id,metric,transaction_key,MAX(amount) AS amount
  FROM money_events
  WHERE biz_date BETWEEN DATE '2026-09-03' AND DATE '2026-09-10'
    AND transaction_key IS NOT NULL
  GROUP BY 1,2,3,4
), daily AS (
  SELECT
    p.biz_date,
    COUNT(DISTINCT p.user_id) AS tada_bettors,
    COUNT(DISTINCT IF(m.metric='充值',p.user_id,NULL)) AS recharge_users,
    COUNT(DISTINCT IF(m.metric='提现',p.user_id,NULL)) AS withdraw_users,
    COUNT(DISTINCT IF(m.metric='充值',m.transaction_key,NULL)) AS recharge_orders,
    COUNT(DISTINCT IF(m.metric='提现',m.transaction_key,NULL)) AS withdraw_orders,
    SUM(IF(m.metric='充值',m.amount,0)) AS recharge,
    SUM(IF(m.metric='提现',m.amount,0)) AS withdraw
  FROM tada_players p
  LEFT JOIN deduplicated_money m USING (biz_date,user_id)
  WHERE p.biz_date BETWEEN DATE '2026-09-03' AND DATE '2026-09-10'
  GROUP BY p.biz_date
  HAVING tada_bettors>=10
)
SELECT
  biz_date,tada_bettors,recharge_users,withdraw_users,recharge_orders,withdraw_orders,
  recharge,withdraw,SAFE_DIVIDE(withdraw,recharge) AS tc_rate
FROM daily
WHERE biz_date BETWEEN DATE '2026-09-03' AND DATE '2026-09-10'
ORDER BY biz_date
LIMIT 100;
