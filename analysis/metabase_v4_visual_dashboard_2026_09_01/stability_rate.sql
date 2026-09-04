-- Aggregate-only Android Fatal stability rate for V4.
-- No user, installation, session, event, issue, device, or stack value is returned.
-- first_session_id is used only inside COUNT(DISTINCT) as a deidentified active-subject proxy.

WITH crash AS (
  SELECT 'Android 主包' AS endpoint, 'com.hfhy.waje.special' AS app_package,
         is_fatal, event_id, firebase_session_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
  UNION ALL
  SELECT 'Android 传音新包', 'com.hfhy.wajecasino.game', is_fatal, event_id, firebase_session_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
  UNION ALL
  SELECT 'Android 传音老包', 'com.hfhy.wajecasino.palmgame', is_fatal, event_id, firebase_session_id
  FROM `wajenigeria.waje_ng_firebase_android_crashlytics.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
),
sessions AS (
  SELECT 'Android 主包' AS endpoint, 'com.hfhy.waje.special' AS app_package,
         session_id, first_session_id
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_waje_special_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
  UNION ALL
  SELECT 'Android 传音新包', 'com.hfhy.wajecasino.game', session_id, first_session_id
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_game_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
  UNION ALL
  SELECT 'Android 传音老包', 'com.hfhy.wajecasino.palmgame', session_id, first_session_id
  FROM `wajenigeria.waje_ng_firebase_android_sessions.com_hfhy_wajecasino_palmgame_ANDROID`
  WHERE DATE(event_timestamp, 'Africa/Lagos') BETWEEN DATE '2026-08-20' AND DATE '2026-08-26'
)
SELECT
  s.endpoint,
  10000 * SAFE_DIVIDE(
    COUNT(DISTINCT IF(c.is_fatal, s.first_session_id, NULL)),
    COUNT(DISTINCT s.first_session_id)
  ) AS fatal_per_10k
FROM sessions AS s
LEFT JOIN crash AS c
  ON s.app_package = c.app_package
 AND CAST(s.session_id AS STRING) = CAST(c.firebase_session_id AS STRING)
GROUP BY s.endpoint
ORDER BY fatal_per_10k DESC;
