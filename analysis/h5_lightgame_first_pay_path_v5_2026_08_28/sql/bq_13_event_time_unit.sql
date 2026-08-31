SELECT
  source,
  min_length,
  max_length,
  min_numeric_time,
  max_numeric_time
FROM (
  SELECT
    'ORDER' AS source,
    MIN(LENGTH(time)) AS min_length,
    MAX(LENGTH(time)) AS max_length,
    MIN(SAFE_CAST(time AS INT64)) AS min_numeric_time,
    MAX(SAFE_CAST(time AS INT64)) AS max_numeric_time
  FROM `wajenigeria.origin_hfyl.view_metaevent_order`
  WHERE app_id = 90006 AND target_day = DATE '2026-07-14'

  UNION ALL

  SELECT
    'GAMESTART',
    MIN(LENGTH(time)),
    MAX(LENGTH(time)),
    MIN(SAFE_CAST(time AS INT64)),
    MAX(SAFE_CAST(time AS INT64))
  FROM `wajenigeria.origin_hfyl.view_metaevent_gamestart`
  WHERE app_id = 90006 AND target_day = DATE '2026-07-14'
);

