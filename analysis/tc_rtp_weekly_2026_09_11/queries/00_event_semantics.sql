WITH pay AS (
  SELECT
    target_day AS biz_date,
    COALESCE(event_type, '(blank)') AS semantic_state,
    COALESCE(log_event_type, '(blank)') AS log_event_type,
    COALESCE(CAST(order_type AS STRING), '(null)') AS order_type,
    COALESCE(noun_type, '(blank)') AS noun_type,
    COUNT(*) AS event_rows,
    COUNT(DISTINCT order_no) AS distinct_orders,
    SUM(COALESCE(pay_amount, 0)) AS amount
  FROM `wajenigeria.origin_hfyl.view_event_pay`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
    AND app_id = 90006
  GROUP BY 1,2,3,4,5
), withdrawal AS (
  SELECT
    target_day AS biz_date,
    COALESCE(log_event_type, '(blank)') AS log_event_type,
    COALESCE(CAST(asset_id AS STRING), '(null)') AS asset_id,
    COALESCE(channel, '(blank)') AS channel,
    COUNT(*) AS event_rows,
    COUNT(DISTINCT serial_num) AS distinct_orders,
    SUM(COALESCE(cash, 0)) AS cash,
    SUM(COALESCE(valid_count, 0)) AS valid_count
  FROM `wajenigeria.origin_hfyl.view_event_withdraw`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
    AND app_id = 90006
  GROUP BY 1,2,3,4
)
SELECT 'pay' AS source, biz_date AS target_day, semantic_state AS state_1, log_event_type AS state_2,
       order_type AS state_3, noun_type AS state_4, event_rows, distinct_orders,
       amount AS amount_1, CAST(NULL AS FLOAT64) AS amount_2
FROM pay
WHERE biz_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
UNION ALL
SELECT 'withdraw', biz_date, log_event_type, asset_id, channel, '(n/a)', event_rows,
       distinct_orders, cash, CAST(valid_count AS FLOAT64)
FROM withdrawal
WHERE biz_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
ORDER BY source, target_day, state_1, state_2
LIMIT 3000;
