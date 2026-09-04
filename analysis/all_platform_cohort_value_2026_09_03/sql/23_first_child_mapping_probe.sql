-- Aggregate-only probe of first_child values among August H5 successful payers.
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
  WHERE cohort_date BETWEEN DATE '2026-08-01' AND DATE '2026-08-31'
    AND order_no IS NOT NULL
    AND order_no != ''
  GROUP BY cohort_date, user_id, order_no
), user_profile AS (
  SELECT
    user_id,
    ANY_VALUE(first_package_name) AS first_package_name,
    ANY_VALUE(first_child) AS first_child,
    ANY_VALUE(first_client_type) AS first_client_type
  FROM `wajenigeria.origin_hfyl.user_info_all`
  GROUP BY user_id
)
SELECT
  COALESCE(NULLIF(first_child, ''), '(blank)') AS first_child,
  COUNT(DISTINCT successful_orders.user_id) AS unique_paying_users,
  SUM(successful_orders.order_amount) AS pay_amount
FROM successful_orders
JOIN user_profile USING (user_id)
WHERE first_package_name = 'com.wajegame.web'
  AND first_client_type = 3
GROUP BY first_child
HAVING COUNT(DISTINCT successful_orders.user_id) >= 10
ORDER BY unique_paying_users DESC
LIMIT 200;
