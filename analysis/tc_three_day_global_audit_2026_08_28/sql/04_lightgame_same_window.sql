/*
  Hilo and Plinko only. These are game-table aggregates, not a complete new-game audit.
  A package x game x terminal-settlement certified View is required for all new third-party games.
*/

SELECT
  DATE(FROM_UNIXTIME(h.ended_at)) AS business_date,
  u.reg_channel,
  COUNT(h.id) AS order_count,
  SUM(CASE WHEN h.status = 2 THEN h.bet_amount ELSE 0 END) / 100.0 AS settled_bet_amount,
  SUM(CASE WHEN h.status = 2 THEN h.cashout_amount ELSE 0 END) / 100.0 AS settled_payout_amount,
  SUM(CASE WHEN h.status = 2 THEN h.cashout_amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN h.status = 2 THEN h.bet_amount ELSE 0 END), 0) AS settled_payout_to_bet_rate,
  SUM(CASE WHEN h.max_win_capped = 1 THEN 1 ELSE 0 END) AS capped_order_count
FROM whot_center.wg_hilo_game_order_v2 AS h
INNER JOIN whot_center.uc_user AS u ON u.user_id = h.gid
WHERE h.ended_at >= UNIX_TIMESTAMP('2026-08-26 00:00:00')
  AND h.ended_at < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND HOUR(FROM_UNIXTIME(h.ended_at)) BETWEEN 0 AND 11
  AND u.reg_channel IN ('WajeSpecial', 'PAWAJEIOS', 'PAWAJEH5')
GROUP BY 1,2
ORDER BY business_date, reg_channel;

SELECT
  DATE(FROM_UNIXTIME(p.create_time)) AS business_date,
  u.reg_channel,
  COUNT(p.id) AS order_count,
  SUM(p.total_bet_amount) / 100.0 AS bet_amount,
  SUM(p.total_payout_amount) / 100.0 AS payout_amount,
  SUM(p.total_payout_amount) / NULLIF(SUM(p.total_bet_amount), 0) AS payout_to_bet_rate,
  SUM(CASE WHEN p.error_code IS NOT NULL AND p.error_code <> 0 THEN 1 ELSE 0 END) AS nonzero_error_order_count,
  SUM(CASE WHEN p.settle_attempts > 1 THEN 1 ELSE 0 END) AS retry_settlement_order_count
FROM whot_center.wg_plinko_order AS p
INNER JOIN whot_center.uc_user AS u ON u.user_id = p.gid
WHERE p.create_time >= UNIX_TIMESTAMP('2026-08-26 00:00:00')
  AND p.create_time < UNIX_TIMESTAMP('2026-08-29 00:00:00')
  AND HOUR(FROM_UNIXTIME(p.create_time)) BETWEEN 0 AND 11
  AND u.reg_channel IN ('WajeSpecial', 'PAWAJEIOS', 'PAWAJEH5')
GROUP BY 1,2
ORDER BY business_date, reg_channel;
