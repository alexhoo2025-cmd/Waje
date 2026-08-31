WITH profile_scope AS (
  SELECT CAST(`用户id` AS STRING) AS user_id
  FROM `wajenigeria.pubwaje.user_profiles_2026-07-10_2026-08-10`
  WHERE `设备类型` = 'Others'
    AND DATE(`首充日期`, 'Africa/Lagos') BETWEEN DATE '2026-07-14' AND DATE '2026-07-28'
), orders AS (
  SELECT
    user_id,
    TIMESTAMP_MILLIS(SAFE_CAST(time AS INT64)) AS order_ts,
    is_first_buy
  FROM `wajenigeria.origin_hfyl.view_metaevent_order`
  WHERE app_id = 90006
    AND target_day BETWEEN DATE '2026-07-14' AND DATE '2026-08-12'
    AND is_success = 'pay_success'
    AND SAFE_CAST(time AS INT64) IS NOT NULL
), first_pay AS (
  SELECT o.user_id, MIN(o.order_ts) AS first_pay_ts
  FROM orders o
  JOIN profile_scope p USING (user_id)
  WHERE o.is_first_buy IS TRUE
  GROUP BY o.user_id
), per_user AS (
  SELECT
    fp.user_id,
    fp.first_pay_ts,
    MIN(IF(o.is_first_buy IS FALSE AND o.order_ts > fp.first_pay_ts, o.order_ts, NULL)) AS first_repeat_pay_ts
  FROM first_pay fp
  LEFT JOIN orders o
    ON o.user_id = fp.user_id
   AND o.order_ts > fp.first_pay_ts
   AND o.order_ts < TIMESTAMP_ADD(fp.first_pay_ts, INTERVAL 15 DAY)
  GROUP BY fp.user_id, fp.first_pay_ts
)
SELECT
  'post' AS period,
  COUNT(*) AS first_pay_users,
  COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 1 DAY)) AS repeat_pay_users_d1,
  COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 3 DAY)) AS repeat_pay_users_d3,
  COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 7 DAY)) AS repeat_pay_users_d7,
  COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 15 DAY)) AS repeat_pay_users_d15,
  SAFE_DIVIDE(COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 1 DAY)), COUNT(*)) AS repeat_pay_rate_d1,
  SAFE_DIVIDE(COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 3 DAY)), COUNT(*)) AS repeat_pay_rate_d3,
  SAFE_DIVIDE(COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 7 DAY)), COUNT(*)) AS repeat_pay_rate_d7,
  SAFE_DIVIDE(COUNTIF(first_repeat_pay_ts < TIMESTAMP_ADD(first_pay_ts, INTERVAL 15 DAY)), COUNT(*)) AS repeat_pay_rate_d15
FROM per_user;

