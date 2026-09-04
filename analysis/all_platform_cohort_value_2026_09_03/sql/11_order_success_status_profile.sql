-- Aggregate-only order success-status profile for payment-fact selection.
WITH order_events AS (
  SELECT
    target_day AS cohort_date,
    event_type,
    is_success,
    is_first_buy,
    noun_type,
    order_type,
    order_no,
    user_id,
    pay_amount
  FROM `wajenigeria.origin_hfyl.view_metaevent_order`
)
SELECT
  cohort_date AS target_day,
  COALESCE(NULLIF(event_type, ''), '(blank)') AS event_type,
  COALESCE(NULLIF(is_success, ''), '(blank)') AS is_success,
  is_first_buy,
  COALESCE(NULLIF(noun_type, ''), '(blank)') AS noun_type,
  order_type,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count,
  APPROX_COUNT_DISTINCT(order_no) AS approx_order_count,
  SUM(COALESCE(pay_amount, 0)) AS pay_amount_sum
FROM order_events
WHERE cohort_date BETWEEN DATE '2026-08-27' AND DATE '2026-09-02'
GROUP BY cohort_date, event_type, is_success, is_first_buy, noun_type, order_type
HAVING APPROX_COUNT_DISTINCT(user_id) >= 10
ORDER BY target_day, event_type, is_success, is_first_buy, noun_type, order_type;
