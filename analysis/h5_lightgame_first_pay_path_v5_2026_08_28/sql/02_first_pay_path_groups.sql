-- First-pay path layer. Uses settled game_record activity as a gameplay proxy.
-- Replace the light_game_map values only after 00_preflight confirms game_record.game vocabulary.
WITH light_game_map AS (
  SELECT 'limbo' AS game_value UNION ALL
  SELECT '9008' UNION ALL
  SELECT 'keno' UNION ALL
  SELECT 'color dice' UNION ALL
  SELECT 'colorgame' UNION ALL
  SELECT '9003' UNION ALL
  SELECT 'hilo' UNION ALL
  SELECT '9011' UNION ALL
  SELECT 'plinko'
), fp AS (
  SELECT
    r.gid,
    MIN(r.firstRechargeTime) AS first_pay_time,
    MAX(r.firstRechargeAmount) AS first_pay_amount_cent,
    CASE WHEN MIN(r.firstRechargeTime) < UNIX_TIMESTAMP('2026-07-14 00:00:00') THEN 'pre' ELSE 'post' END AS period
  FROM risk_recharge r
  WHERE r.firstRechargeTime >= UNIX_TIMESTAMP('2026-06-16 00:00:00')
    AND r.firstRechargeTime < UNIX_TIMESTAMP('2026-08-11 00:00:00')
  GROUP BY r.gid
), game_touch AS (
  SELECT
    fp.gid,
    MIN(CASE WHEN gr.time < fp.first_pay_time THEN gr.time END) AS first_pre_pay_game_time,
    MIN(CASE WHEN gr.time >= fp.first_pay_time THEN gr.time END) AS first_post_pay_game_time
  FROM fp
  LEFT JOIN game_record gr
    ON gr.user_id = fp.gid
   AND gr.time >= fp.first_pay_time - 30 * 86400
   AND gr.time < fp.first_pay_time + 7 * 86400
   AND LOWER(TRIM(gr.game)) IN (SELECT game_value FROM light_game_map)
  GROUP BY fp.gid
), classified AS (
  SELECT
    fp.gid,
    fp.period,
    fp.first_pay_time,
    fp.first_pay_amount_cent,
    CASE
      WHEN gt.first_pre_pay_game_time IS NOT NULL THEN '付费前已玩'
      WHEN gt.first_post_pay_game_time < fp.first_pay_time + 30 * 60 THEN '付费后立即玩'
      WHEN gt.first_post_pay_game_time < fp.first_pay_time + 24 * 60 * 60 THEN '付费后当天玩'
      WHEN gt.first_post_pay_game_time < fp.first_pay_time + 7 * 86400 THEN '付费后延迟玩'
      WHEN gt.first_post_pay_game_time IS NULL THEN '付费后7天未玩'
      ELSE '时序不确定'
    END AS path_group,
    gt.first_post_pay_game_time
  FROM fp
  LEFT JOIN game_touch gt ON gt.gid = fp.gid
)
SELECT
  c.period,
  c.path_group,
  COUNT(*) AS first_pay_users,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY c.period), 4) AS user_share,
  ROUND(AVG(c.first_pay_amount_cent) / 100.0, 2) AS avg_first_pay_amount,
  ROUND(AVG(CASE WHEN c.first_post_pay_game_time IS NOT NULL
                 THEN c.first_post_pay_game_time - c.first_pay_time END) / 60.0, 1) AS avg_minutes_to_first_postpay_game
FROM classified c
GROUP BY c.period, c.path_group
HAVING COUNT(*) >= 30
ORDER BY c.period, first_pay_users DESC;
