-- One-day, one-batch, aggregate-only UID Log audit for the Excel-selected top 30.
WITH selected_users AS (
  SELECT user_id
  FROM UNNEST(@target_user_ids) AS user_id
),
events AS (
  SELECT
    e.user_id,
    e.asset_id,
    e.asset_source_id,
    e.change_type,
    COALESCE(NULLIF(e.asset_method, ''), '(空)') AS asset_method,
    COALESCE(NULLIF(e.play_id, ''), '(空)') AS play_marker,
    COALESCE(NULLIF(e.log_event_type, ''), '(空)') AS log_marker,
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
    asset_source_id,
    change_type,
    asset_method,
    play_marker,
    log_marker,
    change_count,
    change_balance,
    event_time,
    CASE
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(play_marker, ' ', log_marker)), r'充值|recharge|charge') THEN '充值'
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(play_marker, ' ', log_marker)), r'提现|withdraw|audit') THEN '提现'
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(play_marker, ' ', log_marker)), r'下注|\bbet\b') THEN '下注'
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(play_marker, ' ', log_marker)), r'返还|退款|refund|return|结算|派奖|settle|rchip|wcash') THEN '返还/结算'
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(play_marker, ' ', log_marker)), r'奖励|奖品|任务|签到|reward|prize|bonus') THEN '奖励'
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(play_marker, ' ', log_marker)), r'转|兑换|exchange|transfer') THEN '转换'
      ELSE '其他/待映射'
    END AS reason_group,
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
    '来源标识' AS section,
    CONCAT('asset_id=', CAST(asset_id AS STRING)) AS asset_key,
    CONCAT(
      reason_group,
      ' | source=', COALESCE(CAST(asset_source_id AS STRING), '(空)'),
      ' | change_type=', COALESCE(CAST(change_type AS STRING), '(空)'),
      ' | method=', SUBSTR(asset_method, 1, 20),
      ' | play=', SUBSTR(play_marker, 1, 60),
      ' | log=', SUBSTR(log_marker, 1, 40)
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
  GROUP BY asset_id, reason_group, asset_source_id, change_type, asset_method, play_marker, log_marker
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
