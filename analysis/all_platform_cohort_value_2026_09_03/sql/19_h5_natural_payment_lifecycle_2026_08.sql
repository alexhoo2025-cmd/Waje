-- Aggregate-only strict H5 natural registration cohort payment lifecycle.
-- Cohort and payer numerators use the same frozen user set.
WITH cohort_base AS (
  SELECT DISTINCT
    target_day AS cohort_date,
    user_id
  FROM `wajenigeria.origin_hfyl.user_xlid`
  WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
    AND SAFE.PARSE_DATE('%Y-%m-%d', register_day) = target_day
    AND first_package_name = 'com.wajegame.web'
    AND download_channel = 'PAWAJEBETH5'
    AND first_channel = 'PAWAJEBETH5'
    AND first_sub_channel = 'PAWAJEBETH5'
), raw_orders AS (
  SELECT
    target_day AS payment_date,
    user_id,
    order_no,
    pay_amount
  FROM `wajenigeria.origin_hfyl.view_event_pay`
  WHERE event_type = 'order_success'
), successful_orders AS (
  SELECT
    payment_date,
    user_id,
    order_no,
    MAX(COALESCE(pay_amount, 0)) AS order_amount
  FROM raw_orders
  WHERE payment_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-02'
    AND order_no IS NOT NULL
    AND order_no != ''
  GROUP BY payment_date, user_id, order_no
), lifecycle AS (
  SELECT
    cohort_base.cohort_date,
    cohort_base.user_id,
    successful_orders.payment_date,
    successful_orders.order_amount
  FROM cohort_base
  LEFT JOIN successful_orders
    ON successful_orders.user_id = cohort_base.user_id
   AND successful_orders.payment_date >= cohort_base.cohort_date
)
SELECT
  cohort_date,
  COUNT(DISTINCT user_id) AS cohort_users,
  IF(DATE '2026-09-02' >= cohort_date, COUNT(DISTINCT IF(payment_date <= cohort_date, user_id, NULL)), NULL) AS day_1_payers,
  IF(DATE '2026-09-02' >= cohort_date, SAFE_DIVIDE(COUNT(DISTINCT IF(payment_date <= cohort_date, user_id, NULL)), COUNT(DISTINCT user_id)), NULL) AS day_1_payment_rate,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 6 DAY), SAFE_DIVIDE(COUNT(DISTINCT IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 6 DAY), user_id, NULL)), COUNT(DISTINCT user_id)), NULL) AS day_7_payment_rate,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 13 DAY), SAFE_DIVIDE(COUNT(DISTINCT IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 13 DAY), user_id, NULL)), COUNT(DISTINCT user_id)), NULL) AS day_14_payment_rate,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 29 DAY), SAFE_DIVIDE(COUNT(DISTINCT IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 29 DAY), user_id, NULL)), COUNT(DISTINCT user_id)), NULL) AS day_30_payment_rate,
  IF(DATE '2026-09-02' >= cohort_date, SAFE_DIVIDE(SUM(IF(payment_date <= cohort_date, order_amount, 0)), COUNT(DISTINCT user_id)), NULL) AS day_1_arpu,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 6 DAY), SAFE_DIVIDE(SUM(IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 6 DAY), order_amount, 0)), COUNT(DISTINCT user_id)), NULL) AS day_7_arpu,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 13 DAY), SAFE_DIVIDE(SUM(IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 13 DAY), order_amount, 0)), COUNT(DISTINCT user_id)), NULL) AS day_14_arpu,
  IF(DATE '2026-09-02' >= DATE_ADD(cohort_date, INTERVAL 29 DAY), SAFE_DIVIDE(SUM(IF(payment_date <= DATE_ADD(cohort_date, INTERVAL 29 DAY), order_amount, 0)), COUNT(DISTINCT user_id)), NULL) AS day_30_arpu,
  DATE '2026-09-02' AS data_cutoff_date
FROM lifecycle
GROUP BY cohort_date
HAVING COUNT(DISTINCT user_id) >= 10
ORDER BY cohort_date;
