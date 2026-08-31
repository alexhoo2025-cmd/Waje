-- TEMPLATE ONLY: activate the authorized view before execution.
SELECT
  event_date,
  flow_type,
  surface_type,
  package_id,
  SUM(triggered_users) AS triggered_users,
  SUM(idv_started_users) AS idv_started_users,
  SUM(face_requested_users) AS face_requested_users,
  SUM(face_succeeded_users) AS face_succeeded_users,
  SUM(withdraw_succeeded_users) AS withdraw_succeeded_users,
  MAX(data_cutoff) AS data_cutoff,
  LOGICAL_AND(complete_day) AS complete_day
FROM `wajenigeria.agent_analytics.vw_kyc_daily_safe`
WHERE event_date BETWEEN @start_date AND @end_date
GROUP BY event_date, flow_type, surface_type, package_id
HAVING SUM(triggered_users) >= 10
LIMIT 3000;
