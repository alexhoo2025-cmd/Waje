WITH profile_scope AS (
  SELECT
    CAST(`用户id` AS STRING) AS user_id
  FROM `wajenigeria.pubwaje.user_profiles`
  WHERE `设备类型` = 'Others'
    AND DATE(`首充日期`, 'Africa/Lagos') BETWEEN DATE '2026-06-16' AND DATE '2026-06-30'
), first_pay AS (
  SELECT
    o.user_id,
    MIN(TIMESTAMP_MILLIS(SAFE_CAST(o.time AS INT64))) AS first_pay_ts
  FROM `wajenigeria.origin_hfyl.view_metaevent_order` o
  JOIN profile_scope p USING (user_id)
  WHERE o.app_id = 90006
    AND o.target_day BETWEEN DATE '2026-06-16' AND DATE '2026-06-30'
    AND o.is_first_buy IS TRUE
    AND o.is_success = 'pay_success'
    AND SAFE_CAST(o.time AS INT64) IS NOT NULL
  GROUP BY o.user_id
), game_window AS (
  SELECT
    user_id,
    TIMESTAMP_MILLIS(SAFE_CAST(time AS INT64)) AS game_ts
  FROM `wajenigeria.origin_hfyl.view_metaevent_gamestart`
  WHERE app_id = 90006
    AND target_day BETWEEN DATE '2026-06-09' AND DATE '2026-07-07'
    AND SAFE_CAST(time AS INT64) IS NOT NULL
), per_user AS (
  SELECT
    fp.user_id,
    fp.first_pay_ts,
    COUNTIF(g.game_ts < fp.first_pay_ts AND g.game_ts >= TIMESTAMP_SUB(fp.first_pay_ts, INTERVAL 7 DAY)) > 0 AS played_pre_7d,
    MIN(IF(g.game_ts >= fp.first_pay_ts AND g.game_ts < TIMESTAMP_ADD(fp.first_pay_ts, INTERVAL 7 DAY), g.game_ts, NULL)) AS first_post_game_ts
  FROM first_pay fp
  LEFT JOIN game_window g USING (user_id)
  GROUP BY fp.user_id, fp.first_pay_ts
), classified AS (
  SELECT
    CASE
      WHEN played_pre_7d THEN '付费前7日已玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 30 MINUTE) THEN '付费后30分钟内玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 24 HOUR) THEN '付费后24小时内玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 7 DAY) THEN '付费后第2至7天玩'
      ELSE '付费后7天未玩'
    END AS path_group,
    first_pay_ts,
    first_post_game_ts
  FROM per_user
)
SELECT
  'pre_2026-06-16_to_06-30' AS period,
  path_group,
  COUNT(*) AS first_pay_users,
  SAFE_DIVIDE(COUNT(*), SUM(COUNT(*)) OVER ()) AS user_share,
  APPROX_QUANTILES(TIMESTAMP_DIFF(first_post_game_ts, first_pay_ts, MINUTE), 100)[OFFSET(50)] AS median_minutes_to_post_game
FROM classified
GROUP BY path_group
HAVING first_pay_users >= 30
ORDER BY first_pay_users DESC;

