-- One complete-day definition check against Origin, not a substitute for the full analysis window.
WITH scoped AS (
 SELECT target_day AS stat_date,user_id,play_id,bet_num,cash_settlement,refund_num,
        extra_num,service_charge,bet_count,unique_id,unique_id_bar,salt_key,is_robot
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day=DATE '2026-09-06'
   AND app_id=90006 AND event_type='GAMEEND' AND is_robot IS FALSE
), labelled AS (
 SELECT stat_date,user_id,bet_num,cash_settlement,refund_num,extra_num,service_charge,
        bet_count,unique_id,unique_id_bar,salt_key,play_id,
        CASE WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9159999 THEN 'Tada'
             WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9160001 AND 9169999 THEN 'PP'
             ELSE 'other_games' END AS provider
 FROM scoped WHERE stat_date=DATE '2026-09-06'
)
SELECT stat_date,IF(GROUPING(provider)=1,'all_games',provider) AS game_scope,
       COUNT(1) AS event_rows,COUNT(DISTINCT user_id) AS users,
       COUNT(DISTINCT salt_key) AS distinct_log_keys,
       COUNT(DISTINCT CONCAT(user_id,'|',play_id,'|',COALESCE(unique_id,'NULL'),'|',COALESCE(unique_id_bar,'NULL'))) AS distinct_user_game_round_keys,
       COUNTIF(unique_id IS NULL OR unique_id='') AS missing_round_key_rows,
       SUM(bet_num) AS source_bet_sum,SUM(cash_settlement) AS source_settlement_sum,
       SUM(refund_num) AS source_refund_sum,SUM(extra_num) AS source_extra_sum,
       SUM(service_charge) AS source_service_charge_sum,SUM(bet_count) AS source_bet_count,
       COUNTIF(bet_num>0) AS positive_bet_rows,
       COUNTIF(cash_settlement<0) AS negative_settlement_rows
FROM labelled
GROUP BY GROUPING SETS ((stat_date,provider),(stat_date))
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY stat_date,game_scope
LIMIT 100;
