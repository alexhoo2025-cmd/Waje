-- Aggregate-only old-payer validation using full-profile first-pay history and deduplicated successful orders.
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
  WHERE cohort_date BETWEEN DATE '2026-08-16' AND DATE '2026-08-31'
    AND order_no IS NOT NULL
    AND order_no != ''
  GROUP BY cohort_date, user_id, order_no
), user_profile AS (
  SELECT
    user_id,
    SAFE.PARSE_DATE('%Y-%m-%d', first_account_date) AS register_date,
    first_pay_date AS first_pay_date,
    ANY_VALUE(first_package_name) AS first_package_name,
    ANY_VALUE(download_channel) AS download_channel,
    ANY_VALUE(first_client_type) AS first_client_type
  FROM `wajenigeria.origin_hfyl.user_info_all`
  GROUP BY user_id, register_date, first_pay_date
), payer_day AS (
  SELECT
    successful_orders.cohort_date,
    successful_orders.user_id,
    SUM(successful_orders.order_amount) AS pay_amount,
    user_profile.register_date,
    user_profile.first_pay_date,
    user_profile.first_package_name,
    user_profile.download_channel,
    user_profile.first_client_type
  FROM successful_orders
  JOIN user_profile USING (user_id)
  GROUP BY successful_orders.cohort_date, successful_orders.user_id, register_date, first_pay_date, first_package_name, download_channel, first_client_type
)
SELECT
  cohort_date AS target_day,
  CASE first_client_type WHEN 3 THEN 'H5' WHEN 2 THEN 'Android' WHEN 1 THEN 'iOS' ELSE 'Unknown' END AS platform,
  COALESCE(NULLIF(first_package_name, ''), '(blank)') AS first_package_name,
  COALESCE(NULLIF(download_channel, ''), '(blank)') AS download_channel,
  COUNT(*) AS paying_users,
  COUNTIF(register_date = cohort_date) AS new_registered_payers,
  COUNTIF(first_pay_date = cohort_date) AS historical_first_payers,
  COUNTIF(first_pay_date < cohort_date) AS old_payers_excluding_first_pay,
  SUM(pay_amount) AS pay_amount,
  SUM(IF(register_date = cohort_date, pay_amount, 0)) AS new_registered_pay_amount,
  SUM(IF(first_pay_date = cohort_date, pay_amount, 0)) AS historical_first_pay_amount,
  SUM(IF(first_pay_date < cohort_date, pay_amount, 0)) AS old_payer_pay_amount
FROM payer_day
GROUP BY cohort_date, platform, first_package_name, download_channel
HAVING COUNT(*) >= 10
ORDER BY target_day, paying_users DESC
LIMIT 3000;
