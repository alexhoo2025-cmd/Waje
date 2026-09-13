WITH events AS (
  SELECT
    target_day AS biz_date,
    CASE WHEN event_type='ORDER' THEN '充值' ELSE '提现' END AS metric,
    CASE WHEN event_type='ORDER' THEN order_no ELSE serial_num END AS transaction_key,
    user_id,
    CASE WHEN event_type='ORDER' THEN pay_amount ELSE cash_num/100.0 END AS amount
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day=DATE '2026-09-10'
    AND app_id=90006
    AND ((event_type='ORDER' AND is_success='pay_success') OR (event_type='WITHDRAW' AND log_event_type='server_event'))
), deduplicated AS (
  SELECT biz_date,metric,transaction_key,ANY_VALUE(user_id) AS user_id,MAX(amount) AS amount
  FROM events
  WHERE biz_date=DATE '2026-09-10' AND transaction_key IS NOT NULL AND user_id IS NOT NULL
  GROUP BY 1,2,3
), per_user AS (
  SELECT user_id,SUM(IF(metric='充值',amount,0)) AS recharge,
         SUM(IF(metric='提现',amount,0)) AS withdraw,
         SUM(IF(metric='提现',amount,0))-SUM(IF(metric='充值',amount,0)) AS net_cash_out
  FROM deduplicated
  WHERE biz_date=DATE '2026-09-10'
  GROUP BY user_id
), ranked AS (
  SELECT user_id,recharge,withdraw,net_cash_out,
         ROW_NUMBER() OVER(ORDER BY net_cash_out DESC) AS rank_number
  FROM per_user
  WHERE net_cash_out>0
), bucketed AS (
  SELECT
    CASE WHEN rank_number<=10 THEN '前10名合计'
         WHEN rank_number<=50 THEN '第11—50名合计'
         WHEN rank_number<=100 THEN '第51—100名合计'
         ELSE '第101名以后合计' END AS rank_group,
    recharge,withdraw,net_cash_out
  FROM ranked
), total AS (SELECT SUM(net_cash_out) AS total_positive_net_cash_out FROM ranked)
SELECT rank_group,COUNT(*) AS user_count,SUM(recharge) AS recharge,
       SUM(withdraw) AS withdraw,SUM(net_cash_out) AS net_cash_out,
       AVG(net_cash_out) AS average_net_cash_out,
       SAFE_DIVIDE(SUM(net_cash_out),ANY_VALUE(total_positive_net_cash_out)) AS share_of_positive_net_cash_out
FROM bucketed CROSS JOIN total
GROUP BY rank_group
HAVING user_count>=10
ORDER BY CASE rank_group WHEN '前10名合计' THEN 1 WHEN '第11—50名合计' THEN 2 WHEN '第51—100名合计' THEN 3 ELSE 4 END
LIMIT 10;
