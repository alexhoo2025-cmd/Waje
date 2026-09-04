-- Aggregate-only integrity profile for server payment events.
-- No order ID, user ID, payment method, or transaction rows are returned.
WITH pay_events_base AS (
  SELECT
    target_day AS cohort_date,
    event_type,
    log_event_type,
    is_first_buy,
    order_no,
    user_id,
    order_type,
    noun_type,
    pay_amount
  FROM `wajenigeria.origin_hfyl.view_event_pay`
), order_flags AS (
  SELECT
    cohort_date,
    order_no,
    LOGICAL_OR(event_type = 'order_success') AS has_order_success,
    LOGICAL_OR(event_type = 'pay_success') AS has_pay_success,
    COUNT(*) AS source_event_count
  FROM pay_events_base
  WHERE cohort_date BETWEEN DATE '2026-08-27' AND DATE '2026-09-02'
    AND order_no IS NOT NULL
    AND order_no != ''
  GROUP BY cohort_date, order_no
), event_profile AS (
  SELECT
    cohort_date,
    event_type,
    log_event_type,
    is_first_buy,
    order_type,
    COALESCE(NULLIF(noun_type, ''), '(blank)') AS noun_type,
    COUNT(*) AS source_event_count,
    APPROX_COUNT_DISTINCT(user_id) AS approx_subject_count,
    APPROX_COUNT_DISTINCT(order_no) AS approx_order_count,
    SUM(COALESCE(pay_amount, 0)) AS pay_amount_sum
  FROM pay_events_base
  WHERE cohort_date BETWEEN DATE '2026-08-27' AND DATE '2026-09-02'
  GROUP BY cohort_date, event_type, log_event_type, is_first_buy, order_type, noun_type
)
SELECT
  'event_profile' AS result_type,
  CAST(cohort_date AS STRING) AS target_day,
  event_type,
  CAST(log_event_type AS STRING) AS log_event_type,
  CAST(is_first_buy AS STRING) AS is_first_buy,
  CAST(order_type AS STRING) AS order_type,
  noun_type,
  source_event_count,
  approx_subject_count,
  approx_order_count,
  pay_amount_sum
FROM event_profile
WHERE approx_subject_count >= 10
UNION ALL
SELECT
  'order_overlap' AS result_type,
  CAST(cohort_date AS STRING) AS target_day,
  '(all)' AS event_type,
  '(all)' AS log_event_type,
  '(all)' AS is_first_buy,
  '(all)' AS order_type,
  CASE
    WHEN has_order_success AND has_pay_success THEN 'both_event_types'
    WHEN has_order_success THEN 'order_success_only'
    WHEN has_pay_success THEN 'pay_success_only'
    ELSE 'other'
  END AS noun_type,
  COUNT(*) AS source_event_count,
  CAST(NULL AS INT64) AS approx_subject_count,
  COUNT(*) AS approx_order_count,
  CAST(NULL AS FLOAT64) AS pay_amount_sum
FROM order_flags
GROUP BY cohort_date, has_order_success, has_pay_success
ORDER BY result_type, target_day, event_type, order_type, noun_type;
