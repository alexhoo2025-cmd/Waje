WITH scoped AS (
 SELECT target_day AS stat_date, app_id, event_type, client_type, play_id,
        user_id, bet_num, cash_settlement, refund_num, bet_count, is_robot, is_test_uid,
        `time` AS calibrated_time, server_time
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day = DATE '2026-09-06'
   AND event_type IN ('GAMESTART','GAMEEND','BETREWARD')
)
SELECT app_id,event_type,client_type,
       COUNT(1) AS event_rows,COUNT(DISTINCT user_id) AS users,
       COUNT(DISTINCT play_id) AS distinct_play_ids,
       MIN(SAFE_CAST(play_id AS INT64)) AS min_play_code,
       MAX(SAFE_CAST(play_id AS INT64)) AS max_play_code,
       COUNTIF(bet_num>0) AS positive_bet_rows,
       COUNTIF(cash_settlement<0) AS negative_settlement_rows,
       COUNTIF(cash_settlement=0) AS zero_settlement_rows,
       COUNTIF(cash_settlement IS NULL) AS missing_settlement_rows,
       COUNTIF(refund_num>0) AS refund_rows,
       COUNTIF(bet_count>1) AS multi_bet_rows,
       COUNTIF(is_robot IS TRUE) AS robot_rows,
       COUNTIF(is_robot IS NULL) AS robot_unknown_rows,
       COUNTIF(is_test_uid=1) AS test_rows,
       MIN(calibrated_time) AS min_calibrated_time,
       MAX(calibrated_time) AS max_calibrated_time,
       MIN(server_time) AS min_server_time,MAX(server_time) AS max_server_time
FROM scoped
WHERE stat_date = DATE '2026-09-06'
GROUP BY app_id,event_type,client_type
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY app_id,event_type,client_type
LIMIT 1000;
