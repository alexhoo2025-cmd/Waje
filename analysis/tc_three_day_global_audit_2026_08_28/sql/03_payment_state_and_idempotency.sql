/* Payment-state and idempotency checks for the three high-contribution channels. */

SELECT
  DATE(FROM_UNIXTIME(o.time)) AS business_date,
  u.reg_channel,
  SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_status3_amount,
  SUM(CASE WHEN o.type = 1 AND o.status = 4 THEN o.amount ELSE 0 END) / 100.0 AS recharge_status4_amount,
  SUM(CASE WHEN o.type = 1 AND o.status = 1 THEN o.amount ELSE 0 END) / 100.0 AS recharge_status1_amount,
  SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_status103_amount,
  SUM(CASE WHEN o.type = 2 AND o.status = 104 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_status104_amount
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND HOUR(FROM_UNIXTIME(o.time)) BETWEEN 0 AND 11
  AND u.reg_channel IN ('WajeSpecial', 'PAWAJEIOS', 'PAWAJEH5')
  AND o.type IN (1,2)
GROUP BY 1,2
ORDER BY business_date, reg_channel;

SELECT
  DATE(FROM_UNIXTIME(o.time)) AS business_date,
  u.reg_channel,
  o.type AS order_type,
  COUNT(*) AS order_count,
  COUNT(DISTINCT NULLIF(o.serial_num, '')) AS distinct_serial_num,
  COUNT(DISTINCT NULLIF(o.reference, '')) AS distinct_reference,
  SUM(CASE WHEN o.serial_num IS NULL OR o.serial_num = '' THEN 1 ELSE 0 END) AS missing_serial_num_count,
  SUM(CASE WHEN o.reference IS NULL OR o.reference = '' THEN 1 ELSE 0 END) AS missing_reference_count
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND HOUR(FROM_UNIXTIME(o.time)) BETWEEN 0 AND 11
  AND u.reg_channel IN ('WajeSpecial', 'PAWAJEIOS', 'PAWAJEH5')
  AND ((o.type = 1 AND o.status = 3) OR (o.type = 2 AND o.status = 103))
GROUP BY 1,2,3
ORDER BY business_date, reg_channel, order_type;
