WITH events AS (
  SELECT
    target_day AS biz_date,
    CASE WHEN event_type='ORDER' THEN '充值' ELSE '提现' END AS metric,
    CASE WHEN event_type='ORDER' THEN order_no ELSE serial_num END AS transaction_key,
    user_id,
    CASE WHEN event_type='ORDER' THEN pay_amount ELSE cash_num/100.0 END AS amount
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
    AND app_id=90006
    AND ((event_type='ORDER' AND is_success='pay_success') OR (event_type='WITHDRAW' AND log_event_type='server_event'))
), deduplicated AS (
  SELECT biz_date,metric,transaction_key,ANY_VALUE(user_id) AS user_id,MAX(amount) AS amount
  FROM events
  WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
    AND transaction_key IS NOT NULL AND amount>=0
  GROUP BY 1,2,3
), labeled AS (
  SELECT biz_date,metric,transaction_key,user_id,amount,IF(biz_date=DATE '2026-09-10','9月10日','9月4—9日') AS period,
    CASE WHEN amount<1000 THEN '<1千' WHEN amount<5000 THEN '1千—5千'
         WHEN amount<20000 THEN '5千—2万' WHEN amount<100000 THEN '2万—10万' ELSE '10万及以上' END AS amount_band
  FROM deduplicated
  WHERE biz_date BETWEEN DATE '2026-09-04' AND DATE '2026-09-10'
), transaction_rank AS (
  SELECT biz_date,metric,transaction_key,user_id,amount,period,amount_band,
         PERCENT_RANK() OVER(PARTITION BY metric,period ORDER BY amount DESC) AS amount_rank
  FROM labeled
), transaction_stats AS (
  SELECT metric,period,COUNT(*) AS observations,SUM(amount) AS total_amount,AVG(amount) AS mean_amount,
    APPROX_QUANTILES(amount,100)[OFFSET(50)] AS p50,
    APPROX_QUANTILES(amount,100)[OFFSET(90)] AS p90,
    APPROX_QUANTILES(amount,100)[OFFSET(99)] AS p99,
    SAFE_DIVIDE(SUM(IF(amount_rank<=0.01,amount,0)),SUM(amount)) AS top_1pct_share
  FROM transaction_rank GROUP BY 1,2
), user_amount AS (
  SELECT metric,period,user_id,SUM(amount) AS amount
  FROM labeled WHERE user_id IS NOT NULL GROUP BY 1,2,3
), user_rank AS (
  SELECT metric,period,user_id,amount,
         PERCENT_RANK() OVER(PARTITION BY metric,period ORDER BY amount DESC) AS amount_rank
  FROM user_amount
), user_stats AS (
  SELECT metric,period,COUNT(*) AS observations,SUM(amount) AS total_amount,AVG(amount) AS mean_amount,
    APPROX_QUANTILES(amount,100)[OFFSET(50)] AS p50,
    APPROX_QUANTILES(amount,100)[OFFSET(90)] AS p90,
    APPROX_QUANTILES(amount,100)[OFFSET(99)] AS p99,
    SAFE_DIVIDE(SUM(IF(amount_rank<=0.01,amount,0)),SUM(amount)) AS top_1pct_share
  FROM user_rank GROUP BY 1,2 HAVING observations>=10
), bands AS (
  SELECT metric,period,amount_band,COUNT(*) AS observations,SUM(amount) AS total_amount
  FROM labeled GROUP BY 1,2,3
)
SELECT '交易分布' AS row_type,metric,period,'(all)' AS bucket,observations,total_amount,mean_amount,p50,p90,p99,top_1pct_share
FROM transaction_stats WHERE period IN ('9月10日','9月4—9日')
UNION ALL
SELECT '用户分布',metric,period,'(all)',observations,total_amount,mean_amount,p50,p90,p99,top_1pct_share
FROM user_stats WHERE period IN ('9月10日','9月4—9日')
UNION ALL
SELECT '金额档位',metric,period,amount_band,observations,total_amount,
       CAST(NULL AS FLOAT64),CAST(NULL AS FLOAT64),CAST(NULL AS FLOAT64),CAST(NULL AS FLOAT64),CAST(NULL AS FLOAT64)
FROM bands WHERE period IN ('9月10日','9月4—9日')
ORDER BY row_type,metric,period,total_amount DESC
LIMIT 3000;
