/*
  Aggregate-only concentration check. Do not add gid, phone, account, device or bank fields to
  the output. Rows below ten users should remain suppressed in user-facing outputs.
*/

SELECT
  CASE
    WHEN withdraw_amount = 0 THEN '00_no_paid_withdrawal'
    WHEN withdraw_amount < 1000 THEN '01_under_1k'
    WHEN withdraw_amount < 5000 THEN '02_1k_to_5k'
    WHEN withdraw_amount < 20000 THEN '03_5k_to_20k'
    WHEN withdraw_amount < 100000 THEN '04_20k_to_100k'
    ELSE '05_100k_plus'
  END AS paid_withdrawal_band,
  COUNT(*) AS user_count,
  ROUND(SUM(recharge_amount), 2) AS success_recharge_amount,
  ROUND(SUM(withdraw_amount), 2) AS success_withdraw_amount,
  ROUND(SUM(withdraw_amount) / NULLIF(SUM(recharge_amount), 0) * 100, 2) AS tc_pct
FROM (
  SELECT
    o.gid,
    SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_amount,
    SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_amount
  FROM whot_center.order_log AS o
  INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
  WHERE o.time >= UNIX_TIMESTAMP('2026-08-27 00:00:00')
    AND o.time < UNIX_TIMESTAMP('2026-08-28 00:00:00')
    AND u.reg_channel = 'PAWAJEH5'
    AND u.reg_package = 'com.wajegame.web'
  GROUP BY o.gid
) AS user_cashflow
GROUP BY 1
HAVING COUNT(*) >= 10
ORDER BY paid_withdrawal_band;
