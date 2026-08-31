-- Repeat cash recharge after first pay, aggregated by path group.
WITH light_game_map AS (
  SELECT 'limbo' AS game_value UNION ALL SELECT '9008' UNION ALL SELECT 'keno' UNION ALL
  SELECT 'color dice' UNION ALL SELECT 'colorgame' UNION ALL SELECT '9003' UNION ALL
  SELECT 'hilo' UNION ALL SELECT '9011' UNION ALL SELECT 'plinko'
), fp AS (
  SELECT
    gid,
    MIN(firstRechargeTime) AS first_pay_time,
    CASE WHEN MIN(firstRechargeTime) < UNIX_TIMESTAMP('2026-07-14 00:00:00') THEN 'pre' ELSE 'post' END AS period
  FROM risk_recharge
  WHERE firstRechargeTime >= UNIX_TIMESTAMP('2026-06-16 00:00:00')
    AND firstRechargeTime < UNIX_TIMESTAMP('2026-08-11 00:00:00')
  GROUP BY gid
), first_game AS (
  SELECT
    fp.gid,
    MIN(CASE WHEN gr.time < fp.first_pay_time THEN gr.time END) AS pre_time,
    MIN(CASE WHEN gr.time >= fp.first_pay_time THEN gr.time END) AS post_time
  FROM fp
  LEFT JOIN game_record gr
    ON gr.user_id = fp.gid
   AND gr.time >= fp.first_pay_time - 30 * 86400
   AND gr.time < fp.first_pay_time + 7 * 86400
   AND LOWER(TRIM(gr.game)) IN (SELECT game_value FROM light_game_map)
  GROUP BY fp.gid
), cohort AS (
  SELECT
    fp.*,
    CASE
      WHEN fg.pre_time IS NOT NULL THEN '付费前已玩'
      WHEN fg.post_time < fp.first_pay_time + 30 * 60 THEN '付费后立即玩'
      WHEN fg.post_time < fp.first_pay_time + 86400 THEN '付费后当天玩'
      WHEN fg.post_time < fp.first_pay_time + 7 * 86400 THEN '付费后延迟玩'
      WHEN fg.post_time IS NULL THEN '付费后7天未玩'
      ELSE '时序不确定'
    END AS path_group
  FROM fp
  LEFT JOIN first_game fg ON fg.gid = fp.gid
), orders AS (
  SELECT
    c.gid,
    c.period,
    c.path_group,
    SUM(o.time > c.first_pay_time AND o.time < c.first_pay_time + 86400) > 0 AS repeat_pay_d1,
    SUM(o.time > c.first_pay_time AND o.time < c.first_pay_time + 3 * 86400) > 0 AS repeat_pay_d3,
    SUM(o.time > c.first_pay_time AND o.time < c.first_pay_time + 7 * 86400) > 0 AS repeat_pay_d7,
    SUM(o.time > c.first_pay_time AND o.time < c.first_pay_time + 15 * 86400) > 0 AS repeat_pay_d15
  FROM cohort c
  LEFT JOIN order_log o
    ON o.gid = c.gid
   AND o.type = 1
   AND o.status = 3
   AND o.time > c.first_pay_time
   AND o.time < c.first_pay_time + 15 * 86400
  GROUP BY c.gid, c.period, c.path_group
)
SELECT
  period,
  path_group,
  COUNT(*) AS first_pay_users,
  ROUND(SUM(repeat_pay_d1) / COUNT(*), 4) AS repeat_pay_rate_d1,
  ROUND(SUM(repeat_pay_d3) / COUNT(*), 4) AS repeat_pay_rate_d3,
  ROUND(SUM(repeat_pay_d7) / COUNT(*), 4) AS repeat_pay_rate_d7,
  ROUND(SUM(repeat_pay_d15) / COUNT(*), 4) AS repeat_pay_rate_d15
FROM orders
GROUP BY period, path_group
HAVING COUNT(*) >= 30
ORDER BY period, first_pay_users DESC;
