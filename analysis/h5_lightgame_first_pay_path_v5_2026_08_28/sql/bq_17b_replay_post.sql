WITH profile_scope AS (
  SELECT CAST(`用户id` AS STRING) AS user_id
  FROM `wajenigeria.pubwaje.user_profiles_2026-07-10_2026-08-10`
  WHERE `设备类型` = 'Others'
    AND DATE(`首充日期`, 'Africa/Lagos') BETWEEN @cohort_start AND @cohort_end
), first_pay AS (
  SELECT o.user_id, MIN(TIMESTAMP_MILLIS(SAFE_CAST(o.time AS INT64))) AS first_pay_ts
  FROM `wajenigeria.origin_hfyl.view_metaevent_order` o
  JOIN profile_scope p USING (user_id)
  WHERE o.app_id = 90006
    AND o.target_day BETWEEN @cohort_start AND @cohort_end
    AND o.is_first_buy IS TRUE
    AND o.is_success = 'pay_success'
    AND SAFE_CAST(o.time AS INT64) IS NOT NULL
  GROUP BY o.user_id
), game_window AS (
  SELECT user_id, TIMESTAMP_MILLIS(SAFE_CAST(time AS INT64)) AS game_ts
  FROM `wajenigeria.origin_hfyl.view_metaevent_gamestart`
  WHERE app_id = 90006
    AND target_day BETWEEN @game_start AND @game_end
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
    user_id,
    first_pay_ts,
    CASE
      WHEN played_pre_7d THEN '付费前7日已玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 30 MINUTE) THEN '付费后30分钟内玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 24 HOUR) THEN '付费后24小时内玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 7 DAY) THEN '付费后第2至7天玩'
      ELSE '付费后7天未玩'
    END AS path_group
  FROM per_user
), denominators AS (
  SELECT path_group, COUNT(*) AS first_pay_users
  FROM classified
  GROUP BY path_group
), user_day AS (
  SELECT DISTINCT
    c.path_group,
    g.user_id,
    DATE_DIFF(DATE(g.game_ts, 'Africa/Lagos'), DATE(c.first_pay_ts, 'Africa/Lagos'), DAY) AS day_since_first_pay
  FROM classified c
  JOIN game_window g USING (user_id)
  WHERE g.game_ts >= c.first_pay_ts
    AND g.game_ts < TIMESTAMP_ADD(c.first_pay_ts, INTERVAL 16 DAY)
)
SELECT
  @period_label AS period_segment,
  d.path_group,
  day_number AS day_since_first_pay,
  d.first_pay_users,
  COUNT(DISTINCT IF(ud.day_since_first_pay = day_number, ud.user_id, NULL)) AS replay_users,
  SAFE_DIVIDE(COUNT(DISTINCT IF(ud.day_since_first_pay = day_number, ud.user_id, NULL)), d.first_pay_users) AS replay_rate
FROM denominators d
CROSS JOIN UNNEST(GENERATE_ARRAY(0, 15)) AS day_number
LEFT JOIN user_day ud ON ud.path_group = d.path_group
GROUP BY period_segment, d.path_group, day_number, d.first_pay_users
HAVING d.first_pay_users >= 30
ORDER BY d.path_group, day_number;

