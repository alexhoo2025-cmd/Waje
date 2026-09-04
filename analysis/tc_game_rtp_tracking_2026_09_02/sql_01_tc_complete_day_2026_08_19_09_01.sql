SELECT
  DATE(FROM_UNIXTIME(time)) AS business_date,
  SUM(CASE WHEN type = 1 AND status = 3 THEN amount ELSE 0 END) / 100.0 AS success_recharge_amount,
  SUM(CASE WHEN type = 2 AND status = 103 THEN amount ELSE 0 END) / 100.0 AS success_withdraw_amount,
  SUM(CASE WHEN type = 2 AND status = 103 THEN amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN type = 1 AND status = 3 THEN amount ELSE 0 END), 0) AS tc_rate
FROM whot_center.order_log
WHERE time >= UNIX_TIMESTAMP('2026-08-19 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-09-02 00:00:00')
GROUP BY 1 ORDER BY business_date;
