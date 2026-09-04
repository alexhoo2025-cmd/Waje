-- Aggregate-only payment event profile for selecting successful-payment facts.
-- No order numbers, payment methods, users, or monetary detail rows are returned.
WITH pay_events_base AS (
  SELECT
    target_day AS cohort_date,
    event_type,
    log_event_type,
    is_first_buy,
    user_id,
    pay_amount,
    amount
  FROM `wajenigeria.origin_hfyl.view_event_pay`
)
SELECT
  cohort_date AS target_day,
  COALESCE(NULLIF(event_type, ''), '(blank)') AS event_type,
  COALESCE(NULLIF(log_event_type, ''), '(blank)') AS log_event_type,
  is_first_buy,
  COUNT(*) AS event_count,
  APPROX_COUNT_DISTINCT(user_id) AS approx_payer_count,
  SUM(COALESCE(pay_amount, 0)) AS pay_amount_sum,
  SUM(COALESCE(amount, 0)) AS amount_sum
FROM pay_events_base
WHERE cohort_date BETWEEN DATE '2026-08-27' AND DATE '2026-09-02'
GROUP BY cohort_date, event_type, log_event_type, is_first_buy
HAVING APPROX_COUNT_DISTINCT(user_id) >= 10
ORDER BY target_day, event_type, log_event_type, is_first_buy;
