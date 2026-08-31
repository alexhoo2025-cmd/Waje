-- All-new-user layer. D15 first-pay conversion by registration cohort.
-- Denominator is registered users; this query is separate from the first-pay path cohort.
WITH registered AS (
  SELECT
    u.user_id,
    u.reg_time,
    CASE
      WHEN u.reg_time < UNIX_TIMESTAMP('2026-07-14 00:00:00') THEN 'pre'
      ELSE 'post'
    END AS period,
    COALESCE(NULLIF(u.reg_package, ''), '[blank]') AS reg_package,
    COALESCE(NULLIF(a.ad_channel, ''), NULLIF(u.reg_channel, ''), '[blank]') AS media_channel
  FROM uc_user u
  LEFT JOIN uc_user_adchannel a ON a.gid = u.user_id
  WHERE u.reg_time >= UNIX_TIMESTAMP('2026-06-16 00:00:00')
    AND u.reg_time < UNIX_TIMESTAMP('2026-08-11 00:00:00')
), fp AS (
  SELECT gid, MIN(firstRechargeTime) AS first_pay_time
  FROM risk_recharge
  GROUP BY gid
)
SELECT
  r.period,
  r.reg_package,
  r.media_channel,
  COUNT(*) AS new_users,
  SUM(fp.first_pay_time >= r.reg_time AND fp.first_pay_time < r.reg_time + 15 * 86400) AS first_pay_users_d15,
  ROUND(
    SUM(fp.first_pay_time >= r.reg_time AND fp.first_pay_time < r.reg_time + 15 * 86400) / COUNT(*),
    4
  ) AS first_pay_rate_d15
FROM registered r
LEFT JOIN fp ON fp.gid = r.user_id
GROUP BY r.period, r.reg_package, r.media_channel
HAVING COUNT(*) >= 30
ORDER BY r.period, new_users DESC;

