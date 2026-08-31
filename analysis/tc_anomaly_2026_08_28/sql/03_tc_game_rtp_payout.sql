/*
  Required certified game settlement query.
  This template deliberately uses an authorised daily settlement View rather than a lifecycle
  aggregate: TC cannot establish individual-game RTP. Replace the view name only after Data
  Development confirms its owner, terminal-status predicate, asset scope, and package mapping.
*/

SELECT
  business_date,
  package_id,
  attribution_media_id,
  game_id,
  game_name,
  provider,
  game_version,
  config_version,
  SUM(valid_cash_bet_amount) AS valid_cash_bet_amount,
  SUM(final_cash_payout_amount) AS final_cash_payout_amount,
  SUM(valid_round_count) AS valid_round_count,
  ROUND(SUM(final_cash_payout_amount) / NULLIF(SUM(valid_cash_bet_amount), 0) * 100, 2) AS actual_rtp_pct,
  MAX(theoretical_rtp_pct) AS theoretical_rtp_pct,
  SUM(CASE WHEN final_cash_payout_amount >= 10000000 THEN 1 ELSE 0 END) AS high_payout_event_count,
  SUM(CASE WHEN final_cash_payout_amount >= 10000000 THEN final_cash_payout_amount ELSE 0 END) AS high_payout_amount
FROM certified_game_settlement_daily  /* data development must supply this authorised View */
WHERE business_date = '2026-08-27'
  AND package_id IN ('com.wajegame.web', 'com.hfyl.special.h5')
  AND settlement_status = 'settled'
GROUP BY 1,2,3,4,5,6,7,8
ORDER BY final_cash_payout_amount DESC;

/* Hilo candidate check: safe aggregate only, no user or order identifiers returned. */
SELECT
  COUNT(DISTINCT h.gid) AS hilo_participants,
  COUNT(h.id) AS hilo_orders,
  ROUND(SUM(CASE WHEN h.status = 2 THEN h.bet_amount ELSE 0 END) / 100.0, 2) AS settled_bet_amount,
  ROUND(SUM(CASE WHEN h.status = 2 THEN h.cashout_amount ELSE 0 END) / 100.0, 2) AS settled_cashout_amount,
  ROUND(SUM(CASE WHEN h.status = 2 THEN h.cashout_amount ELSE 0 END)
    / NULLIF(SUM(CASE WHEN h.status = 2 THEN h.bet_amount ELSE 0 END), 0) * 100, 2) AS settled_payout_to_bet_pct,
  SUM(CASE WHEN h.max_win_capped = 1 THEN 1 ELSE 0 END) AS capped_order_count
FROM whot_center.wg_hilo_game_order_v2 AS h
INNER JOIN (
  SELECT o.gid
  FROM whot_center.order_log AS o
  INNER JOIN whot_center.uc_user AS u ON u.user_id = o.gid
  WHERE o.type = 2 AND o.status = 103
    AND o.time >= UNIX_TIMESTAMP('2026-08-27 00:00:00')
    AND o.time < UNIX_TIMESTAMP('2026-08-28 00:00:00')
    AND u.reg_channel = 'PAWAJEH5'
    AND u.reg_package = 'com.wajegame.web'
  GROUP BY o.gid
  HAVING SUM(o.amount) >= 2000000
) AS high_withdraw_users ON high_withdraw_users.gid = h.gid
WHERE h.ended_at >= UNIX_TIMESTAMP('2026-08-27 00:00:00')
  AND h.ended_at < UNIX_TIMESTAMP('2026-08-28 00:00:00');
