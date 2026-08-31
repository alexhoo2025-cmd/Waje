/*
  All-product TC reproduction.
  Candidate success-state mapping — payment owner must certify before financial sign-off:
    cash recharge = type 1 / status 3
    paid withdrawal = type 2 / status 103
  Values are stored in cents; output divides amounts by 100.
*/

/* Complete-day trend. Do not include an incomplete day in a full-day comparison. */
SELECT
  DATE(FROM_UNIXTIME(time)) AS business_date,
  COUNT(DISTINCT HOUR(FROM_UNIXTIME(time))) AS loaded_hour_count,
  SUM(CASE WHEN type = 1 AND status = 3 THEN amount ELSE 0 END) / 100.0 AS success_recharge_amount,
  SUM(CASE WHEN type = 2 AND status = 103 THEN amount ELSE 0 END) / 100.0 AS success_withdraw_amount,
  SUM(CASE WHEN type = 2 AND status = 103 THEN amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN type = 1 AND status = 3 THEN amount ELSE 0 END), 0) AS tc_rate
FROM whot_center.order_log
WHERE time >= UNIX_TIMESTAMP('2026-08-19 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
GROUP BY 1
ORDER BY business_date;

/* Same-window comparison for the unfinished 2026-08-28 day. */
SELECT
  DATE(FROM_UNIXTIME(time)) AS business_date,
  SUM(CASE WHEN type = 1 AND status = 3 THEN amount ELSE 0 END) / 100.0 AS success_recharge_amount,
  SUM(CASE WHEN type = 2 AND status = 103 THEN amount ELSE 0 END) / 100.0 AS success_withdraw_amount,
  SUM(CASE WHEN type = 2 AND status = 103 THEN amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN type = 1 AND status = 3 THEN amount ELSE 0 END), 0) AS tc_rate
FROM whot_center.order_log
WHERE time >= UNIX_TIMESTAMP('2026-08-19 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND HOUR(FROM_UNIXTIME(time)) BETWEEN 0 AND 11
GROUP BY 1
ORDER BY business_date;
