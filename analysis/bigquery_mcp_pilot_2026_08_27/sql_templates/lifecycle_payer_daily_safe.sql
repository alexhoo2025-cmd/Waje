-- TEMPLATE ONLY: activate the authorized view before execution.
SELECT
  cohort_date,
  lifecycle_day,
  payer_segment,
  surface_type,
  package_id,
  channel,
  SUM(cohort_users) AS cohort_users,
  SUM(active_users) AS active_users,
  SUM(payer_users) AS payer_users,
  SUM(payment_amount) AS payment_amount,
  MAX(data_cutoff) AS data_cutoff,
  LOGICAL_AND(complete_day) AS complete_day,
  LOGICAL_AND(mature_cohort) AS mature_cohort
FROM `wajenigeria.agent_analytics.vw_lifecycle_payer_daily_safe`
WHERE cohort_date BETWEEN @start_date AND @end_date
GROUP BY cohort_date, lifecycle_day, payer_segment, surface_type, package_id, channel
HAVING SUM(cohort_users) >= 10
LIMIT 3000;
