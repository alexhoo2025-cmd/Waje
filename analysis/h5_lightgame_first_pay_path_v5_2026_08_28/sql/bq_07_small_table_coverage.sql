SELECT 'first_pay_rate' AS source,
       COUNT(*) AS row_count,
       MIN(target_day) AS min_day,
       MAX(target_day) AS max_day
FROM `wajenigeria.bigdata.first_pay_rate`
UNION ALL
SELECT 'daily_gameplay_multi_dimension', COUNT(*), MIN(target_day), MAX(target_day)
FROM `wajenigeria.bigdata.daily_gameplay_multi_dimension`
UNION ALL
SELECT 'first_pay_retention', COUNT(*), MIN(target_day), MAX(target_day)
FROM `wajenigeria.bigdata.first_pay_retention`
UNION ALL
SELECT 'sys_game', COUNT(*), NULL, NULL
FROM `wajenigeria.origin_hfyl.sys_game`;
