-- Full requested window: check candidate marts before using their totals.
-- Row sums are diagnostic only until dimension overlap and units are certified.
WITH activity AS (
 SELECT target_day AS stat_date,channel,sub_channel,traffic_source_type,
        dayly_users,game_users,game_count,pay_users_count,pay_amount,audit_cash
 FROM `wajenigeria.ares_hfyl.user_activety_indicators_downloadchannel`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07' AND app_id=90006
), tc AS (
 SELECT target_day AS stat_date,download_channel,first_channel,pay_amount,withdraw_amount
 FROM `wajenigeria.bigdata.tc_ratio`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07' AND app_id=90006
), gameplay AS (
 SELECT target_day AS stat_date,channel_package,play_id,paid_users,free_users
 FROM `wajenigeria.bigdata.daily_gameplay_multi_dimension`
 WHERE target_day BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
)
SELECT 'activity_mart' AS source,stat_date,COUNT(1) AS source_rows,
 COUNT(DISTINCT channel) AS channel_count,
 SUM(dayly_users) AS user_count_row_sum,SUM(game_users) AS game_user_count_row_sum,
 SUM(game_count) AS game_count_row_sum,SUM(pay_amount) AS pay_amount_row_sum,
 SUM(audit_cash) AS withdraw_amount_row_sum,
 COUNTIF(channel IS NULL OR channel IN ('-9999','0','all','ALL','全部')) AS possible_total_channel_rows,
 ARRAY_AGG(DISTINCT traffic_source_type IGNORE NULLS LIMIT 20) AS traffic_types
FROM activity WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
GROUP BY stat_date HAVING SUM(dayly_users)>=10
UNION ALL
SELECT 'tc_mart',stat_date,COUNT(1),COUNT(DISTINCT download_channel),
 CAST(NULL AS INT64),CAST(NULL AS INT64),CAST(NULL AS INT64),SUM(pay_amount),SUM(withdraw_amount),
 COUNTIF(download_channel IS NULL OR download_channel IN ('-9999','0','all','ALL','全部')),
 CAST(NULL AS ARRAY<STRING>)
FROM tc WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
GROUP BY stat_date
UNION ALL
SELECT 'gameplay_mart_product_scope_unverified',stat_date,COUNT(1),COUNT(DISTINCT channel_package),
 SUM(paid_users)+SUM(free_users),CAST(NULL AS INT64),CAST(NULL AS INT64),
 CAST(NULL AS FLOAT64),CAST(NULL AS FLOAT64),
 COUNTIF(channel_package IS NULL OR channel_package IN ('-9999','0','all','ALL','全部')),
 CAST(NULL AS ARRAY<STRING>)
FROM gameplay WHERE stat_date BETWEEN DATE '2026-08-01' AND DATE '2026-09-07'
GROUP BY stat_date HAVING SUM(paid_users)+SUM(free_users)>=10
ORDER BY source,stat_date
LIMIT 200;
