/*
  Daily TC comparison across the main business packages.
  IMPORTANT: reg_channel/reg_package are registration attributes in this source. They are not
  automatically an event-time attribution proof. Join a certified attribution snapshot before
  presenting a Facebook- or Google-media conclusion.
*/

SELECT
  DATE(FROM_UNIXTIME(o.time)) AS business_date,
  u.reg_channel,
  u.reg_sub_channel,
  u.reg_package,
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
  AND u.reg_channel IN ('WajeSpecial', 'PAWAJEIOS', 'PAWAJEBETH5', 'PAWAJEH5', 'PAPAWAJEH5GA')
GROUP BY 1, 2, 3, 4
ORDER BY business_date DESC, reg_channel, reg_package;

/*
  Contribution calculation for a confirmed complete day.
  Replace the 0.7998 baseline with the approved complete-day baseline for the selected channel.
*/
SELECT
  package_daily.business_date,
  package_daily.reg_channel,
  package_daily.reg_package,
  package_daily.success_recharge_amount,
  package_daily.success_withdraw_amount,
  ROUND(package_daily.success_withdraw_amount / NULLIF(package_daily.success_recharge_amount, 0) * 100, 2) AS tc_pct,
  ROUND(package_daily.success_recharge_amount * 0.7998, 2) AS expected_withdraw_amount_at_baseline,
  ROUND(package_daily.success_withdraw_amount - package_daily.success_recharge_amount * 0.7998, 2) AS excess_withdraw_amount
FROM (
  SELECT
    DATE(FROM_UNIXTIME(o.time)) AS business_date,
    u.reg_channel,
    u.reg_package,
    SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS success_recharge_amount,
    SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS success_withdraw_amount
  FROM whot_center.order_log AS o
  INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
  WHERE o.time >= UNIX_TIMESTAMP('2026-08-27 00:00:00')
    AND o.time < UNIX_TIMESTAMP('2026-08-28 00:00:00')
    AND u.reg_channel IN ('WajeSpecial', 'PAWAJEIOS', 'PAWAJEBETH5', 'PAWAJEH5', 'PAPAWAJEH5GA')
  GROUP BY 1, 2, 3
) AS package_daily
ORDER BY excess_withdraw_amount DESC;
