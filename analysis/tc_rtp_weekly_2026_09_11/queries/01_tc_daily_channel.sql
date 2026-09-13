WITH profiles AS (
  SELECT
    target_day AS biz_date,
    xl_id,
    ANY_VALUE(COALESCE(NULLIF(download_channel, ''), '(unknown)')) AS channel,
    COUNT(DISTINCT COALESCE(NULLIF(download_channel, ''), '(unknown)')) AS channel_versions
  FROM `wajenigeria.origin_hfyl.user_events`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
    AND app_id = 90006
    AND xl_id IS NOT NULL
  GROUP BY 1,2
), money_events AS (
  SELECT
    target_day AS biz_date,
    xl_id,
    CASE WHEN event_type = 'ORDER' THEN 'recharge' ELSE 'withdraw' END AS metric,
    CASE WHEN event_type = 'ORDER' THEN pay_amount ELSE cash_num / 100.0 END AS amount,
    CASE WHEN event_type = 'ORDER' THEN order_no ELSE serial_num END AS transaction_key
  FROM `wajenigeria.origin_hfyl.view_event_server`
  WHERE target_day BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
    AND app_id = 90006
    AND (
      (event_type = 'ORDER' AND is_success = 'pay_success')
      OR (event_type = 'WITHDRAW' AND log_event_type = 'server_event')
    )
), deduplicated AS (
  SELECT biz_date, xl_id, metric, transaction_key, MAX(amount) AS amount
  FROM money_events
  WHERE biz_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
    AND transaction_key IS NOT NULL
  GROUP BY 1,2,3,4
), enriched AS (
  SELECT
    e.biz_date,
    e.metric,
    e.amount,
    e.transaction_key,
    COALESCE(p.channel, '(unknown)') AS channel,
    p.xl_id IS NOT NULL AS profile_matched,
    COALESCE(p.channel_versions, 0) AS channel_versions
  FROM deduplicated e
  LEFT JOIN profiles p USING (biz_date, xl_id)
  WHERE e.biz_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
), daily AS (
  SELECT
    'daily' AS row_type,
    biz_date,
    CASE WHEN biz_date <= DATE '2026-09-03' THEN '基线：8月28日—9月3日' ELSE '本期：9月4—10日' END AS period,
    '(all)' AS channel,
    SUM(IF(metric='recharge',amount,0)) AS recharge,
    SUM(IF(metric='withdraw',amount,0)) AS withdraw,
    COUNT(DISTINCT IF(metric='recharge',transaction_key,NULL)) AS recharge_orders,
    COUNT(DISTINCT IF(metric='withdraw',transaction_key,NULL)) AS withdraw_orders,
    SUM(IF(NOT profile_matched,amount,0)) AS unmatched_amount,
    COUNTIF(channel_versions>1) AS conflicting_channel_rows
  FROM enriched
  WHERE biz_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
  GROUP BY 1,2,3,4
), channel_week AS (
  SELECT
    'channel_week' AS row_type,
    CAST(NULL AS DATE) AS biz_date,
    CASE WHEN biz_date <= DATE '2026-09-03' THEN '基线：8月28日—9月3日' ELSE '本期：9月4—10日' END AS period,
    channel,
    SUM(IF(metric='recharge',amount,0)) AS recharge,
    SUM(IF(metric='withdraw',amount,0)) AS withdraw,
    COUNT(DISTINCT IF(metric='recharge',transaction_key,NULL)) AS recharge_orders,
    COUNT(DISTINCT IF(metric='withdraw',transaction_key,NULL)) AS withdraw_orders,
    SUM(IF(NOT profile_matched,amount,0)) AS unmatched_amount,
    COUNTIF(channel_versions>1) AS conflicting_channel_rows
  FROM enriched
  WHERE biz_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
  GROUP BY 1,2,3,4
)
SELECT row_type,biz_date,period,channel,recharge,withdraw,
       SAFE_DIVIDE(withdraw,recharge) AS tc_rate,recharge_orders,withdraw_orders,
       unmatched_amount,conflicting_channel_rows
FROM daily
WHERE biz_date BETWEEN DATE '2026-08-28' AND DATE '2026-09-10'
UNION ALL
SELECT row_type,biz_date,period,channel,recharge,withdraw,
       SAFE_DIVIDE(withdraw,recharge),recharge_orders,withdraw_orders,
       unmatched_amount,conflicting_channel_rows
FROM channel_week
WHERE period IN ('基线：8月28日—9月3日','本期：9月4—10日')
ORDER BY row_type,biz_date,period,recharge DESC
LIMIT 3000;
