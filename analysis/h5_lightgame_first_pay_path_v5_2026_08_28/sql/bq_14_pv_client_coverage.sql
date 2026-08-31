SELECT
  client_type,
  COALESCE(NULLIF(lib, ''), '[blank]') AS lib,
  COALESCE(NULLIF(browser, ''), '[blank]') AS browser,
  COALESCE(NULLIF(os, ''), '[blank]') AS os,
  COALESCE(NULLIF(package_channel, ''), '[blank]') AS package_channel,
  COUNT(*) AS events,
  APPROX_COUNT_DISTINCT(user_id) AS users
FROM `wajenigeria.origin_hfyl.view_metaevent_pv`
WHERE app_id = 90006
  AND target_day = DATE '2026-07-14'
GROUP BY client_type, lib, browser, os, package_channel
HAVING users >= 30
ORDER BY users DESC;

