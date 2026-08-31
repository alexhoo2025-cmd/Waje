/*
  Status=4 semantic audit. This query produces only aggregate evidence.
  It does not replace the payment-service source-code enum or ledger state machine.
*/

/* Did a status=4 reference later appear as status=3 with the same reference? */
SELECT
  DATE(FROM_UNIXTIME(s4.time)) AS status4_date,
  COUNT(*) AS status4_order_count,
  SUM(s4.amount) / 100.0 AS status4_amount,
  SUM(CASE WHEN s3.reference IS NOT NULL THEN 1 ELSE 0 END) AS matched_later_status3_order_count,
  SUM(CASE WHEN s3.reference IS NOT NULL THEN s4.amount ELSE 0 END) / 100.0 AS matched_later_status3_amount,
  SUM(CASE WHEN s3.reference IS NOT NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS later_success_match_rate
FROM whot_center.order_log AS s4
LEFT JOIN whot_center.order_log AS s3
  ON s3.type = 1
  AND s3.status = 3
  AND s3.reference = s4.reference
  AND s3.time >= s4.time
  AND s3.time < s4.time + 7 * 86400
WHERE s4.type = 1
  AND s4.status = 4
  AND s4.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00')
  AND s4.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
GROUP BY 1
ORDER BY status4_date;

/* Compare the payment-field profile of the three visible recharge states. */
SELECT
  status AS recharge_status,
  pay_way,
  COUNT(*) AS order_count,
  SUM(amount) / 100.0 AS amount_sum,
  SUM(pay_amount) / 100.0 AS pay_amount_sum,
  SUM(fee) / 100.0 AS fee_sum,
  SUM(CASE WHEN pay_amount = amount THEN 1 ELSE 0 END) AS pay_amount_equals_amount_orders,
  SUM(CASE WHEN pay_amount = 0 THEN 1 ELSE 0 END) AS zero_pay_amount_orders
FROM whot_center.order_log
WHERE type = 1
  AND status IN (1,3,4)
  AND time >= UNIX_TIMESTAMP('2026-08-26 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-08-28 00:00:00')
GROUP BY 1,2
ORDER BY recharge_status, amount_sum DESC;
