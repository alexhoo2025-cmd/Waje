-- Aggregate-only unique payer lifecycle template.
-- Replace the two date literals as one inclusive calendar-month window before execution.
WITH raw_orders AS (
  SELECT
    target_day AS cohort_date,
    user_id,
    order_no,
    pay_amount
  FROM `wajenigeria.origin_hfyl.view_event_pay`
  WHERE event_type = 'order_success'
), successful_orders AS (
  SELECT
    cohort_date,
    user_id,
    order_no,
    MAX(COALESCE(pay_amount, 0)) AS order_amount
  FROM raw_orders
  WHERE cohort_date BETWEEN DATE '2026-06-01' AND DATE '2026-06-30'
    AND order_no IS NOT NULL
    AND order_no != ''
  GROUP BY cohort_date, user_id, order_no
), user_profile AS (
  SELECT
    user_id,
    SAFE.PARSE_DATE('%Y-%m-%d', first_account_date) AS register_date,
    first_pay_date,
    ANY_VALUE(first_package_name) AS first_package_name,
    ANY_VALUE(download_channel) AS download_channel,
    ANY_VALUE(first_client_type) AS first_client_type
  FROM `wajenigeria.origin_hfyl.user_info_all`
  GROUP BY user_id, register_date, first_pay_date
), payer_month AS (
  SELECT
    successful_orders.user_id,
    user_profile.register_date,
    user_profile.first_pay_date,
    user_profile.first_package_name,
    user_profile.download_channel,
    user_profile.first_client_type,
    SUM(successful_orders.order_amount) AS pay_amount,
    SUM(IF(successful_orders.cohort_date = user_profile.first_pay_date, successful_orders.order_amount, 0)) AS first_payment_amount,
    SUM(IF(successful_orders.cohort_date > user_profile.first_pay_date, successful_orders.order_amount, 0)) AS repeat_payment_amount,
    LOGICAL_OR(successful_orders.cohort_date = user_profile.first_pay_date) AS has_first_payment,
    LOGICAL_OR(successful_orders.cohort_date > user_profile.first_pay_date) AS has_repeat_payment
  FROM successful_orders
  JOIN user_profile USING (user_id)
  GROUP BY successful_orders.user_id, register_date, first_pay_date, first_package_name, download_channel, first_client_type
)
SELECT
  CASE first_client_type WHEN 3 THEN 'H5' WHEN 2 THEN 'Android' WHEN 1 THEN 'iOS' ELSE 'Unknown' END AS platform,
  COALESCE(NULLIF(first_package_name, ''), '(blank)') AS first_package_name,
  COALESCE(NULLIF(download_channel, ''), '(blank)') AS download_channel,
  COUNT(*) AS unique_paying_users,
  COUNTIF(register_date BETWEEN DATE '2026-06-01' AND DATE '2026-06-30') AS unique_new_registered_payers,
  COUNTIF(has_first_payment) AS unique_first_payers,
  COUNTIF(has_repeat_payment) AS unique_repeat_payers_excluding_first_payment,
  SUM(pay_amount) AS pay_amount,
  SUM(first_payment_amount) AS first_payment_amount,
  SUM(repeat_payment_amount) AS repeat_payment_amount,
  SAFE_DIVIDE(SUM(pay_amount), COUNT(*)) AS payer_arppu,
  SAFE_DIVIDE(SUM(repeat_payment_amount), COUNTIF(has_repeat_payment)) AS repeat_payer_arppu
FROM payer_month
GROUP BY platform, first_package_name, download_channel
HAVING COUNT(*) >= 10
ORDER BY unique_paying_users DESC
LIMIT 3000;
