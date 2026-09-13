SELECT
  u.reg_channel AS channel,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-01 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_prev,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-01 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_prev,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-09-01 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-08 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_curr,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-09-01 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-08 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_curr
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-09-08 00:00:00')
  AND ((o.type = 1 AND o.status = 3) OR (o.type = 2 AND o.status = 103))
GROUP BY 1
HAVING recharge_curr > 0
ORDER BY recharge_curr DESC;
