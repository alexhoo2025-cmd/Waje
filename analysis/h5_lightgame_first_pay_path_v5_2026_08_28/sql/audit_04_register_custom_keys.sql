SELECT
  key,
  COUNT(*) AS populated_events
FROM (
  SELECT custom, target_day AS event_date
  FROM `wajenigeria.origin_hfyl.view_metaevent_register`
  WHERE app_id = 90006
    AND target_day BETWEEN DATE '2026-06-16' AND DATE '2026-08-10'
),
UNNEST(IFNULL(JSON_KEYS(SAFE.PARSE_JSON(custom)), [])) AS key
WHERE event_date BETWEEN DATE '2026-06-16' AND DATE '2026-08-10'
GROUP BY key
ORDER BY populated_events DESC
LIMIT 100;
