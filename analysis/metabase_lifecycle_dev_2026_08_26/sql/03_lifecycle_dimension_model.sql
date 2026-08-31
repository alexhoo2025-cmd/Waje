-- Waje GM Lifecycle V2 (Joint)
-- 03_lifecycle_dimension_model.sql
-- 用途：授权 Model/View 字段契约和历史维度关联模板。
-- <...> 占位来源必须由数据开发替换为已授权真实表/视图。

WITH lifecycle_fact AS (
    SELECT
        business_date, data_scope, population_type, display_lifecycle,
        game_id, real_profit, expected_profit, adjusted_profit,
        entire_bet, bankruptcy_bet, bankruptcy_profit,
        control_bet, control_profit, expected_rtp,
        real_reserved, expected_reserved, actual_profit, base_bet,
        base_actual_profit, base_expected_profit, entire_expected_profit,
        entire_actual_profit, entire_actual_rtp,
        profit_ratio_numerator, profit_ratio_denominator,
        flow_recharge_numerator, flow_recharge_denominator,
        tc_numerator, tc_denominator, loss_numerator, loss_denominator,
        lifecycle_user_key,
        recharge_amount, repeat_recharge_amount, withdraw_amount,
        controlled_user_count, controlled_count,
        absolute_bankrupt_user_count, absolute_bankrupt_count,
        snapshot_time, data_status, metric_version, data_cutoff_at
    FROM <authorized_lifecycle_v2_pivot>
),
game_dimension AS (
    SELECT
        game_id, game_name, game_type, provider, is_joint, is_self_developed
    FROM <authorized_game_dimension>
),
historical_surface_dimension AS (
    SELECT
        business_date, game_id, app_version, package_id,
        distribution_channel_id, attribution_media_id, attribution_channel_id
    FROM <authorized_historical_surface_dimension>
)
SELECT
    f.business_date,
    f.data_scope,
    f.population_type,
    f.display_lifecycle,
    f.game_id,
    COALESCE(g.game_name, 'unknown') AS game_name,
    COALESCE(g.game_type, 'unknown') AS game_type,
    COALESCE(g.provider, 'unknown') AS provider,
    COALESCE(g.is_joint, FALSE) AS is_joint,
    COALESCE(g.is_self_developed, FALSE) AS is_self_developed,
    COALESCE(s.app_version, 'not_available') AS app_version,
    COALESCE(s.package_id, 'not_available') AS package_id,
    COALESCE(s.distribution_channel_id, 'not_available') AS distribution_channel_id,
    COALESCE(s.attribution_media_id, 'not_available') AS attribution_media_id,
    COALESCE(s.attribution_channel_id, 'not_available') AS attribution_channel_id,
    f.real_profit,
    f.expected_profit,
    f.adjusted_profit,
    f.entire_bet,
    f.bankruptcy_bet,
    f.bankruptcy_profit,
    f.control_bet,
    f.control_profit,
    f.expected_rtp,
    f.real_reserved,
    f.expected_reserved,
    f.actual_profit,
    f.base_bet,
    f.base_actual_profit,
    f.base_expected_profit,
    f.entire_expected_profit,
    f.entire_actual_profit,
    CASE WHEN f.base_bet = 0 THEN NULL
         ELSE 1 - f.base_actual_profit / f.base_bet END AS summary_base_actual_rtp,
    CASE WHEN f.entire_bet = 0 THEN NULL
         ELSE 1 - f.base_actual_profit / f.entire_bet END AS detail_page_base_actual_rtp,
    f.entire_actual_rtp,
    f.expected_rtp AS entire_expected_rtp,
    f.profit_ratio_numerator,
    f.profit_ratio_denominator,
    f.flow_recharge_numerator,
    f.flow_recharge_denominator,
    f.tc_numerator,
    f.tc_denominator,
    f.loss_numerator,
    f.loss_denominator,
    f.lifecycle_user_key,
    CASE WHEN f.expected_rtp = 0 THEN NULL
         ELSE f.entire_actual_rtp / f.expected_rtp - 1 END AS entire_rtp_gap,
    f.recharge_amount,
    f.repeat_recharge_amount,
    f.withdraw_amount,
    f.controlled_user_count,
    f.controlled_count,
    f.absolute_bankrupt_user_count,
    f.absolute_bankrupt_count,
    f.snapshot_time,
    f.data_status,
    f.metric_version,
    f.data_cutoff_at
FROM lifecycle_fact AS f
LEFT JOIN game_dimension AS g ON g.game_id = f.game_id
LEFT JOIN historical_surface_dimension AS s
    ON s.business_date = f.business_date
   AND s.game_id = f.game_id;

-- 上线前必须确认：
-- 1. 三个占位来源的真实表名、Owner、刷新时间和权限；
-- 2. 历史版本/包体/渠道关联键和覆盖率；
-- 3. population_type 与 TC/流充比/折损系数的认证分子分母；
-- 4. business_date 的数据库时区。
