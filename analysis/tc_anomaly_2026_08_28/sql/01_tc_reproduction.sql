/*
  Waje TC audit — reproduction and data-completeness check.
  Purpose: calculate cash TC as successful paid withdrawal / successful cash recharge.
  Source-system status values below are a provisional mapping because the formal state dictionary
  has not been supplied by the payment owner:
    recharge candidate = order_log.type = 1 AND status = 3
    paid-withdrawal candidate = order_log.type = 2 AND status = 103
  Amounts are stored in cents and are converted to Naira in this query.
*/

SELECT
  DATE(FROM_UNIXTIME(o.time)) AS business_date,
  MIN(HOUR(FROM_UNIXTIME(o.time))) AS first_loaded_hour,
  MAX(HOUR(FROM_UNIXTIME(o.time))) AS last_loaded_hour,
  COUNT(DISTINCT HOUR(FROM_UNIXTIME(o.time))) AS loaded_hour_count,
  ROUND(SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0, 2) AS success_recharge_amount,
  ROUND(SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0, 2) AS success_withdraw_amount,
  ROUND(
    SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END)
      / NULLIF(SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) * 100,
    2
  ) AS tc_pct,
  CASE WHEN COUNT(DISTINCT HOUR(FROM_UNIXTIME(o.time))) = 24 THEN 'complete_day' ELSE 'partial_day' END AS data_status
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u
  ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-21 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  /* Replace this predicate only after the business label-to-source mapping is certified. */
  AND u.reg_channel = 'PAWAJEH5'
GROUP BY 1
ORDER BY business_date DESC;

/* Same-hour comparison for an unfinished day. Change 10 only after recording the observed cutoff. */
SELECT
  DATE(FROM_UNIXTIME(o.time)) AS business_date,
  ROUND(SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0, 2) AS success_recharge_amount,
  ROUND(SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0, 2) AS success_withdraw_amount,
  ROUND(
    SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END)
      / NULLIF(SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) * 100,
    2
  ) AS tc_pct
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u
  ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-21 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND HOUR(FROM_UNIXTIME(o.time)) BETWEEN 0 AND 10
  AND u.reg_channel = 'PAWAJEH5'
GROUP BY 1
ORDER BY business_date DESC;
