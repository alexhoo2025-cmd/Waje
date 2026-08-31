SELECT
  app_id,
  COALESCE(NULLIF(download_channel, ''), '[blank]') AS download_channel,
  COALESCE(NULLIF(first_channel, ''), '[blank]') AS first_channel,
  first_media,
  COALESCE(NULLIF(first_sub_channel, ''), '[blank]') AS first_sub_channel,
  SUM(new_users) AS new_users,
  SUM(new_pay_user) AS first_pay_users,
  SAFE_DIVIDE(SUM(new_pay_user), SUM(new_users)) AS recomputed_first_pay_rate
FROM `wajenigeria.bigdata.first_pay_rate`
WHERE target_day BETWEEN DATE '2026-06-16' AND DATE '2026-08-10'
GROUP BY app_id, download_channel, first_channel, first_media, first_sub_channel
HAVING new_users >= 30
ORDER BY new_users DESC;

