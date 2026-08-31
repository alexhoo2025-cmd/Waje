SELECT
  client_type,
  COALESCE(NULLIF(package_channel, ''), '[blank]') AS package_channel,
  COALESCE(NULLIF(is_success, ''), '[blank]') AS is_success,
  is_first_buy,
  COUNT(*) AS events,
  APPROX_COUNT_DISTINCT(user_id) AS users,
  COUNTIF(SAFE_CAST(time AS INT64) IS NOT NULL) AS numeric_time_events,
  MIN(target_day) AS first_day,
  MAX(target_day) AS last_day
FROM `wajenigeria.origin_hfyl.view_metaevent_order`
WHERE app_id = 90006
  AND target_day BETWEEN DATE '2026-07-14' AND DATE '2026-08-10'
GROUP BY client_type, package_channel, is_success, is_first_buy
HAVING users >= 30
ORDER BY events DESC;

