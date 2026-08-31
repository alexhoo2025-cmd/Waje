-- T0-D15 gameplay depth by path group and elapsed day.
-- Uses game_record as the candidate settled-round fact; publish only after grain validation.
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
), pre_post_touch AS (
  SELECT
    fp.gid,
    MIN(CASE WHEN gr.time < fp.first_pay_time THEN gr.time END) AS pre_time,
    MIN(CASE WHEN gr.time >= fp.first_pay_time THEN gr.time END) AS post_time
  FROM fp
  LEFT JOIN game_record gr
    ON gr.user_id = fp.gid
   AND gr.time >= fp.first_pay_time - 30 * 86400
   AND gr.time < fp.first_pay_time + 15 * 86400
   AND LOWER(TRIM(gr.game)) IN (SELECT game_value FROM light_game_map)
  GROUP BY fp.gid
), cohort AS (
  SELECT
    fp.*,
    CASE
      WHEN t.pre_time IS NOT NULL THEN '付费前已玩'
      WHEN t.post_time < fp.first_pay_time + 30 * 60 THEN '付费后立即玩'
      WHEN t.post_time < fp.first_pay_time + 86400 THEN '付费后当天玩'
      WHEN t.post_time < fp.first_pay_time + 7 * 86400 THEN '付费后延迟玩'
      WHEN t.post_time IS NULL THEN '付费后7天未玩'
      ELSE '时序不确定'
    END AS path_group
  FROM fp
  LEFT JOIN pre_post_touch t ON t.gid = fp.gid
), user_day AS (
  SELECT
    c.gid,
    c.period,
    c.path_group,
    FLOOR((gr.time - c.first_pay_time) / 86400) AS day_since_first_pay,
    COUNT(*) AS rounds,
    SUM(gr.bet) AS bet_cent,
    SUM(gr.reward) AS reward_cent
  FROM cohort c
  JOIN game_record gr
    ON gr.user_id = c.gid
   AND gr.time >= c.first_pay_time
   AND gr.time < c.first_pay_time + 16 * 86400
   AND LOWER(TRIM(gr.game)) IN (SELECT game_value FROM light_game_map)
  GROUP BY c.gid, c.period, c.path_group, FLOOR((gr.time - c.first_pay_time) / 86400)
), denominators AS (
  SELECT period, path_group, COUNT(*) AS first_pay_users
  FROM cohort
  GROUP BY period, path_group
)
SELECT
  ud.period,
  ud.path_group,
  ud.day_since_first_pay,
  d.first_pay_users,
  COUNT(*) AS replay_users,
  ROUND(COUNT(*) / d.first_pay_users, 4) AS replay_rate,
  SUM(ud.rounds) AS rounds,
  ROUND(SUM(ud.rounds) / COUNT(*), 2) AS avg_rounds_per_replay_user,
  ROUND(SUM(ud.bet_cent) / 100.0, 2) AS bet_amount,
  ROUND(SUM(ud.reward_cent) / 100.0, 2) AS reward_amount
FROM user_day ud
JOIN denominators d ON d.period = ud.period AND d.path_group = ud.path_group
WHERE ud.day_since_first_pay BETWEEN 0 AND 15
GROUP BY ud.period, ud.path_group, ud.day_since_first_pay, d.first_pay_users
HAVING d.first_pay_users >= 30
ORDER BY ud.period, ud.path_group, ud.day_since_first_pay;
