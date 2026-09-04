-- Aggregate-only full-August H5 PAWAJEBETH5 payer segmentation.
-- This is a cost-controlled replacement attempt for non-additive half-month windows.
WITH user_profile AS (
  SELECT
    user_id,
    SAFE.PARSE_DATE('%Y-%m-%d', first_account_date) AS register_date,
    first_pay_date
  FROM `wajenigeria.origin_hfyl.user_info_all`
  WHERE first_client_type = 3
    AND first_package_name = 'com.wajegame.web'
    AND download_channel = 'PAWAJEBETH5'
), raw_orders AS (
  SELECT
    target_day AS payment_date,
    target_day AS cohort_date,
    user_id,
    order_no,
    pay_amount
  FROM `wajenigeria.origin_hfyl.view_event_pay`
  WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
    AND event_type = 'order_success'
), successful_orders AS (
  SELECT payment_date, user_id, order_no, MAX(COALESCE(pay_amount, 0)) AS order_amount
  FROM raw_orders
  WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
    AND user_id IS NOT NULL AND user_id != '' AND order_no IS NOT NULL AND order_no != ''
  GROUP BY payment_date, user_id, order_no
), payer_month AS (
  SELECT
    successful_orders.user_id,
    user_profile.register_date,
    user_profile.first_pay_date,
    SUM(successful_orders.order_amount) AS pay_amount,
    SUM(IF(successful_orders.payment_date = user_profile.first_pay_date, successful_orders.order_amount, 0)) AS first_payment_amount,
    SUM(IF(successful_orders.payment_date > user_profile.first_pay_date, successful_orders.order_amount, 0)) AS repeat_payment_amount,
    LOGICAL_OR(successful_orders.payment_date = user_profile.first_pay_date) AS has_first_payment,
    LOGICAL_OR(successful_orders.payment_date > user_profile.first_pay_date) AS has_repeat_payment
  FROM successful_orders
  JOIN user_profile USING (user_id)
  GROUP BY successful_orders.user_id, register_date, first_pay_date
)
SELECT
  '2026-08' AS payment_month,
  COUNT(*) AS unique_paying_users,
  COUNTIF(register_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31') AS unique_new_registered_payers,
  COUNTIF(has_first_payment) AS unique_first_payers,
  COUNTIF(first_pay_date < DATE '2026-08-01') AS unique_old_payers_at_month_start,
  COUNTIF(has_repeat_payment) AS unique_repeat_payers_after_first_payment,
  SUM(pay_amount) AS pay_amount,
  SUM(first_payment_amount) AS first_payment_amount,
  SUM(repeat_payment_amount) AS repeat_payment_amount,
  SAFE_DIVIDE(SUM(pay_amount), COUNT(*)) AS payer_arppu,
  SAFE_DIVIDE(SUM(repeat_payment_amount), COUNTIF(has_repeat_payment)) AS repeat_payer_arppu
FROM payer_month
WHERE first_pay_date IS NOT NULL;
