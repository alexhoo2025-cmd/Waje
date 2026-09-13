WITH scoped AS (
 SELECT target_day AS stat_date,user_id,play_id,game_type,lib,mode_id,room_id,asset_id,
        noun_type,client_type,package_channel,bet_num,cash_settlement,is_robot,
        is_test_uid,bet_count,refund_num,custom,
        CASE WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9159999 THEN 'Tada_code_range'
             WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9160001 AND 9169999 THEN 'PP_code_range'
             ELSE 'other' END AS provider_candidate
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day=DATE '2026-09-06' AND app_id=90006 AND event_type='GAMEEND'
   AND SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9169999
)
SELECT provider_candidate,game_type,lib,mode_id,room_id,asset_id,noun_type,client_type,
       COUNT(1) AS event_rows,COUNT(DISTINCT user_id) AS users,
       COUNT(DISTINCT play_id) AS games,
       SUM(bet_num) AS source_bet_sum,SUM(cash_settlement) AS source_cash_settlement_sum,
       COUNTIF(cash_settlement<0) AS negative_settlement_rows,
       COUNTIF(bet_count IS NULL) AS missing_bet_count_rows,
       COUNTIF(bet_count>1) AS multi_bet_rows,
       COUNTIF(refund_num>0) AS refund_rows,
       COUNTIF(is_robot IS TRUE) AS robot_rows,
       COUNTIF(is_robot IS NULL) AS unknown_robot_rows,
       COUNTIF(is_test_uid=1) AS test_rows,
       COUNTIF(package_channel IS NOT NULL AND package_channel!='') AS package_channel_present,
       COUNTIF(custom IS NOT NULL AND custom NOT IN ('','{}')) AS custom_present
FROM scoped WHERE stat_date=DATE '2026-09-06'
GROUP BY provider_candidate,game_type,lib,mode_id,room_id,asset_id,noun_type,client_type
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY provider_candidate,event_rows DESC
LIMIT 1000;
