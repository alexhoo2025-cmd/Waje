WITH profile_candidates AS (
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
 SELECT user_id,registration_date,channel_name,CASE WHEN channel_name IN ('PACHAMPIONS','PAPAWJBETCY2','PAWAJEPALM2','PAWAJEPALMS','PAWAJESPOPAY','PAWAJEXENDER','PAWajespecia','PAgoogleplay','WajeSpecial') THEN 'APP_Android'
WHEN channel_name IN ('1016246163569761','1163272865598617','1679734739569802','1693027911335063','1760719951146036','1807677293050348','1817271422343789','927128656153268','PAWAJEIOS','adjustqiqdbtawmebkFacebook','adjustqiqdbtawmebkGoogleAds','adjustqiqdbtawmebkOrganic') THEN 'APP_iOS'
WHEN channel_name IN ('1057805740332057','1086073807708718','1268361438340480','1360891245684659','1488400826662700','1545741160000078','1584420786411834','1603683537460322','1707128760547457','1747604103','1752545802277475','2319680875136934','2545521782446776','2730368513961225','4308954285992033','4888457997','5214811898','5725818139','6143498115','771602205049164','9281932950','PAOPAYLIANYU','PAPAWAJECJ','PAPAWAJEH5GA','PAPAWAJEH5SU','PAWAJEBETH5','PAWAJEH5','PAWAJEH5APL','PAWAJEH5CY','PAWAJEH5DXYQ','PAWAJEH5FB','PAWAJEH5FUN','PAWAJEH5GEO','PAWAJEH5GG','PAWAJEH5JOY','PAWAJEH5LD','PAWAJEH5M01','PAWAJEH5M02','PAWAJEH5M03','PAWAJEH5M04','PAWAJEH5M05','PAWAJEH5M06','PAWAJEH5M07','PAWAJEH5M08','PAWAJEH5M09','PAWAJEH5M10','PAWAJEH5MB','PAWAJEH5MB2','PAWAJEH5MB3','PAWAJEH5MB4','PAWAJEH5MB5','PAWAJEH5NAT','PAWAJEH5OP','PAWAJEH5OP2','PAWAJEH5OP3','PAWAJEH5OP4','PAWAJEH5OP5','PAWAJEH5OP6','PAWAJEH5OP7','PAWAJEH5OP8','PAWAJEH5OPAD','PAWAJEH5PALM','PAWAJEH5PHX','PAWAJEH5PLAY','PAWAJEH5PP','PAWAJEH5PW','PAWAJEH5PW2','PAWAJEH5PW3','PAWAJEH5PWCY','PAWAJEH5PWIN','PAWAJEH5PWW','PAWAJEH5SU','PAWAJEH5TG01','PAWAJEH5TG02','PAWAJEH5TG03','PAXENDERH5') THEN 'H5'
WHEN channel_name IN ('1150288483928367','1205296008205924','PAPWAT031224','PAWAJEH5PWA','PAWAJEH5PWAT') THEN 'PWA_named' ELSE 'unmapped' END AS channel_platform
 FROM profiles
), events AS (
 SELECT target_day AS stat_date,user_id,play_id,mode_id,bet_num,cash_settlement,refund_num,
        extra_num,bet_count,is_robot,is_test_uid,salt_key,unique_id,unique_id_bar,server_time
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND app_id=90006 AND event_type='GAMEEND' AND target_day IN (DATE '2026-08-05',DATE '2026-08-25',DATE '2026-08-30')
), ranked_events AS (
 SELECT stat_date,user_id,play_id,mode_id,bet_num,cash_settlement,refund_num,extra_num,bet_count,is_robot,is_test_uid,
 ROW_NUMBER() OVER(PARTITION BY stat_date,user_id,play_id,unique_id,unique_id_bar ORDER BY SAFE_CAST(server_time AS INT64) DESC,salt_key DESC) AS round_rank,
 COUNT(DISTINCT TO_JSON_STRING(STRUCT(bet_num,cash_settlement,refund_num,extra_num,mode_id))) OVER(PARTITION BY stat_date,user_id,play_id,unique_id,unique_id_bar) AS amount_variants
 FROM events
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
        e.refund_num,e.extra_num,e.bet_count,e.round_rank,e.amount_variants
 FROM ranked_events e LEFT JOIN mapped_profiles p ON p.user_id=e.user_id
 WHERE e.stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND e.is_robot IS FALSE AND (e.is_test_uid IS NULL OR e.is_test_uid!=1)
)
SELECT
 CASE WHEN GROUPING(stat_date)=0 THEN 'core_correction' WHEN GROUPING(play_id)=0 THEN 'game_correction' ELSE 'quality_total' END AS correction_grain,
 stat_date,product_mode,channel_platform,platform,provider,age_group,play_id,
 COUNT(DISTINCT user_id) AS population_accounts,
 COUNTIF(round_rank>1) AS duplicate_records,
 COUNTIF(round_rank>1 AND effective_stake>0) AS duplicate_positive_records,
 SUM(IF(round_rank>1,effective_stake,0)) AS duplicate_stake_source_units,
 SUM(IF(round_rank>1,settlement,0)) AS duplicate_settlement_source_units,
 SUM(IF(round_rank>1,COALESCE(extra_num,0),0)) AS duplicate_extra_source_units,
 SUM(IF(round_rank>1,COALESCE(refund_num,0),0)) AS duplicate_refund_source_units,
 COUNTIF(round_rank>1 AND amount_variants>1) AS duplicate_records_with_conflicting_amounts
FROM labelled
GROUP BY GROUPING SETS((stat_date,product_mode,channel_platform,platform,provider,age_group),
 (product_mode,platform,provider,play_id),(product_mode,provider))
HAVING COUNT(DISTINCT user_id)>=10 AND COUNTIF(round_rank>1)>0
ORDER BY correction_grain,stat_date,product_mode,platform,provider,play_id
LIMIT 500;
