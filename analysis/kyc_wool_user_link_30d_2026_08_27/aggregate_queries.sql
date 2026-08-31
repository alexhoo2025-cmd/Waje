-- Privacy boundary: all user identifiers are used only inside database joins.
-- Every result set is aggregated and excludes raw user, account, device, IP,
-- biometric, bank and transaction identifiers.
-- Database: Metabase / whot_center. Run as ephemeral read-only native queries;
-- do not save this SQL as an editable shared question without data-owner review.

-- Q1. 30-day current face-status record trend. State record is not a full funnel.
SELECT
  CASE
    WHEN f.create_time < '2026-08-04 00:00:00' THEN '7月28日-8月3日'
    WHEN f.create_time < '2026-08-11 00:00:00' THEN '8月4日-8月10日'
    WHEN f.create_time < '2026-08-18 00:00:00' THEN '8月11日-8月17日'
    ELSE '8月18日-8月26日'
  END AS phase,
  COUNT(DISTINCT f.gid) AS face_status_users,
  SUM(CASE WHEN f.result = 1 THEN 1 ELSE 0 END) AS face_success_users,
  SUM(CASE WHEN f.result = 0 THEN 1 ELSE 0 END) AS face_not_pass_users,
  ROUND(SUM(CASE WHEN f.result = 1 THEN 1 ELSE 0 END) / COUNT(DISTINCT f.gid), 4) AS face_success_share,
  ROUND(AVG(f.verify_num), 2) AS avg_verify_attempts
FROM kyc_face_info f
WHERE f.create_time >= '2026-07-28 00:00:00'
  AND f.create_time < '2026-08-27 00:00:00'
GROUP BY phase
ORDER BY MIN(f.create_time);

-- Q2. Completed seven-day observation for first-charge users by face state.
-- type=1/status=3 and type=2/status=103 are provisional success mappings,
-- reconciled to the same-day Origin TC aggregate before use.
WITH first_pay AS (
  SELECT r.gid, r.firstRechargeTime AS first_pay_time, r.firstRechargeAmount AS first_pay_amount_cent
  FROM risk_recharge r
  WHERE r.firstRechargeTime >= UNIX_TIMESTAMP('2026-08-12 00:00:00')
    AND r.firstRechargeTime < UNIX_TIMESTAMP('2026-08-20 00:00:00')
), withdraw_7d AS (
  SELECT fp.gid,
    COALESCE(SUM(o.amount), 0) AS withdraw_amount_cent,
    MAX(CASE WHEN o.id IS NOT NULL THEN 1 ELSE 0 END) AS has_withdraw_7d,
    MAX(CASE WHEN o.time < fp.first_pay_time + 86400 THEN 1 ELSE 0 END) AS has_withdraw_24h
  FROM first_pay fp
  LEFT JOIN order_log o
    ON o.gid = fp.gid AND o.type = 2 AND o.status = 103
   AND o.time >= fp.first_pay_time
   AND o.time < LEAST(fp.first_pay_time + 7 * 86400, UNIX_TIMESTAMP('2026-08-27 00:00:00'))
  GROUP BY fp.gid
)
SELECT
  CASE WHEN f.result = 1 THEN 'face_success'
       WHEN f.result = 0 THEN 'face_not_pass'
       ELSE 'no_face_state_record' END AS face_status_group,
  COUNT(*) AS first_pay_users,
  ROUND(SUM(fp.first_pay_amount_cent) / 100.0, 2) AS first_pay_amount,
  ROUND(SUM(w.withdraw_amount_cent) / 100.0, 2) AS withdraw_amount_7d,
  ROUND(SUM(w.withdraw_amount_cent) / NULLIF(SUM(fp.first_pay_amount_cent),0), 4) AS withdraw_to_first_pay_ratio_7d,
  ROUND(SUM(w.has_withdraw_7d) / COUNT(*), 4) AS withdraw_user_rate_7d,
  ROUND(SUM(w.has_withdraw_24h) / COUNT(*), 4) AS fast_withdraw_user_rate_24h,
  ROUND(SUM(CASE WHEN w.withdraw_amount_cent > fp.first_pay_amount_cent THEN 1 ELSE 0 END) / COUNT(*), 4) AS withdraw_gt_first_pay_user_rate
FROM first_pay fp
LEFT JOIN kyc_face_info f ON f.gid = fp.gid
LEFT JOIN withdraw_7d w ON w.gid = fp.gid
GROUP BY face_status_group
HAVING COUNT(*) >= 10
ORDER BY first_pay_users DESC;

-- Q3. Same first-charge population: gameplay participation only.
WITH first_pay AS (
  SELECT r.gid, r.firstRechargeTime AS first_pay_time
  FROM risk_recharge r
  WHERE r.firstRechargeTime >= UNIX_TIMESTAMP('2026-08-12 00:00:00')
    AND r.firstRechargeTime < UNIX_TIMESTAMP('2026-08-20 00:00:00')
), game_7d AS (
  SELECT fp.gid,
    COUNT(g.id) AS game_summary_record_count,
    COALESCE(SUM(g.round_count), 0) AS round_count_7d,
    COALESCE(SUM(g.bet_amount), 0) AS bet_amount_7d
  FROM first_pay fp
  LEFT JOIN stat_game_bet_gain g
    ON g.gid = fp.gid
   AND g.update_at >= fp.first_pay_time
   AND g.update_at < LEAST(fp.first_pay_time + 7 * 86400, UNIX_TIMESTAMP('2026-08-27 00:00:00'))
  GROUP BY fp.gid
)
SELECT
  CASE WHEN f.result = 1 THEN 'face_success'
       WHEN f.result = 0 THEN 'face_not_pass'
       ELSE 'no_face_state_record' END AS face_status_group,
  COUNT(*) AS first_pay_users,
  ROUND(SUM(CASE WHEN g.game_summary_record_count > 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS game_user_rate_7d,
  ROUND(SUM(CASE WHEN g.round_count_7d = 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS zero_round_user_rate_7d,
  ROUND(SUM(g.round_count_7d) / NULLIF(SUM(CASE WHEN g.game_summary_record_count > 0 THEN 1 ELSE 0 END), 0), 1) AS avg_rounds_per_game_user_7d
FROM first_pay fp
LEFT JOIN kyc_face_info f ON f.gid = fp.gid
LEFT JOIN game_7d g ON g.gid = fp.gid
GROUP BY face_status_group
HAVING COUNT(*) >= 10
ORDER BY first_pay_users DESC;

-- Q4. Existing rule linkage, not a user-level output and not a no-risk proof.
WITH first_pay AS (
  SELECT r.gid, r.firstRechargeTime AS first_pay_time
  FROM risk_recharge r
  WHERE r.firstRechargeTime >= UNIX_TIMESTAMP('2026-08-12 00:00:00')
    AND r.firstRechargeTime < UNIX_TIMESTAMP('2026-08-20 00:00:00')
), risk_7d AS (
  SELECT fp.gid,
    COUNT(ri.id) AS risk_info_record_count,
    COUNT(DISTINCT ri.sub_type) AS linked_identity_type_count,
    MAX(CASE WHEN rr.id IS NOT NULL THEN 1 ELSE 0 END) AS has_rule_match
  FROM first_pay fp
  LEFT JOIN risk_info ri
    ON ri.gid = fp.gid
   AND ri.create_time >= FROM_UNIXTIME(fp.first_pay_time)
   AND ri.create_time < FROM_UNIXTIME(LEAST(fp.first_pay_time + 7 * 86400, UNIX_TIMESTAMP('2026-08-27 00:00:00')))
  LEFT JOIN risk_rule rr ON rr.unique_id = ri.unique_id
  GROUP BY fp.gid
)
SELECT
  CASE WHEN f.result = 1 THEN 'face_success'
       WHEN f.result = 0 THEN 'face_not_pass'
       ELSE 'no_face_state_record' END AS face_status_group,
  COUNT(*) AS first_pay_users,
  ROUND(SUM(CASE WHEN r.risk_info_record_count > 0 THEN 1 ELSE 0 END) / COUNT(*), 4) AS identity_link_record_user_rate,
  ROUND(SUM(CASE WHEN r.linked_identity_type_count >= 2 THEN 1 ELSE 0 END) / COUNT(*), 4) AS multi_identity_type_user_rate,
  ROUND(SUM(r.has_rule_match) / COUNT(*), 4) AS risk_rule_match_user_rate
FROM first_pay fp
LEFT JOIN kyc_face_info f ON f.gid = fp.gid
LEFT JOIN risk_7d r ON r.gid = fp.gid
GROUP BY face_status_group
HAVING COUNT(*) >= 10
ORDER BY first_pay_users DESC;

-- Q5. Corrected 7-day cash TC. The anchor is the actual first successful cash
-- recharge found within +/-24h of the risk first-recharge timestamp. The ratio
-- is successful withdrawal over all successful cash recharge inside the same 7 days.
WITH risk_first_pay AS (
  SELECT r.gid, r.firstRechargeTime AS risk_first_pay_time
  FROM risk_recharge r
  WHERE r.firstRechargeTime >= UNIX_TIMESTAMP('2026-08-12 00:00:00')
    AND r.firstRechargeTime < UNIX_TIMESTAMP('2026-08-20 00:00:00')
), actual_first_pay AS (
  SELECT rf.gid, MIN(o.time) AS actual_first_pay_time
  FROM risk_first_pay rf
  JOIN order_log o
    ON o.gid = rf.gid
   AND o.type = 1
   AND o.status = 3
   AND o.time >= rf.risk_first_pay_time - 86400
   AND o.time < rf.risk_first_pay_time + 86400
  GROUP BY rf.gid
), cashflow_7d AS (
  SELECT af.gid,
    COALESCE(SUM(CASE WHEN o.type = 1 AND o.status = 3 THEN o.pay_amount ELSE 0 END), 0) AS cash_recharge_7d_cent,
    COALESCE(SUM(CASE WHEN o.type = 2 AND o.status = 103 THEN o.amount ELSE 0 END), 0) AS successful_withdraw_7d_cent,
    COUNT(CASE WHEN o.type = 1 AND o.status = 3 THEN o.id END) AS successful_recharge_order_count,
    MAX(CASE WHEN o.type = 2 AND o.status = 103 AND o.time < af.actual_first_pay_time + 86400 THEN 1 ELSE 0 END) AS has_withdraw_24h
  FROM actual_first_pay af
  LEFT JOIN order_log o
    ON o.gid = af.gid
   AND o.time >= af.actual_first_pay_time
   AND o.time < af.actual_first_pay_time + 7 * 86400
   AND ((o.type = 1 AND o.status = 3) OR (o.type = 2 AND o.status = 103))
  GROUP BY af.gid
)
SELECT
  CASE WHEN f.result = 1 THEN 'face_success'
       WHEN f.result = 0 THEN 'face_not_pass'
       ELSE 'no_face_state_record' END AS face_status_group,
  COUNT(*) AS first_pay_users,
  ROUND(SUM(c.cash_recharge_7d_cent) / 100.0, 2) AS cash_recharge_7d,
  ROUND(SUM(c.successful_withdraw_7d_cent) / 100.0, 2) AS successful_withdraw_7d,
  ROUND(SUM(c.successful_withdraw_7d_cent) / NULLIF(SUM(c.cash_recharge_7d_cent), 0), 4) AS tc_ratio_7d,
  ROUND(SUM(CASE WHEN c.successful_recharge_order_count >= 2 THEN 1 ELSE 0 END) / COUNT(*), 4) AS repeat_recharge_user_rate,
  ROUND(SUM(c.has_withdraw_24h) / COUNT(*), 4) AS withdraw_user_rate_24h
FROM actual_first_pay af
LEFT JOIN kyc_face_info f ON f.gid = af.gid
LEFT JOIN cashflow_7d c ON c.gid = af.gid
GROUP BY face_status_group
HAVING COUNT(*) >= 10
ORDER BY first_pay_users DESC;
