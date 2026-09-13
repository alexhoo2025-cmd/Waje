WITH orders AS (
 SELECT target_day AS cohort_date, user_id, event_type, is_first_buy
 FROM `wajenigeria.origin_hfyl.view_event_pay`
 WHERE target_day BETWEEN DATE '2026-09-01' AND DATE '2026-09-03'
)
SELECT event_type, CAST(is_first_buy AS STRING) AS first_buy_flag,
 COUNT(*) AS event_rows, COUNT(DISTINCT user_id) AS users
FROM orders
WHERE cohort_date BETWEEN DATE '2026-09-01' AND DATE '2026-09-03'
GROUP BY event_type, first_buy_flag
HAVING COUNT(DISTINCT user_id) >= 10
LIMIT 100;
