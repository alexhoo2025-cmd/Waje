-- One-day, one-batch, aggregate-only UID Log audit for the Excel-selected top 30.
WITH selected_users AS (
  SELECT user_id
  FROM UNNEST(@target_user_ids) AS user_id
),
events AS (
  SELECT
    e.user_id,
    e.asset_id,
    e.change_type,
    COALESCE(NULLIF(e.asset_method, ''), '(空)') AS asset_method,
    e.change_count,
    e.change_balance,
    COALESCE(
      SAFE_CAST(e.local_time AS DATETIME),
      SAFE_CAST(e.time AS DATETIME),
      SAFE_CAST(e.server_time AS DATETIME),
      CASE
        WHEN REGEXP_CONTAINS(e.time, r'^\d{13}$') THEN DATETIME(TIMESTAMP_MILLIS(CAST(e.time AS INT64)), 'Africa/Lagos')
        WHEN REGEXP_CONTAINS(e.time, r'^\d{10}$') THEN DATETIME(TIMESTAMP_SECONDS(CAST(e.time AS INT64)), 'Africa/Lagos')
      END,
      CASE
        WHEN REGEXP_CONTAINS(e.local_time, r'^\d{13}$') THEN DATETIME(TIMESTAMP_MILLIS(CAST(e.local_time AS INT64)), 'Africa/Lagos')
        WHEN REGEXP_CONTAINS(e.local_time, r'^\d{10}$') THEN DATETIME(TIMESTAMP_SECONDS(CAST(e.local_time AS INT64)), 'Africa/Lagos')
      END
    ) AS event_time
  FROM `wajenigeria.origin_hfyl.realtime_event_server` AS e
  JOIN selected_users AS s USING (user_id)
  WHERE e.target_day = DATE '2026-09-10'
    AND e.app_id = 90006
    AND e.event_type = 'ASSET'
),
enriched AS (
  SELECT
    user_id,
    asset_id,
    change_type,
    asset_method,
    change_count,
    change_balance,
    event_time,
    CASE
      WHEN event_time IS NULL THEN '时间未知'
      WHEN EXTRACT(HOUR FROM event_time) < 6 THEN '00–05时'
      WHEN EXTRACT(HOUR FROM event_time) < 12 THEN '06–11时'
      WHEN EXTRACT(HOUR FROM event_time) < 18 THEN '12–17时'
      ELSE '18–23时'
    END AS time_bucket
  FROM events
),
overall AS (
  SELECT
    '总体' AS section,
    '全部资产' AS asset_key,
    '全部原因' AS reason_key,
    '全天' AS time_key,
    COUNT(DISTINCT user_id) AS user_count,
    COUNT(*) AS event_count,
    SUM(IF(change_count > 0, change_count, 0)) AS inflow,
    SUM(IF(change_count < 0, -change_count, 0)) AS outflow,
    SUM(change_count) AS net_change,
    MIN(change_balance) AS min_after_balance,
    MAX(change_balance) AS max_after_balance,
    MIN(event_time) AS first_event_time,
    MAX(event_time) AS last_event_time
  FROM enriched
),
asset_rollup AS (
  SELECT
    '资产' AS section,
    CONCAT('asset_id=', CAST(asset_id AS STRING)) AS asset_key,
    '全部原因' AS reason_key,
    '全天' AS time_key,
    COUNT(DISTINCT user_id) AS user_count,
    COUNT(*) AS event_count,
    SUM(IF(change_count > 0, change_count, 0)) AS inflow,
    SUM(IF(change_count < 0, -change_count, 0)) AS outflow,
    SUM(change_count) AS net_change,
    MIN(change_balance) AS min_after_balance,
    MAX(change_balance) AS max_after_balance,
    MIN(event_time) AS first_event_time,
    MAX(event_time) AS last_event_time
  FROM enriched
  GROUP BY asset_id
  HAVING COUNT(DISTINCT user_id) >= 10
),
reason_rollup AS (
  SELECT
    '变动代码' AS section,
    CONCAT('asset_id=', CAST(asset_id AS STRING)) AS asset_key,
    CONCAT(
      'change_type=', COALESCE(CAST(change_type AS STRING), '(空)'),
      ' | direction=', SUBSTR(asset_method, 1, 20)
    ) AS reason_key,
    '全天' AS time_key,
    COUNT(DISTINCT user_id) AS user_count,
    COUNT(*) AS event_count,
    SUM(IF(change_count > 0, change_count, 0)) AS inflow,
    SUM(IF(change_count < 0, -change_count, 0)) AS outflow,
    SUM(change_count) AS net_change,
    MIN(change_balance) AS min_after_balance,
    MAX(change_balance) AS max_after_balance,
    MIN(event_time) AS first_event_time,
    MAX(event_time) AS last_event_time
  FROM enriched
  GROUP BY asset_id, change_type, asset_method
  HAVING COUNT(DISTINCT user_id) >= 10
),
time_rollup AS (
  SELECT
    '时段' AS section,
    CONCAT('asset_id=', CAST(asset_id AS STRING)) AS asset_key,
    '全部原因' AS reason_key,
    time_bucket AS time_key,
    COUNT(DISTINCT user_id) AS user_count,
    COUNT(*) AS event_count,
    SUM(IF(change_count > 0, change_count, 0)) AS inflow,
    SUM(IF(change_count < 0, -change_count, 0)) AS outflow,
    SUM(change_count) AS net_change,
    MIN(change_balance) AS min_after_balance,
    MAX(change_balance) AS max_after_balance,
    MIN(event_time) AS first_event_time,
    MAX(event_time) AS last_event_time
  FROM enriched
  GROUP BY asset_id, time_bucket
  HAVING COUNT(DISTINCT user_id) >= 10
)
SELECT section, asset_key, reason_key, time_key, user_count, event_count, inflow, outflow, net_change, min_after_balance, max_after_balance, first_event_time, last_event_time FROM overall
UNION ALL SELECT section, asset_key, reason_key, time_key, user_count, event_count, inflow, outflow, net_change, min_after_balance, max_after_balance, first_event_time, last_event_time FROM asset_rollup
UNION ALL SELECT section, asset_key, reason_key, time_key, user_count, event_count, inflow, outflow, net_change, min_after_balance, max_after_balance, first_event_time, last_event_time FROM reason_rollup
UNION ALL SELECT section, asset_key, reason_key, time_key, user_count, event_count, inflow, outflow, net_change, min_after_balance, max_after_balance, first_event_time, last_event_time FROM time_rollup
ORDER BY section, asset_key, reason_key, time_key
LIMIT 3000;
