/*
  Rank each registration channel's positive or negative paid-withdrawal deviation
  against its own 2026-08-19—25 same-window baseline.
  Registration channel is not a certified event-time attribution dimension.
*/
SELECT
  current_day.business_date,
  current_day.reg_channel,
  current_day.success_recharge_amount,
  current_day.success_withdraw_amount,
  current_day.success_withdraw_amount / NULLIF(current_day.success_recharge_amount, 0) AS tc_rate,
  baseline.baseline_tc_rate,
  current_day.success_withdraw_amount
    - current_day.success_recharge_amount * baseline.baseline_tc_rate AS excess_withdraw_amount
FROM (
  SELECT
    DATE(FROM_UNIXTIME(o.time)) AS business_date,
    u.reg_channel,
    SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS success_recharge_amount,
    SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS success_withdraw_amount
  FROM whot_center.order_log AS o
  INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
  WHERE o.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00')
    AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
    AND HOUR(FROM_UNIXTIME(o.time)) BETWEEN 0 AND 11
  GROUP BY 1,2
) AS current_day
LEFT JOIN (
  SELECT
    u.reg_channel,
    SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) * 1.0
      / NULLIF(SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) AS baseline_tc_rate
  FROM whot_center.order_log AS o
  INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
  WHERE o.time >= UNIX_TIMESTAMP('2026-08-19 00:00:00')
    AND o.time < UNIX_TIMESTAMP('2026-08-26 00:00:00')
    AND HOUR(FROM_UNIXTIME(o.time)) BETWEEN 0 AND 11
  GROUP BY 1
) AS baseline ON baseline.reg_channel = current_day.reg_channel
WHERE current_day.success_recharge_amount >= 100000
ORDER BY current_day.business_date DESC, excess_withdraw_amount DESC;
