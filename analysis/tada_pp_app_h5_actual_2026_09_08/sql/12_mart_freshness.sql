WITH tc AS (
 SELECT target_day AS stat_date
 FROM `wajenigeria.bigdata.tc_ratio`
 WHERE target_day BETWEEN DATE '2019-01-01' AND DATE '2026-09-07' AND app_id=90006
), gameplay AS (
 SELECT target_day AS stat_date
 FROM `wajenigeria.bigdata.daily_gameplay_multi_dimension`
 WHERE target_day BETWEEN DATE '2019-01-01' AND DATE '2026-09-07'
)
SELECT 'tc_mart_app90006' AS source,MIN(stat_date) AS first_date,MAX(stat_date) AS latest_date,
 COUNT(1) AS aggregate_rows,COUNT(DISTINCT stat_date) AS dates
FROM tc WHERE stat_date BETWEEN DATE '2019-01-01' AND DATE '2026-09-07'
UNION ALL
SELECT 'gameplay_mart_product_scope_unverified',MIN(stat_date),MAX(stat_date),COUNT(1),COUNT(DISTINCT stat_date)
FROM gameplay WHERE stat_date BETWEEN DATE '2019-01-01' AND DATE '2026-09-07'
LIMIT 10;
