/* Status distribution and idempotency checks for the leading regular H5 package. */

SELECT
  DATE(FROM_UNIXTIME(o.time)) AS business_date,
  o.type AS order_type,
  o.status AS order_status,
  COUNT(*) AS order_count,
  ROUND(SUM(o.amount) / 100.0, 2) AS amount
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND u.reg_channel = 'PAWAJEH5'
  AND u.reg_package = 'com.wajegame.web'
  AND o.type IN (1, 2)
GROUP BY 1,2,3
ORDER BY business_date DESC, order_type, amount DESC;

/* Success-state duplicate check. A count differing from the distinct values requires ledger review. */
SELECT
  DATE(FROM_UNIXTIME(o.time)) AS business_date,
  o.type AS order_type,
  o.status AS order_status,
  COUNT(*) AS order_count,
  COUNT(DISTINCT NULLIF(o.serial_num, '')) AS distinct_serial_num,
  COUNT(DISTINCT NULLIF(o.reference, '')) AS distinct_reference,
  SUM(CASE WHEN o.serial_num IS NULL OR o.serial_num = '' THEN 1 ELSE 0 END) AS missing_serial_num_count,
  SUM(CASE WHEN o.reference IS NULL OR o.reference = '' THEN 1 ELSE 0 END) AS missing_reference_count,
  ROUND(SUM(o.amount) / 100.0, 2) AS amount
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-27 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND u.reg_channel = 'PAWAJEH5'
  AND u.reg_package = 'com.wajegame.web'
  AND ((o.type = 1 AND o.status = 3) OR (o.type = 2 AND o.status = 103))
GROUP BY 1,2,3
ORDER BY business_date DESC, order_type;
