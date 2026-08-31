-- Design contract only. Replace the approved view name after the server-fact owner registers it.
-- This script must remain blocked until an approved aggregate source is available.
SELECT
  metric_date_lagos,
  endpoint,
  stage,
  attempt_count,
  success_count,
  complete_day,
  quality_status,
  data_cutoff_at
FROM `wajenigeria.agent_analytics.vw_approved_server_core_funnel_daily`
WHERE metric_date_lagos BETWEEN DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 30 DAY) AND DATE_SUB(CURRENT_DATE('Africa/Lagos'), INTERVAL 1 DAY)
ORDER BY metric_date_lagos, endpoint, stage
LIMIT 3000;
