/*
  Comparable channel TC for 2026-08-23—25 vs 2026-08-26—28.
  Both periods use 00:00—11:59 because 2026-08-28 is an incomplete day.
*/
SELECT
  u.reg_channel,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-23 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-26 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_0823_0825,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-23 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-26 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_0823_0825,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-23 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-26 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-23 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-26 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) AS tc_0823_0825,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END) / 100.0 AS recharge_0826_0828,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END) / 100.0 AS withdraw_0826_0828,
  SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN o.time >= UNIX_TIMESTAMP('2026-08-26 00:00:00') AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00') AND o.type = 1 AND o.status = 3 THEN o.amount ELSE 0 END), 0) AS tc_0826_0828
FROM whot_center.order_log AS o
INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
WHERE o.time >= UNIX_TIMESTAMP('2026-08-23 00:00:00')
  AND o.time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND HOUR(FROM_UNIXTIME(o.time)) BETWEEN 0 AND 11
  AND ((o.type = 1 AND o.status = 3) OR (o.type = 2 AND o.status = 103))
GROUP BY 1
ORDER BY recharge_0826_0828 DESC;

/*
  RTP cannot be filled from current sources. Data Development should provide this authorised View:
  one row per business_date x event-time channel x game x version x config x currency,
  using final successful settlement only.
*/
SELECT
  channel_id,
  SUM(effective_cash_bet_amount) AS effective_cash_bet_amount,
  SUM(final_cash_payout_amount) AS final_cash_payout_amount,
  SUM(final_cash_payout_amount) / NULLIF(SUM(effective_cash_bet_amount), 0) AS actual_rtp
FROM certified_channel_game_settlement_daily
WHERE business_date >= '2026-08-23'
  AND business_date < '2026-08-29'
  AND settlement_status = 'settled'
GROUP BY 1;
