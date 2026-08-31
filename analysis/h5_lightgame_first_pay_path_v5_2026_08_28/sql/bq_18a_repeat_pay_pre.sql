WITH profile_scope AS (
  SELECT CAST(`用户id` AS STRING) AS user_id
  FROM `wajenigeria.pubwaje.user_profiles`
  WHERE `设备类型` = 'Others'
    AND DATE(`首充日期`, 'Africa/Lagos') BETWEEN @cohort_start AND @cohort_end
), order_window AS (
  SELECT
    user_id,
    TIMESTAMP_MILLIS(SAFE_CAST(time AS INT64)) AS order_ts,
    is_first_buy,
    order_no,
    uuid
  FROM `wajenigeria.origin_hfyl.view_metaevent_order`
  WHERE app_id = 90006
    AND target_day BETWEEN @cohort_start AND @order_end
    AND is_success = 'pay_success'
    AND SAFE_CAST(time AS INT64) IS NOT NULL
), first_pay AS (
  SELECT o.user_id, MIN(o.order_ts) AS first_pay_ts
  FROM order_window o
  JOIN profile_scope p USING (user_id)
  WHERE o.is_first_buy IS TRUE
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
    first_post_game_ts,
    CASE
      WHEN played_pre_7d THEN '付费前7日已玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 30 MINUTE) THEN '付费后30分钟内玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 24 HOUR) THEN '付费后24小时内玩'
      WHEN first_post_game_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 7 DAY) THEN '付费后第2至7天玩'
      ELSE '付费后7天未玩'
    END AS path_group
  FROM per_user
), repeat_by_user AS (
  SELECT
    c.user_id,
    c.path_group,
    c.first_pay_ts,
    c.first_post_game_ts,
    MIN(IF(o.is_first_buy IS FALSE AND o.order_ts > c.first_pay_ts, o.order_ts, NULL)) AS first_repeat_pay_ts,
    COUNT(DISTINCT IF(o.is_first_buy IS FALSE AND o.order_ts > c.first_pay_ts, COALESCE(NULLIF(o.order_no, ''), o.uuid), NULL)) AS repeat_orders_7d
  FROM classified c
  LEFT JOIN order_window o
    ON o.user_id = c.user_id
   AND o.order_ts > c.first_pay_ts
   AND o.order_ts < TIMESTAMP_ADD(c.first_pay_ts, INTERVAL 7 DAY)
  GROUP BY c.user_id, c.path_group, c.first_pay_ts, c.first_post_game_ts
)
SELECT
  @period_label AS period_segment,
  path_group,
  COUNT(*) AS first_pay_users,
  COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 1 DAY)) AS repeat_pay_users_d1,
  COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 3 DAY)) AS repeat_pay_users_d3,
  COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 7 DAY)) AS repeat_pay_users_d7,
  SAFE_DIVIDE(COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 1 DAY)), COUNT(*)) AS repeat_pay_rate_d1,
  SAFE_DIVIDE(COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 3 DAY)), COUNT(*)) AS repeat_pay_rate_d3,
  SAFE_DIVIDE(COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 7 DAY)), COUNT(*)) AS repeat_pay_rate_d7,
  COUNTIF(first_repeat_pay_ts IS NOT NULL AND first_post_game_ts IS NOT NULL AND first_repeat_pay_ts < first_post_game_ts) AS repeat_before_first_game_users,
  COUNTIF(first_repeat_pay_ts IS NOT NULL AND first_post_game_ts IS NOT NULL AND first_repeat_pay_ts >= first_post_game_ts) AS repeat_after_first_game_users,
  COUNTIF(first_repeat_pay_ts IS NOT NULL AND first_post_game_ts IS NULL) AS repeat_without_post_game_users,
  SUM(repeat_orders_7d) AS repeat_orders_7d
FROM repeat_by_user
GROUP BY period_segment, path_group
HAVING first_pay_users >= 30
ORDER BY first_pay_users DESC;
