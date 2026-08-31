SELECT
  json_key,
  COUNT(*) AS events_with_key,
  APPROX_COUNT_DISTINCT(user_id) AS users
FROM `wajenigeria.origin_hfyl.view_metaevent_gamestart`,
UNNEST(IFNULL(JSON_KEYS(SAFE.PARSE_JSON(custom)), [])) AS json_key
WHERE app_id = 90006
  AND target_day BETWEEN DATE '2026-07-14' AND DATE '2026-07-27'
GROUP BY json_key
HAVING users >= 30
ORDER BY users DESC;

