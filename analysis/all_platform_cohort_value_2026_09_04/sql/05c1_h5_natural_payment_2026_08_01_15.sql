-- Aggregate-only August 1-15 strict H5 natural payment lifecycle; success orders only.
WITH cohort AS (
  SELECT DISTINCT target_day AS cohort_date, user_id
  FROM `wajenigeria.origin_hfyl.user_events`
  WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-15'
    AND SAFE.PARSE_DATE('%Y-%m-%d', register_day) = target_day
    AND first_package_name = 'com.wajegame.web'
    AND download_channel = 'PAWAJEBETH5' AND first_channel = 'PAWAJEBETH5' AND first_sub_channel = 'PAWAJEBETH5'
), raw_success_orders AS (
  SELECT target_day AS payment_date, user_id, order_no, pay_amount
  FROM `wajenigeria.origin_hfyl.view_event_pay`
  WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-28'
    AND event_type = 'order_success' AND user_id IS NOT NULL AND user_id != '' AND order_no IS NOT NULL AND order_no != ''
), successful_orders AS (
  SELECT payment_date, user_id, order_no, MAX(COALESCE(pay_amount, 0)) AS order_amount
  FROM raw_success_orders GROUP BY payment_date, user_id, order_no
), lifecycle AS (
  SELECT cohort.cohort_date, cohort.user_id, successful_orders.payment_date, successful_orders.order_amount
  FROM cohort LEFT JOIN successful_orders ON successful_orders.user_id = cohort.user_id AND successful_orders.payment_date >= cohort.cohort_date
)
SELECT cohort_date, COUNT(DISTINCT user_id) AS cohort_users,
  SAFE_DIVIDE(COUNT(DISTINCT IF(payment_date <= cohort_date, user_id, NULL)), COUNT(DISTINCT user_id)) AS day_1_payment_rate,
  SAFE_DIVIDE(COUNT(DISTINCT IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 6 DAY), user_id, NULL)), COUNT(DISTINCT user_id)) AS day_7_payment_rate,
  SAFE_DIVIDE(COUNT(DISTINCT IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 13 DAY), user_id, NULL)), COUNT(DISTINCT user_id)) AS day_14_payment_rate,
  SAFE_DIVIDE(SUM(IF(payment_date <= cohort_date, order_amount, 0)), COUNT(DISTINCT user_id)) AS day_1_arpu,
  SAFE_DIVIDE(SUM(IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 6 DAY), order_amount, 0)), COUNT(DISTINCT user_id)) AS day_7_arpu,
  SAFE_DIVIDE(SUM(IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 13 DAY), order_amount, 0)), COUNT(DISTINCT user_id)) AS day_14_arpu,
  DATE '2026-09-04' AS data_cutoff_date
FROM lifecycle
WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-15'
GROUP BY cohort_date HAVING COUNT(DISTINCT user_id) >= 10 ORDER BY cohort_date;
