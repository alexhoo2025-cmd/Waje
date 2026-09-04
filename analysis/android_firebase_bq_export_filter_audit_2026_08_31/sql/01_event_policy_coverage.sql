-- Compare protected anchors with exclude candidates at aggregate level.
-- No user identifiers, order identifiers, parameter values or raw rows are returned.
WITH event_policy AS (
  SELECT 'first_open' AS event_name, 'keep' AS policy UNION ALL
  SELECT 'session_start', 'keep' UNION ALL
  SELECT 'register', 'keep' UNION ALL
  SELECT 'notification_receive', 'exclude_candidate' UNION ALL
  SELECT 'notification_dismiss', 'exclude_candidate' UNION ALL
  SELECT 'user_engagement', 'exclude_candidate' UNION ALL
  SELECT 'app_remove', 'exclude_candidate' UNION ALL
  SELECT 'screen_view', 'conditional_keep' UNION ALL
  SELECT 'recharge', 'choose_one' UNION ALL
  SELECT 'rechargeDollar', 'choose_one' UNION ALL
  SELECT 'rechargeFix', 'exclude_candidate' UNION ALL
  SELECT 'rechargeAndWithdrawTotalTimes', 'exclude_candidate'
), daily AS (
  SELECT
    PARSE_DATE('%Y%m%d', _TABLE_SUFFIX) AS event_day,
    event_name,
    COUNT(*) AS event_count
  FROM `wajenigeria.waje_ng_firebase_android.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20260820' AND '20260826'
    AND platform = 'ANDROID'
  GROUP BY event_day, event_name
)
SELECT
  d.event_day,
  COALESCE(p.policy, 'unclassified') AS policy,
  SUM(d.event_count) AS event_count,
  COUNT(DISTINCT d.event_name) AS event_type_count
FROM daily d
LEFT JOIN event_policy p USING (event_name)
GROUP BY d.event_day, policy
ORDER BY d.event_day, policy;
