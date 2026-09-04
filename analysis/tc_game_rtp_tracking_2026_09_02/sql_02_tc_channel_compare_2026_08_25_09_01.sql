SELECT
  u.reg_channel AS channel,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_0825_0828,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_0825_0828,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / NULLIF(SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) AS tc_0825_0828,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_0829_0901,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_0829_0901,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / NULLIF(SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) AS tc_0829_0901
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-25 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-09-02 00:00:00')
  AND ((o.type = 1 AND o.status = 3) OR (o.type = 2 AND o.status = 103))
GROUP BY 1
HAVING recharge_0829_0901 > 0
ORDER BY recharge_0829_0901 DESC;
