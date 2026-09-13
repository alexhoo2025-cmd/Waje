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
 SELECT target_day AS stat_date,user_id,event_type,is_success,is_accept,noun_type,asset_id,
        pay_amount,cash_num,change_count,order_no,serial_num,salt_key,server_time,is_test_uid
 FROM `wajenigeria.origin_hfyl.realtime_event_server`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
   AND app_id=90006 AND event_type IN ('ORDER','WITHDRAW','AUDIT')
), dedup AS (
 SELECT stat_date,user_id,event_type,is_success,is_accept,noun_type,asset_id,pay_amount,cash_num,change_count
 FROM events WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
  AND (is_test_uid IS NULL OR is_test_uid!=1)
  AND (event_type!='ORDER' OR is_success='pay_success')
 QUALIFY ROW_NUMBER() OVER(PARTITION BY event_type,is_success,is_accept,COALESCE(NULLIF(order_no,''),NULLIF(serial_num,''),salt_key)
   ORDER BY SAFE_CAST(server_time AS INT64) DESC)=1
), labelled AS (
 SELECT e.stat_date,e.user_id,e.event_type,e.is_accept,e.noun_type,e.asset_id,e.pay_amount,e.cash_num,e.change_count,
 CASE WHEN p.channel_platform IN ('APP_Android','APP_iOS') THEN 'APP' ELSE COALESCE(p.channel_platform,'unmapped') END AS platform,
 CASE WHEN p.registration_date IS NULL THEN 'unknown_registration'
      WHEN DATE_DIFF(e.stat_date,p.registration_date,DAY)<0 THEN 'invalid_registration'
      WHEN DATE_DIFF(e.stat_date,p.registration_date,DAY)<30 THEN 'new_30d' ELSE 'old_over_30d' END AS age_group
 FROM dedup e LEFT JOIN mapped_profiles p ON p.user_id=e.user_id
)
SELECT IF(GROUPING(stat_date)=1,'period','daily') AS time_grain,COALESCE(stat_date,DATE '2026-08-01') AS date_key,
 IF(GROUPING(platform)=1,'all_platforms',platform) AS platform_group,
 IF(GROUPING(age_group)=1,'all_ages',age_group) AS age_segment,
 event_type,is_accept,noun_type,asset_id,
 COUNT(1) AS dedup_events,COUNT(DISTINCT user_id) AS accounts,
 SUM(pay_amount) AS paid_amount_native,SUM(cash_num) AS cash_num_native,SUM(change_count) AS change_count_native
FROM labelled
GROUP BY GROUPING SETS((platform,age_group,event_type,is_accept,noun_type,asset_id),(platform,event_type,is_accept,noun_type,asset_id),
 (stat_date,platform,event_type,is_accept,noun_type,asset_id),(event_type,is_accept,noun_type,asset_id))
HAVING COUNT(DISTINCT user_id)>=10
ORDER BY event_type,time_grain,date_key,platform_group,age_segment,is_accept
LIMIT 1500;
