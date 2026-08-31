-- Waje GM Lifecycle V2 (Joint)
-- 04_lifecycle_report_queries.sql
-- 依赖：model_lifecycle_v2_joint_daily 已创建并完成字段认证。
-- 所有 {{...}} 应配置为 Metabase Field Filter 或受控 Dropdown。

-- ================================================================
-- Q01_lifecycle_overview
-- ================================================================
SELECT
    CASE WHEN {{display_mode}} = 'detail' THEN business_date END AS business_date,
    SUM(base_bet) AS total_base_bet,
    SUM(entire_bet) AS total_entire_bet,
    SUM(base_actual_profit) AS total_base_actual_profit,
    SUM(entire_actual_profit) AS total_entire_actual_profit,
    SUM(base_expected_profit) AS total_base_expected_profit,
    SUM(entire_expected_profit) AS total_entire_expected_profit,
    CASE WHEN SUM(base_bet) = 0 THEN NULL
         ELSE 1 - SUM(base_actual_profit) / SUM(base_bet) END AS total_base_actual_rtp,
    CASE WHEN SUM(entire_bet) = 0 THEN NULL
         ELSE 1 - SUM(entire_actual_profit) / SUM(entire_bet) END AS total_entire_actual_rtp,
    SUM(base_expected_rtp * base_bet) / NULLIF(SUM(base_bet), 0) AS total_base_expected_rtp,
    SUM(entire_expected_rtp * entire_bet) / NULLIF(SUM(entire_bet), 0) AS total_entire_expected_rtp,
    COUNT(DISTINCT lifecycle_user_key) AS total_user_count,
    SUM(entire_actual_profit) / NULLIF(COUNT(DISTINCT lifecycle_user_key), 0) AS avg_actual_profit_per_user,
    SUM(adjusted_profit) AS adjusted_profit,
    MAX(data_cutoff_at) AS data_cutoff_at,
    MAX(data_status) AS data_status
FROM model_lifecycle_v2_joint_daily
WHERE 1=1
  [[AND {{business_date}}]] [[AND {{data_scope}}]] [[AND {{population_type}}]]
  [[AND {{app_version}}]] [[AND {{package_id}}]] [[AND {{distribution_channel_id}}]]
  [[AND {{attribution_media_id}}]] [[AND {{attribution_channel_id}}]]
  [[AND {{data_status}}]]
GROUP BY CASE WHEN {{display_mode}} = 'detail' THEN business_date END
ORDER BY business_date;

-- ================================================================
-- Q02_lifecycle_pool_detail
-- ================================================================
SELECT
    CASE WHEN {{display_mode}} = 'detail' THEN business_date END AS business_date,
    display_lifecycle, game_id, game_name,
    SUM(expected_rtp * entire_bet) / NULLIF(SUM(entire_bet), 0) AS expected_rtp,
    SUM(profit_ratio_numerator) / NULLIF(SUM(profit_ratio_denominator), 0) AS profit_ratio_per_10000,
    SUM(base_expected_profit) AS base_expected_profit,
    SUM(base_actual_profit) AS base_actual_profit,
    SUM(base_bet) AS base_bet,
    1 - SUM(base_actual_profit) / NULLIF(SUM(entire_bet), 0) AS detail_page_base_actual_rtp,
    SUM(bankruptcy_protection_amount) AS bankruptcy_protection_amount,
    SUM(user_profit_control_amount) AS user_profit_control_amount,
    SUM(entire_expected_profit) AS entire_expected_profit,
    SUM(entire_actual_profit) AS entire_actual_profit,
    SUM(entire_bet) AS entire_bet,
    SUM(entire_bet) / NULLIF(SUM(SUM(entire_bet)) OVER (), 0) AS entire_bet_share,
    1 - SUM(entire_actual_profit) / NULLIF(SUM(entire_bet), 0) AS entire_actual_rtp,
    MAX(data_status) AS data_status
FROM model_lifecycle_v2_joint_daily
WHERE 1=1
  [[AND {{business_date}}]] [[AND {{data_scope}}]] [[AND {{population_type}}]]
  [[AND {{app_version}}]] [[AND {{package_id}}]] [[AND {{distribution_channel_id}}]]
  [[AND {{attribution_media_id}}]] [[AND {{attribution_channel_id}}]]
  [[AND {{display_lifecycle}}]] [[AND {{game_id}}]] [[AND {{data_status}}]]
GROUP BY CASE WHEN {{display_mode}} = 'detail' THEN business_date END,
         display_lifecycle, game_id, game_name
ORDER BY entire_bet DESC, display_lifecycle, game_id;

-- ================================================================
-- Q03_lifecycle_game_summary
-- ================================================================
SELECT
    CASE WHEN {{display_mode}} = 'detail' THEN business_date END AS business_date,
    game_id, game_name, provider, is_joint,
    SUM(base_bet) AS base_bet,
    SUM(base_expected_profit) AS base_expected_profit,
    SUM(base_actual_profit) AS base_actual_profit,
    1 - SUM(base_actual_profit) / NULLIF(SUM(base_bet), 0) AS base_actual_rtp,
    SUM(base_expected_rtp * base_bet) / NULLIF(SUM(base_bet), 0) AS base_expected_rtp,
    SUM(bankruptcy_protection_amount) AS bankruptcy_protection_amount,
    SUM(user_profit_control_amount) AS user_profit_control_amount,
    SUM(bankruptcy_protection_amount) / NULLIF(SUM(base_bet), 0) AS bankruptcy_protection_to_bet,
    SUM(user_profit_control_amount) / NULLIF(SUM(base_bet), 0) AS user_profit_control_to_bet,
    SUM(entire_bet) AS entire_bet,
    SUM(entire_expected_profit) AS entire_expected_profit,
    SUM(entire_actual_profit) AS entire_actual_profit,
    1 - SUM(entire_actual_profit) / NULLIF(SUM(entire_bet), 0) AS entire_actual_rtp,
    SUM(entire_expected_rtp * entire_bet) / NULLIF(SUM(entire_bet), 0) AS entire_expected_rtp,
    SUM(entire_bet) / NULLIF(SUM(SUM(entire_bet)) OVER (), 0) AS entire_bet_share,
    MAX(data_status) AS data_status
FROM model_lifecycle_v2_joint_daily
WHERE 1=1
  [[AND {{business_date}}]] [[AND {{data_scope}}]] [[AND {{population_type}}]]
  [[AND {{app_version}}]] [[AND {{package_id}}]] [[AND {{distribution_channel_id}}]]
  [[AND {{attribution_media_id}}]] [[AND {{attribution_channel_id}}]]
  [[AND {{game_id}}]] [[AND {{data_status}}]]
GROUP BY CASE WHEN {{display_mode}} = 'detail' THEN business_date END,
         game_id, game_name, provider, is_joint
ORDER BY entire_bet DESC;

-- ================================================================
-- Q04_lifecycle_return_by_lifecycle
-- ================================================================
SELECT
    CASE WHEN {{display_mode}} = 'detail' THEN business_date END AS business_date,
    display_lifecycle,
    SUM(base_bet) AS base_bet,
    SUM(base_actual_profit) AS base_actual_profit,
    SUM(base_expected_profit) AS base_expected_profit,
    1 - SUM(base_actual_profit) / NULLIF(SUM(base_bet), 0) AS summary_base_actual_rtp,
    SUM(base_expected_rtp * base_bet) / NULLIF(SUM(base_bet), 0) AS base_expected_rtp,
    SUM(bankruptcy_protection_amount) AS bankruptcy_protection_amount,
    SUM(user_profit_control_amount) AS user_profit_control_amount,
    SUM(entire_bet) AS entire_bet,
    SUM(entire_bet) / NULLIF(SUM(SUM(entire_bet)) OVER (), 0) AS entire_bet_share,
    SUM(entire_actual_profit) AS entire_actual_profit,
    SUM(entire_expected_profit) AS entire_expected_profit,
    1 - SUM(entire_actual_profit) / NULLIF(SUM(entire_bet), 0) AS entire_actual_rtp,
    SUM(entire_expected_rtp * entire_bet) / NULLIF(SUM(entire_bet), 0) AS entire_expected_rtp,
    COUNT(DISTINCT lifecycle_user_key) AS user_count,
    SUM(entire_actual_profit) / NULLIF(COUNT(DISTINCT lifecycle_user_key), 0) AS avg_actual_profit_per_user,
    MAX(data_status) AS data_status
FROM model_lifecycle_v2_joint_daily
WHERE 1=1
  [[AND {{business_date}}]] [[AND {{data_scope}}]] [[AND {{population_type}}]]
  [[AND {{app_version}}]] [[AND {{package_id}}]] [[AND {{distribution_channel_id}}]]
  [[AND {{attribution_media_id}}]] [[AND {{attribution_channel_id}}]]
  [[AND {{display_lifecycle}}]] [[AND {{data_status}}]]
GROUP BY CASE WHEN {{display_mode}} = 'detail' THEN business_date END,
         display_lifecycle
ORDER BY display_lifecycle;

-- ================================================================
-- Q05_lifecycle_payment_by_lifecycle
-- ================================================================
SELECT
    CASE WHEN {{display_mode}} = 'detail' THEN business_date END AS business_date,
    display_lifecycle,
    COUNT(DISTINCT lifecycle_user_key) AS user_count,
    SUM(recharge_count) AS recharge_count,
    SUM(recharge_amount) AS recharge_amount,
    SUM(repeat_recharge_count) AS repeat_recharge_count,
    SUM(repeat_recharge_amount) AS repeat_recharge_amount,
    SUM(withdraw_count) AS withdraw_count,
    SUM(withdraw_amount) AS withdraw_amount,
    SUM(flow_recharge_numerator) / NULLIF(SUM(flow_recharge_denominator), 0) AS avg_flow_recharge_ratio,
    SUM(recharge_amount - withdraw_amount) AS revenue,
    SUM(tx_amount) AS tx_amount,
    SUM(recharge_amount - withdraw_amount) / NULLIF(COUNT(DISTINCT lifecycle_user_key), 0) AS avg_actual_revenue_per_user,
    SUM(tc_numerator) / NULLIF(SUM(tc_denominator), 0) AS tc_ratio,
    SUM(loss_numerator) / NULLIF(SUM(loss_denominator), 0) AS loss_coefficient,
    SUM(absolute_bankrupt_count) AS absolute_bankrupt_count,
    SUM(absolute_bankrupt_count) / NULLIF(COUNT(DISTINCT lifecycle_user_key), 0) AS avg_absolute_bankrupt_count,
    MAX(data_status) AS data_status
FROM model_lifecycle_v2_joint_daily
WHERE 1=1
  [[AND {{business_date}}]] [[AND {{data_scope}}]] [[AND {{population_type}}]]
  [[AND {{app_version}}]] [[AND {{package_id}}]] [[AND {{distribution_channel_id}}]]
  [[AND {{attribution_media_id}}]] [[AND {{attribution_channel_id}}]]
  [[AND {{display_lifecycle}}]] [[AND {{data_status}}]]
GROUP BY CASE WHEN {{display_mode}} = 'detail' THEN business_date END,
         display_lifecycle
ORDER BY display_lifecycle;

-- 说明：lifecycle_user_key 是隐藏去重键，不得作为查询结果返回。
-- tc_numerator/denominator、flow_recharge_numerator/denominator、
-- loss_numerator/denominator 必须由授权 Model/View 提供。
