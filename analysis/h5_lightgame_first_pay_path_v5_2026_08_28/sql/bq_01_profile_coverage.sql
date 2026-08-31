SELECT
  COUNT(*) AS profile_rows,
  APPROX_COUNT_DISTINCT(`用户id`) AS users,
  COUNTIF(`首充日期` IS NOT NULL) AS users_with_first_pay,
  MIN(`注册时间`) AS min_register_time,
  MAX(`注册时间`) AS max_register_time,
  MIN(`首充日期`) AS min_first_pay_time,
  MAX(`首充日期`) AS max_first_pay_time
FROM `wajenigeria.pubwaje.user_profiles`;

