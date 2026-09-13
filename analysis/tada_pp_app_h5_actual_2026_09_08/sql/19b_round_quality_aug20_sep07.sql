WITH events AS (
 SELECT target_day AS stat_date,user_id,play_id,mode_id,salt_key,unique_id,unique_id_bar,is_robot,is_test_uid
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-20' AND DATE '2026-09-07' AND app_id=90006 AND event_type='GAMEEND'
), labelled AS (
 SELECT stat_date,user_id,play_id,salt_key,unique_id,unique_id_bar,
 CASE WHEN mode_id=11 THEN 'Waje' WHEN mode_id=100 THEN 'WajeCoin' ELSE 'other_or_unknown_mode' END AS product_mode,
 CASE WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9159999 THEN 'Tada'
      WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9160001 AND 9169999 THEN 'PP' ELSE 'other_games' END AS provider
 FROM events WHERE stat_date BETWEEN DATE '2026-08-20' AND DATE '2026-09-07'
 AND is_robot IS FALSE AND (is_test_uid IS NULL OR is_test_uid!=1)
)
SELECT stat_date,product_mode,provider,COUNT(1) AS records,COUNT(DISTINCT user_id) AS users,
 COUNT(DISTINCT salt_key) AS distinct_log_keys,
 COUNTIF(salt_key IS NULL OR salt_key='') AS missing_log_key_records,
 COUNT(DISTINCT CONCAT(user_id,'|',play_id,'|',COALESCE(unique_id,'NULL'),'|',COALESCE(unique_id_bar,'NULL'))) AS distinct_user_game_round_keys,
 COUNTIF(unique_id IS NULL OR unique_id='') AS missing_round_key_records
FROM labelled GROUP BY stat_date,product_mode,provider
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY stat_date,product_mode,provider
LIMIT 500;
