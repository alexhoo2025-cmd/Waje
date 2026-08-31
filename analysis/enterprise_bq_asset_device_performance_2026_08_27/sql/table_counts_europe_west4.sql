-- Read-only metadata inventory: europe-west4 datasets only.
SELECT 'GE_90006' AS dataset_id, COUNT(*) AS table_or_view_count,
       COUNTIF(table_type = 'BASE TABLE') AS base_table_count,
       COUNTIF(table_type = 'VIEW') AS view_count,
       COUNTIF(table_type = 'MATERIALIZED VIEW') AS materialized_view_count
FROM `wajenigeria.GE_90006.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'ares_hfyl', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.ares_hfyl.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'ares_hfyl_test', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.ares_hfyl_test.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'bigdata', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.bigdata.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'origin_hfyl', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.origin_hfyl.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'pubwaje', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.pubwaje.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'track_hfyl', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.track_hfyl.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'waje_ng_firebase_h5', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.waje_ng_firebase_h5.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'waje_ng_firebase_ios', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.waje_ng_firebase_ios.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'waje_ng_firebase_ios_crashlytics', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.waje_ng_firebase_ios_crashlytics.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'waje_ng_firebase_ios_messaging', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.waje_ng_firebase_ios_messaging.INFORMATION_SCHEMA.TABLES`
UNION ALL SELECT 'waje_ng_firebase_ios_performance', COUNT(*), COUNTIF(table_type = 'BASE TABLE'), COUNTIF(table_type = 'VIEW'), COUNTIF(table_type = 'MATERIALIZED VIEW') FROM `wajenigeria.waje_ng_firebase_ios_performance.INFORMATION_SCHEMA.TABLES`
ORDER BY dataset_id;
