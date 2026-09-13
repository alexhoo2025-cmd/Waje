WITH scoped AS (
 SELECT target_day AS stat_date,user_id,
        CASE WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9159999 THEN 'Tada_code_range'
             WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9160001 AND 9169999 THEN 'PP_code_range'
             ELSE 'other' END AS provider_candidate,
        custom
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day = DATE '2026-09-06' AND app_id=90006 AND event_type='GAMEEND'
   AND SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9169999
), keys AS (
 SELECT provider_candidate,user_id,k
 FROM scoped,UNNEST(JSON_KEYS(SAFE.PARSE_JSON(custom))) AS k
 WHERE stat_date = DATE '2026-09-06'
   AND REGEXP_CONTAINS(k,r'^[A-Za-z_][A-Za-z0-9_.]{0,64}$')
)
SELECT provider_candidate,k AS field_path,COUNT(1) AS occurrences,COUNT(DISTINCT user_id) AS users
FROM keys
GROUP BY provider_candidate,k
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY provider_candidate,occurrences DESC
LIMIT 1000;
