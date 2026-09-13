-- DRY-RUN DESIGN ONLY at this stage. Channel-cohort comparison, not actual host.
-- Amounts are source units and GAMEEND rows are not yet certified bet counts.
WITH profile_candidates AS (
 SELECT user_id,register_time,xlid_time,download_channel,first_channel
 FROM `wajenigeria.origin_hfyl.user_xlid`
 WHERE target_day BETWEEN DATE '2019-01-01' AND DATE '2026-09-07'
   AND app_id=90006 AND user_id IS NOT NULL AND user_id!=''
), profiles AS (
 SELECT user_id,
        MIN(IF(register_time>0,DATE(TIMESTAMP_MILLIS(register_time),'Africa/Lagos'),NULL)) AS register_date,
        ARRAY_AGG(STRUCT(download_channel,first_channel)
          ORDER BY IF(register_time>0,0,1),register_time,xlid_time LIMIT 1)[OFFSET(0)] AS channel_record
 FROM profile_candidates GROUP BY user_id
), game_events AS (
 SELECT target_day AS stat_date,user_id,play_id,bet_num,cash_settlement,is_robot,is_test_uid
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND app_id=90006 AND event_type='GAMEEND'
), labelled AS (
 SELECT g.stat_date,g.user_id,g.bet_num,g.cash_settlement,
        COALESCE(p.channel_record.download_channel,'UNKNOWN') AS channel_name,
        CASE WHEN p.register_date IS NULL THEN 'unknown_registration'
             WHEN DATE_DIFF(g.stat_date,p.register_date,DAY)<0 THEN 'invalid_registration'
             WHEN DATE_DIFF(g.stat_date,p.register_date,DAY)<30 THEN 'new_30d'
             ELSE 'old_over_30d' END AS age_group,
        CASE WHEN SAFE_CAST(g.play_id AS INT64) BETWEEN 9150001 AND 9159999 THEN 'Tada'
             WHEN SAFE_CAST(g.play_id AS INT64) BETWEEN 9160001 AND 9169999 THEN 'PP'
             ELSE 'other_games' END AS provider
 FROM game_events g LEFT JOIN profiles p ON p.user_id=g.user_id
 WHERE g.stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND g.is_robot IS FALSE AND (g.is_test_uid IS NULL OR g.is_test_uid!=1)
)
SELECT channel_name,age_group,provider,
       COUNT(1) AS settlement_event_rows,COUNT(DISTINCT user_id) AS users,
       SUM(bet_num) AS source_bet_sum,SUM(cash_settlement) AS source_settlement_sum
FROM labelled GROUP BY channel_name,age_group,provider
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY channel_name,age_group,provider
LIMIT 3000;
