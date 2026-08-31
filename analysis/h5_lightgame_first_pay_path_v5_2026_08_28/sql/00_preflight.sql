-- V5 preflight. Run each SELECT separately in Metabase, read-only.
-- Do not save raw user rows. All outputs are metadata or aggregate groups.

-- A. Session timezone and Unix conversion.
SELECT
  @@session.time_zone AS session_time_zone,
  @@system_time_zone AS system_time_zone,
  NOW() AS session_now,
  UTC_TIMESTAMP() AS utc_now,
  TIMESTAMPDIFF(MINUTE, UTC_TIMESTAMP(), NOW()) AS session_utc_offset_minutes;

-- B. First-pay uniqueness and order reconciliation by 28-day period.
WITH fp AS (
  SELECT
    gid,
    MIN(firstRechargeTime) AS first_pay_time,
    COUNT(*) AS risk_first_pay_rows
  FROM risk_recharge
  WHERE firstRechargeTime >= UNIX_TIMESTAMP('2026-06-16 00:00:00')
    AND firstRechargeTime < UNIX_TIMESTAMP('2026-08-11 00:00:00')
  GROUP BY gid
), matched AS (
  SELECT
    fp.gid,
    fp.first_pay_time,
    fp.risk_first_pay_rows,
    COUNT(o.id) AS matching_success_orders
  FROM fp
  LEFT JOIN order_log o
    ON o.gid = fp.gid
   AND o.type = 1
   AND o.status = 3
   AND o.time >= fp.first_pay_time - 86400
   AND o.time < fp.first_pay_time + 86400
  GROUP BY fp.gid, fp.first_pay_time, fp.risk_first_pay_rows
)
SELECT
  CASE WHEN first_pay_time < UNIX_TIMESTAMP('2026-07-14 00:00:00') THEN 'pre' ELSE 'post' END AS period,
  COUNT(*) AS first_pay_users,
  SUM(risk_first_pay_rows > 1) AS duplicate_risk_rows_users,
  SUM(matching_success_orders > 0) AS matched_success_order_users,
  ROUND(SUM(matching_success_orders > 0) / COUNT(*), 4) AS order_match_rate
FROM matched
GROUP BY period;

-- C. Safe channel/package vocabulary. Values are business categories, not user rows.
SELECT
  COALESCE(NULLIF(u.reg_package, ''), '[blank]') AS reg_package,
  COALESCE(NULLIF(u.reg_channel, ''), '[blank]') AS reg_channel,
  COALESCE(NULLIF(u.reg_sub_channel, ''), '[blank]') AS reg_sub_channel,
  COALESCE(NULLIF(a.ad_channel, ''), '[blank]') AS ad_channel,
  COUNT(*) AS users
FROM risk_recharge r
JOIN uc_user u ON u.user_id = r.gid
LEFT JOIN uc_user_adchannel a ON a.gid = r.gid
WHERE r.firstRechargeTime >= UNIX_TIMESTAMP('2026-06-16 00:00:00')
  AND r.firstRechargeTime < UNIX_TIMESTAMP('2026-08-11 00:00:00')
GROUP BY reg_package, reg_channel, reg_sub_channel, ad_channel
HAVING COUNT(*) >= 30
ORDER BY users DESC;

-- D. Game value mapping and scale. Review before enabling the light-game filter.
SELECT
  LOWER(TRIM(game)) AS game_value,
  COUNT(*) AS records,
  COUNT(DISTINCT user_id) AS users,
  ROUND(SUM(bet) / 100.0, 2) AS bet_amount,
  MIN(FROM_UNIXTIME(time)) AS first_seen,
  MAX(FROM_UNIXTIME(time)) AS last_seen
FROM game_record
WHERE time >= UNIX_TIMESTAMP('2026-06-16 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-08-26 00:00:00')
GROUP BY LOWER(TRIM(game))
HAVING COUNT(DISTINCT user_id) >= 30
ORDER BY users DESC;

-- E. Candidate grain check: number of records per user/game/day.
WITH g AS (
  SELECT
    user_id,
    LOWER(TRIM(game)) AS game_value,
    DATE(FROM_UNIXTIME(time)) AS game_day,
    COUNT(*) AS records,
    SUM(bet) AS bet_cent,
    SUM(reward) AS reward_cent
  FROM game_record
  WHERE time >= UNIX_TIMESTAMP('2026-07-01 00:00:00')
    AND time < UNIX_TIMESTAMP('2026-08-26 00:00:00')
  GROUP BY user_id, LOWER(TRIM(game)), DATE(FROM_UNIXTIME(time))
)
SELECT
  game_value,
  COUNT(*) AS user_game_days,
  ROUND(AVG(records), 2) AS avg_records_per_user_game_day,
  MAX(records) AS max_records_per_user_game_day,
  SUM(bet_cent = 0 AND reward_cent = 0) AS zero_value_user_game_days
FROM g
GROUP BY game_value
HAVING COUNT(*) >= 30
ORDER BY user_game_days DESC;

-- F. User-action enum profile. Do not interpret retention until enum owner confirms act values.
SELECT
  act,
  COUNT(*) AS records,
  COUNT(DISTINCT user_id) AS users,
  MIN(FROM_UNIXTIME(time)) AS first_seen,
  MAX(FROM_UNIXTIME(time)) AS last_seen
FROM stat_user_action
WHERE time >= UNIX_TIMESTAMP('2026-06-16 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-08-26 00:00:00')
GROUP BY act
HAVING COUNT(DISTINCT user_id) >= 30
ORDER BY users DESC;

