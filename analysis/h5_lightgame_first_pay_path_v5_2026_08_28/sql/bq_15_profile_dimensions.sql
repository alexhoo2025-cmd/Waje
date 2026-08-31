SELECT
  'history_to_2026-06-30' AS source,
  CAST(`注册方式` AS STRING) AS register_mode,
  COALESCE(NULLIF(`设备类型`, ''), '[blank]') AS device_type,
  COUNT(*) AS first_pay_users,
  MIN(`首充日期`) AS min_first_pay_time,
  MAX(`首充日期`) AS max_first_pay_time
FROM `wajenigeria.pubwaje.user_profiles`
WHERE `首充日期` BETWEEN TIMESTAMP('2026-06-16 00:00:00', 'Africa/Lagos')
                       AND TIMESTAMP('2026-06-30 23:59:59', 'Africa/Lagos')
GROUP BY 1, 2, 3

UNION ALL

SELECT
  'snapshot_2026-07-10_to_2026-08-10',
  CAST(`注册方式` AS STRING),
  COALESCE(NULLIF(`设备类型`, ''), '[blank]'),
  COUNT(*),
  MIN(`首充日期`),
  MAX(`首充日期`)
FROM `wajenigeria.pubwaje.user_profiles_2026-07-10_2026-08-10`
WHERE `首充日期` BETWEEN TIMESTAMP('2026-07-14 00:00:00', 'Africa/Lagos')
                       AND TIMESTAMP('2026-08-10 23:59:59', 'Africa/Lagos')
GROUP BY 1, 2, 3
ORDER BY source, first_pay_users DESC;
