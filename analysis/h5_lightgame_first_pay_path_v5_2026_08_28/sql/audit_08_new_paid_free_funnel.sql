WITH scoped AS (
  SELECT
    SAFE.PARSE_DATE('%Y-%m-%d', register_day) AS register_date,
    SAFE.PARSE_DATE('%Y-%m-%d', first_pay_date) AS first_pay_date,
    SAFE.PARSE_DATE('%Y-%m-%d', first_game_date) AS first_game_date,
    SAFE.PARSE_DATE('%Y-%m-%d', last_game_date) AS last_game_date,
    first_client_type,
    first_channel,
    first_media,
    target_day AS event_date
  FROM `wajenigeria.origin_hfyl.user_xlid`
  WHERE app_id = 90006
    AND target_day BETWEEN DATE '2026-01-01' AND DATE '2026-12-31'
    AND first_client_type = 3
    AND SAFE.PARSE_DATE('%Y-%m-%d', register_day)
        BETWEEN DATE '2026-06-16' AND DATE '2026-08-10'
), classified AS (
  SELECT
    CASE
      WHEN register_date BETWEEN DATE '2026-06-16' AND DATE '2026-07-13' THEN 'pre'
      WHEN register_date BETWEEN DATE '2026-07-14' AND DATE '2026-08-10' THEN 'post'
    END AS period,
    CASE
      WHEN first_channel = 'PAWAJEBETH5' THEN 'H5自然'
      WHEN first_channel = 'PAWAJEH5PWA' THEN 'PWA自然_映射待核验'
      WHEN first_media = 80 THEN 'H5 Facebook'
      WHEN first_media = 81 THEN 'H5 Google'
      ELSE 'H5其他'
    END AS segment,
    CASE
      WHEN first_pay_date = register_date THEN '当日新增首充'
      ELSE '当日新增未付费'
    END AS user_group,
    register_date,
    first_game_date,
    last_game_date,
    event_date
  FROM scoped
)
SELECT
  period,
  segment,
  user_group,
  COUNT(*) AS new_users,
  COUNTIF(first_game_date = register_date) AS first_game_d0_users,
  COUNTIF(first_game_date BETWEEN register_date AND DATE_ADD(register_date, INTERVAL 7 DAY)) AS first_game_d7_users,
  COUNTIF(first_game_date IS NULL OR first_game_date > DATE_ADD(register_date, INTERVAL 7 DAY)) AS no_first_game_by_d7,
  COUNTIF(first_game_date IS NULL AND last_game_date IS NOT NULL) AS contradictory_game_dates
FROM classified
WHERE event_date BETWEEN DATE '2026-01-01' AND DATE '2026-12-31'
GROUP BY period, segment, user_group
HAVING new_users >= 30
ORDER BY period, segment, user_group;
