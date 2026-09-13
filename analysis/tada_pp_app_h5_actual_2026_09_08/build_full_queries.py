"""Generate explicit bounded aggregate SQL using reviewed task-local mappings."""
import json
from pathlib import Path

P=Path(__file__).resolve().parent

def lit(value):
    return "'"+value.replace("'","''")+"'"

def base():
    mapping=json.loads((P/'channel-mapping.json').read_text())['rows']
    groups={name:[] for name in ['APP_Android','APP_iOS','H5','PWA_named']}
    for row in mapping:
        if row['platform_group'] in groups:groups[row['platform_group']].append(row['channel'])
    cases='\n'.join(f"WHEN channel_name IN ({','.join(map(lit,codes))}) THEN {lit(name)}" for name,codes in groups.items())
    return f"""WITH profile_candidates AS (
 SELECT user_id,register_time,xlid_time,download_channel,first_channel
 FROM `wajenigeria.origin_hfyl.user_xlid`
 WHERE target_day BETWEEN DATE '2019-01-01' AND DATE '2026-09-07'
   AND app_id=90006 AND user_id IS NOT NULL AND user_id!=''
), profiles AS (
 SELECT user_id,
        CASE WHEN register_time BETWEEN 1262304000000 AND UNIX_MILLIS(TIMESTAMP(DATE '2026-09-09','Africa/Lagos'))-1
             THEN DATE(TIMESTAMP_MILLIS(register_time),'Africa/Lagos') END AS registration_date,
        COALESCE(NULLIF(download_channel,''),NULLIF(first_channel,''),'UNKNOWN') AS channel_name
 FROM profile_candidates
 QUALIFY ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY IF(register_time>0,0,1),register_time,xlid_time,COALESCE(download_channel,first_channel,''))=1
), mapped_profiles AS (
 SELECT user_id,registration_date,channel_name,CASE {cases} ELSE 'unmapped' END AS channel_platform
 FROM profiles
), events AS (
 SELECT target_day AS stat_date,user_id,play_id,mode_id,bet_num,cash_settlement,refund_num,
        extra_num,bet_count,is_robot,is_test_uid
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND app_id=90006 AND event_type='GAMEEND'
), labelled AS (
 SELECT e.stat_date,DATE_TRUNC(e.stat_date,WEEK(MONDAY)) AS week_start,e.user_id,
        SAFE_CAST(e.play_id AS INT64) AS play_id,
        CASE WHEN e.mode_id=11 THEN 'Waje' WHEN e.mode_id=100 THEN 'WajeCoin' ELSE 'other_or_unknown_mode' END AS product_mode,
        COALESCE(p.channel_platform,'unmapped') AS channel_platform,
        CASE WHEN p.channel_platform IN ('APP_Android','APP_iOS') THEN 'APP' ELSE COALESCE(p.channel_platform,'unmapped') END AS platform,
        COALESCE(p.channel_name,'UNKNOWN') AS channel_name,
        CASE WHEN p.registration_date IS NULL THEN 'unknown_registration'
             WHEN DATE_DIFF(e.stat_date,p.registration_date,DAY)<0 THEN 'invalid_registration'
             WHEN DATE_DIFF(e.stat_date,p.registration_date,DAY)<30 THEN 'new_30d'
             ELSE 'old_over_30d' END AS age_group,
        CASE WHEN SAFE_CAST(e.play_id AS INT64) BETWEEN 9150001 AND 9159999 THEN 'Tada'
             WHEN SAFE_CAST(e.play_id AS INT64) BETWEEN 9160001 AND 9169999 THEN 'PP'
             ELSE 'other_games' END AS provider,
        CAST(e.bet_num AS BIGNUMERIC)-COALESCE(e.refund_num,0) AS effective_stake,
        CAST(e.cash_settlement AS BIGNUMERIC) AS settlement,
        e.refund_num,e.extra_num,e.bet_count
 FROM events e LEFT JOIN mapped_profiles p ON p.user_id=e.user_id
 WHERE e.stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND e.is_robot IS FALSE AND (e.is_test_uid IS NULL OR e.is_test_uid!=1)
)\n"""

def main():
    sql=base()+"""SELECT
 CASE WHEN GROUPING(stat_date)=0 THEN 'daily' WHEN GROUPING(week_start)=0 THEN 'weekly' ELSE 'period' END AS time_grain,
 COALESCE(stat_date,week_start,DATE '2026-08-01') AS date_key,
 product_mode,
 CASE WHEN GROUPING(platform)=0 THEN 'platform' WHEN GROUPING(channel_platform)=0 THEN 'subplatform' ELSE 'all_platforms' END AS segment_grain,
 COALESCE(platform,channel_platform,'all_platforms') AS platform_group,
 IF(GROUPING(provider)=1,'all_games',provider) AS provider_group,
 IF(GROUPING(age_group)=1,'all_ages',age_group) AS age_segment,
 COUNT(1) AS settlement_records,
 COUNT(DISTINCT user_id) AS settlement_users,
 COUNT(DISTINCT IF(effective_stake>0,user_id,NULL)) AS bettors,
 COUNT(DISTINCT IF(effective_stake>0,CONCAT(user_id,'|',CAST(stat_date AS STRING)),NULL)) AS betting_user_days,
 COUNTIF(effective_stake>0) AS positive_stake_records,
 SUM(effective_stake) AS effective_stake_source_units,
 SUM(settlement) AS settlement_source_units,
 SUM(COALESCE(extra_num,0)) AS extra_source_units,
 SUM(COALESCE(refund_num,0)) AS refund_source_units,
 SUM(bet_count) AS reported_bet_count,
 COUNTIF(bet_count IS NULL) AS missing_bet_count_records,
 COUNTIF(effective_stake IS NULL OR settlement IS NULL) AS missing_amount_records,
 COUNTIF(effective_stake<0) AS negative_effective_stake_records,
 COUNT(DISTINCT IF(effective_stake>0,play_id,NULL)) AS played_game_count
FROM labelled
GROUP BY GROUPING SETS (
 (product_mode,platform,provider,age_group),(product_mode,platform,age_group),
 (product_mode,platform,provider),(product_mode,platform),
 (product_mode,channel_platform,provider,age_group),(product_mode,channel_platform,age_group),
 (product_mode,channel_platform,provider),(product_mode,channel_platform),
 (product_mode,stat_date,platform,provider),(product_mode,stat_date,platform),
 (product_mode,week_start,platform,provider,age_group),(product_mode,week_start,platform,age_group),
 (product_mode,stat_date,provider),(product_mode,stat_date),
 (product_mode,provider,age_group),(product_mode,age_group),(product_mode,provider),(product_mode)
)
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY product_mode,time_grain,date_key,segment_grain,platform_group,age_segment,provider_group
LIMIT 3000;
"""
    (P/'sql/14_full_core.sql').write_text(sql)
    print('Generated sql/14_full_core.sql; read-only and aggregate-only; source unit reconciliation applied, final quality certification pending')

if __name__=='__main__':main()
