WITH events AS (
 SELECT target_day AS stat_date,user_id,event_type,is_success,is_accept,mode_id,asset_id,noun_type,
        pay_amount,price_amount,cash_num,change_count,service_fee,order_no,serial_num,is_test_uid
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND app_id=90006 AND event_type IN ('ORDER','WITHDRAW')
)
SELECT event_type,is_success,is_accept,mode_id,asset_id,noun_type,
 COUNT(1) AS event_records,COUNT(DISTINCT user_id) AS accounts,
 COUNT(DISTINCT order_no) AS distinct_order_keys,COUNT(DISTINCT serial_num) AS distinct_serial_keys,
 COUNTIF(order_no IS NULL OR order_no='') AS missing_order_keys,
 COUNTIF(serial_num IS NULL OR serial_num='') AS missing_serial_keys,
 SUM(pay_amount) AS pay_amount_sum,SUM(price_amount) AS price_amount_sum,
 SUM(cash_num) AS cash_num_sum,SUM(change_count) AS change_count_sum,SUM(service_fee) AS service_fee_sum,
 MIN(stat_date) AS first_date,MAX(stat_date) AS last_date,COUNT(DISTINCT stat_date) AS observed_dates
FROM events WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
 AND (is_test_uid IS NULL OR is_test_uid!=1)
GROUP BY event_type,is_success,is_accept,mode_id,asset_id,noun_type
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY event_type,event_records DESC
LIMIT 300;
