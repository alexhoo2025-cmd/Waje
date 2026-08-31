/*
  Run as a release-quality gate before reporting a TC exception as a business incident.
  Each query is aggregate-only; change dates deliberately and record the data cutoff.
*/

/* 1. Verify that the source has a complete twenty-four-hour day. */
SELECT
  DATE(FROM_UNIXTIME(time)) AS business_date,
  COUNT(DISTINCT HOUR(FROM_UNIXTIME(time))) AS loaded_hour_count,
  MAX(FROM_UNIXTIME(time)) AS source_max_event_time
FROM whot_center.order_log
WHERE time >= UNIX_TIMESTAMP('2026-08-21 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
GROUP BY 1
ORDER BY business_date DESC;

/* 2. Verify that success-state amounts reconcile to the business-facing TC report. */
SELECT
  DATE(FROM_UNIXTIME(o.time)) AS business_date,
  ROUND(SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0, 2) AS recharge_candidate,
  ROUND(SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0, 2) AS paid_withdraw_candidate
FROM whot_center.order_log AS o
WHERE o.time >= UNIX_TIMESTAMP('2026-08-21 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
GROUP BY 1
ORDER BY business_date DESC;

/* 3. Require the payment owner to attach an approved status dictionary before sign-off. */
SELECT type AS order_type, status AS order_status, COUNT(*) AS order_count
FROM whot_center.order_log
WHERE time >= UNIX_TIMESTAMP('2026-08-27 00:00:00')
  AND time < UNIX_TIMESTAMP('2026-08-28 00:00:00')
  AND type IN (1, 2)
GROUP BY 1,2
ORDER BY 1,2;
