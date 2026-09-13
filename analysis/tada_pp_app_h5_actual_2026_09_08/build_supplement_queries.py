from pathlib import Path
from build_full_queries import base

P=Path(__file__).resolve().parent

def save(name,sql):
    path=P/'sql'/name
    if path.exists():raise RuntimeError(f'Preserve existing SQL snapshot: {path.name}')
    path.write_text(sql)

def main():
    save('15_full_round_quality.sql',"""WITH events AS (
 SELECT target_day AS stat_date,user_id,play_id,mode_id,salt_key,unique_id,unique_id_bar,
        bet_num,refund_num,bet_count,asset_id,noun_type,is_robot,is_test_uid
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND app_id=90006 AND event_type='GAMEEND'
), labelled AS (
 SELECT stat_date,user_id,salt_key,unique_id,unique_id_bar,play_id,bet_num,refund_num,bet_count,asset_id,noun_type,
        CASE WHEN mode_id=11 THEN 'Waje' WHEN mode_id=100 THEN 'WajeCoin' ELSE 'other_or_unknown_mode' END AS product_mode,
        CASE WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9150001 AND 9159999 THEN 'Tada'
             WHEN SAFE_CAST(play_id AS INT64) BETWEEN 9160001 AND 9169999 THEN 'PP' ELSE 'other_games' END AS provider
 FROM events WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND is_robot IS FALSE AND (is_test_uid IS NULL OR is_test_uid!=1)
)
SELECT IF(GROUPING(stat_date)=1,'period','daily') AS time_grain,
 COALESCE(stat_date,DATE '2026-08-01') AS date_key,product_mode,provider,
 COUNT(1) AS records,COUNT(DISTINCT user_id) AS users,
 COUNT(DISTINCT salt_key) AS distinct_log_keys,
 COUNTIF(salt_key IS NULL OR salt_key='') AS missing_log_key_records,
 COUNT(DISTINCT CONCAT(user_id,'|',play_id,'|',COALESCE(unique_id,'NULL'),'|',COALESCE(unique_id_bar,'NULL'))) AS distinct_user_game_round_keys,
 COUNTIF(unique_id IS NULL OR unique_id='') AS missing_round_key_records,
 COUNTIF(bet_num-COALESCE(refund_num,0)>0) AS positive_stake_records,
 COUNTIF(bet_count IS NULL) AS missing_bet_count_records,
 COUNTIF(asset_id IS NULL) AS missing_asset_records,
 COUNTIF(noun_type IS NULL OR noun_type='') AS missing_currency_records,
 ARRAY_AGG(DISTINCT asset_id IGNORE NULLS LIMIT 30) AS observed_asset_codes,
 ARRAY_AGG(DISTINCT noun_type IGNORE NULLS LIMIT 30) AS observed_currency_codes
FROM labelled
GROUP BY GROUPING SETS((stat_date,product_mode,provider),(product_mode,provider))
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY product_mode,provider,time_grain,date_key
LIMIT 1000;
""")
    profiles=base().split(', events AS (',1)[0]
    save('16_full_active_base.sql',profiles+""", active AS (
 SELECT target_day AS stat_date,user_id
 FROM `wajenigeria.origin_hfyl.realtime_edw_user_version_daily`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07' AND app_id=90006
), labelled AS (
 SELECT a.stat_date,a.user_id,COALESCE(p.channel_platform,'unmapped') AS channel_platform,
   CASE WHEN p.channel_platform IN ('APP_Android','APP_iOS') THEN 'APP' ELSE COALESCE(p.channel_platform,'unmapped') END AS platform,
   CASE WHEN p.registration_date IS NULL THEN 'unknown_registration'
        WHEN DATE_DIFF(a.stat_date,p.registration_date,DAY)<0 THEN 'invalid_registration'
        WHEN DATE_DIFF(a.stat_date,p.registration_date,DAY)<30 THEN 'new_30d' ELSE 'old_over_30d' END AS age_group
 FROM active a LEFT JOIN mapped_profiles p ON p.user_id=a.user_id
 WHERE a.stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
)
SELECT IF(GROUPING(stat_date)=1,'period','daily') AS time_grain,COALESCE(stat_date,DATE '2026-08-01') AS date_key,
 CASE WHEN GROUPING(platform)=0 THEN 'platform' WHEN GROUPING(channel_platform)=0 THEN 'subplatform' ELSE 'all_platforms' END AS segment_grain,
 COALESCE(platform,channel_platform,'all_platforms') AS platform_group,
 IF(GROUPING(age_group)=1,'all_ages',age_group) AS age_segment,
 COUNT(DISTINCT user_id) AS active_accounts,
 COUNT(DISTINCT CONCAT(user_id,'|',CAST(stat_date AS STRING))) AS active_account_days,
 COUNT(1) AS daily_version_rows
FROM labelled GROUP BY GROUPING SETS(
 (platform,age_group),(platform),(channel_platform,age_group),(channel_platform),
 (stat_date,platform,age_group),(stat_date,platform),(stat_date),(age_group),()
)
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY time_grain,date_key,segment_grain,platform_group,age_segment
LIMIT 1500;
""")
    save('17_full_games.sql',base()+"""SELECT
 IF(GROUPING(platform)=1,'APP_H5_combined',platform) AS platform_group,provider,play_id,
 COUNT(DISTINCT user_id) AS settlement_users,
 COUNT(DISTINCT IF(effective_stake>0,user_id,NULL)) AS bettors,
 COUNT(DISTINCT IF(effective_stake>0,CONCAT(user_id,'|',CAST(stat_date AS STRING)),NULL)) AS betting_user_days,
 COUNTIF(effective_stake>0) AS positive_stake_records,
 SUM(effective_stake) AS effective_stake_source_units,SUM(settlement) AS settlement_source_units,
 MIN(IF(effective_stake>0,stat_date,NULL)) AS first_observed_bet_date,
 MAX(IF(effective_stake>0,stat_date,NULL)) AS last_observed_bet_date,
 COUNT(DISTINCT IF(effective_stake>0,stat_date,NULL)) AS observed_betting_days
FROM labelled
WHERE product_mode='Waje' AND provider IN ('Tada','PP') AND platform IN ('APP','H5')
GROUP BY GROUPING SETS((platform,provider,play_id),(provider,play_id))
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY provider,play_id,platform_group
LIMIT 2000;
""")
    save('18_full_return.sql',base()+""", daily_bets AS (
 SELECT stat_date,user_id,platform,channel_platform,provider,age_group,play_id
 FROM labelled WHERE product_mode='Waje' AND effective_stake>0
 GROUP BY stat_date,user_id,platform,channel_platform,provider,age_group,play_id
), origins AS (
 SELECT user_id,platform,provider,MIN(stat_date) AS origin_date,
        ARRAY_AGG(age_group ORDER BY stat_date,age_group LIMIT 1)[OFFSET(0)] AS origin_age,
        ARRAY_AGG(STRUCT(stat_date,play_id) ORDER BY stat_date,play_id LIMIT 1)[OFFSET(0)].play_id AS origin_game
 FROM daily_bets WHERE provider IN ('Tada','PP') GROUP BY user_id,platform,provider
), states AS (
 SELECT o.user_id,o.platform,o.provider,o.origin_date,o.origin_age,obs AS observation_day,
        LOGICAL_OR(b.provider=o.provider) AS same_provider_return,
        LOGICAL_OR(b.provider=o.provider AND b.play_id=o.origin_game) AS first_game_return,
        COUNT(b.user_id)>0 AS any_game_return
 FROM origins o CROSS JOIN UNNEST([2,3,7,14,30]) obs
 LEFT JOIN daily_bets b ON b.user_id=o.user_id AND b.stat_date=DATE_ADD(o.origin_date,INTERVAL (obs-1) DAY)
 WHERE DATE_ADD(o.origin_date,INTERVAL (obs-1) DAY)<=DATE '2026-09-07'
 GROUP BY o.user_id,o.platform,o.provider,o.origin_date,o.origin_age,observation_day
)
SELECT platform,provider,IF(GROUPING(origin_age)=1,'all_ages',origin_age) AS age_segment,
 observation_day,IF(GROUPING(origin_date)=1,'max_mature','daily_cohort') AS cohort_scope,
 MIN(origin_date) AS first_origin_date,MAX(origin_date) AS last_origin_date,
 COUNT(1) AS eligible_accounts,
 COUNTIF(same_provider_return) AS same_provider_return_accounts,
 COUNTIF(first_game_return) AS selected_origin_game_return_accounts,
 COUNTIF(any_game_return AND NOT COALESCE(same_provider_return,FALSE)) AS other_provider_only_accounts,
 COUNTIF(NOT any_game_return) AS no_observed_bet_accounts
FROM states
GROUP BY GROUPING SETS((platform,provider,origin_age,observation_day),(platform,provider,observation_day),
 (platform,provider,origin_date,observation_day))
HAVING COUNT(1)>=10
ORDER BY platform,provider,cohort_scope,age_segment,observation_day,first_origin_date
LIMIT 2500;
""")
    print('Generated queries 15–18; not executed')

if __name__=='__main__':main()
