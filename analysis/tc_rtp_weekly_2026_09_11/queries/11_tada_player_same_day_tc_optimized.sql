WITH user_day AS (
  SELECT
    target_day AS biz_date,
    user_id,
    COUNTIF(
      event_type='GAMEEND' AND mode_id=11
      AND SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9159999
      AND CAST(bet_num AS BIGNUMERIC)-COALESCE(refund_num,0)>0
      AND is_robot IS FALSE AND (is_test_uid IS NULL OR is_test_uid!=1)
    ) AS tada_bet_rows,
    SUM(IF(event_type='ORDER' AND is_success='pay_success',pay_amount,0)) AS recharge,
    SUM(IF(event_type='WITHDRAW' AND log_event_type='server_event',cash_num/100.0,0)) AS withdraw,
    COUNTIF(event_type='ORDER' AND is_success='pay_success') AS recharge_event_rows,
    COUNT(DISTINCT IF(event_type='ORDER' AND is_success='pay_success',order_no,NULL)) AS recharge_orders,
    COUNTIF(event_type='WITHDRAW' AND log_event_type='server_event') AS withdraw_event_rows,
    COUNT(DISTINCT IF(event_type='WITHDRAW' AND log_event_type='server_event',serial_num,NULL)) AS withdraw_orders
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN DATE '2026-09-03' AND DATE '2026-09-10'
    AND app_id=90006
    AND user_id IS NOT NULL
    AND event_type IN ('GAMEEND','ORDER','WITHDRAW')
  GROUP BY 1,2
), daily AS (
  SELECT
    biz_date,
    COUNT(*) AS tada_bettors,
    COUNTIF(recharge>0) AS recharge_users,
    COUNTIF(withdraw>0) AS withdraw_users,
    SUM(recharge_orders) AS recharge_orders,
    SUM(withdraw_orders) AS withdraw_orders,
    SUM(recharge) AS recharge,
    SUM(withdraw) AS withdraw,
    SUM(recharge_event_rows-recharge_orders) AS duplicate_recharge_rows,
    SUM(withdraw_event_rows-withdraw_orders) AS duplicate_withdraw_rows
  FROM user_day
  WHERE biz_date BETWEEN DATE '2026-09-03' AND DATE '2026-09-10'
    AND tada_bet_rows>0
  GROUP BY biz_date
  HAVING tada_bettors>=10
)
SELECT
  biz_date,tada_bettors,recharge_users,withdraw_users,recharge_orders,withdraw_orders,
  recharge,withdraw,SAFE_DIVIDE(withdraw,recharge) AS tc_rate,
  duplicate_recharge_rows,duplicate_withdraw_rows
FROM daily
WHERE biz_date BETWEEN DATE '2026-09-03' AND DATE '2026-09-10'
ORDER BY biz_date
LIMIT 100;
