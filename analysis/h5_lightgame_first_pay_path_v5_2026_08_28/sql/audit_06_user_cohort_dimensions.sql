WITH scoped AS (
  SELECT
    user_id,
    SAFE.PARSE_DATE('%Y-%m-%d', register_day) AS register_date,
    SAFE.PARSE_DATE('%Y-%m-%d', first_pay_date) AS first_pay_date,
    SAFE.PARSE_DATE('%Y-%m-%d', first_game_date) AS first_game_date,
    first_client_type,
    first_package_name,
    first_channel,
    first_sub_channel,
    first_media,
    link_channel,
    target_day AS event_date
  FROM `wajenigeria.origin_hfyl.user_xlid`
  WHERE app_id = 90006
    AND target_day BETWEEN DATE '2026-01-01' AND DATE '2026-12-31'
    AND SAFE.PARSE_DATE('%Y-%m-%d', register_day)
        BETWEEN DATE '2026-06-16' AND DATE '2026-08-10'
)
SELECT
  CASE
    WHEN register_date BETWEEN DATE '2026-06-16' AND DATE '2026-07-13' THEN 'pre'
    WHEN register_date BETWEEN DATE '2026-07-14' AND DATE '2026-08-10' THEN 'post'
  END AS period,
  first_client_type,
  COALESCE(NULLIF(first_package_name, ''), '(blank)') AS first_package_name,
  COALESCE(NULLIF(first_channel, ''), '(blank)') AS first_channel,
  COALESCE(NULLIF(first_sub_channel, ''), '(blank)') AS first_sub_channel,
  first_media,
  COALESCE(NULLIF(link_channel, ''), '(blank)') AS link_channel,
  COUNT(*) AS registered_users,
  COUNTIF(first_pay_date = register_date) AS same_day_first_pay_users,
  COUNTIF(first_game_date = register_date) AS first_game_d0_users,
  COUNTIF(first_game_date BETWEEN register_date AND DATE_ADD(register_date, INTERVAL 7 DAY)) AS first_game_d7_users
FROM scoped
WHERE event_date BETWEEN DATE '2026-01-01' AND DATE '2026-12-31'
GROUP BY period, first_client_type, first_package_name, first_channel,
         first_sub_channel, first_media, link_channel
HAVING registered_users >= 30
ORDER BY period, registered_users DESC
LIMIT 3000;
